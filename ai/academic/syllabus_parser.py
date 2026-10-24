import io
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TopicDef(BaseModel):
    title: str
    subtopics: List[str] = []
    is_core: bool = False
    difficulty_level: str = "Medium"
    recommended_study_method: str = "Active Recall"
    conceptual_dependencies: List[str] = []


class ModuleDef(BaseModel):
    name: str
    module_number: int = 1
    description: str = ""
    topics: List[TopicDef] = []
    conceptual_chain: List[str] = []


class SyllabusDocumentExtractor:
    """Extracts raw text from PDF, DOCX, TXT, images, or document files with validation."""

    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
    SUPPORTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str, content_type: str = "") -> str:
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")
        if len(file_bytes) > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size ({len(file_bytes) / 1024 / 1024:.1f} MB) exceeds the 15 MB limit.")

        ext = filename.lower().split(".")[-1] if "." in filename else ""

        if ext == "pdf" or "pdf" in content_type:
            return cls._extract_pdf(file_bytes)
        elif ext in ["docx", "doc"] or "wordprocessingml" in content_type:
            return cls._extract_docx(file_bytes)
        elif ext in cls.SUPPORTED_IMAGE_EXTENSIONS or content_type.startswith("image/"):
            return cls._extract_image(file_bytes, filename)
        elif ext in ["txt", "md", "text", "rtf"] or "text/plain" in content_type:
            return cls._extract_plain_text(file_bytes)
        else:
            # Fallback to plain text attempt
            text = cls._extract_plain_text(file_bytes)
            if not text.strip():
                raise ValueError(
                    f"Unsupported file format '.{ext}'. Supported formats are PDF, DOCX, TXT, Markdown, PNG, and JPG."
                )
            return text

    @classmethod
    def _extract_image(cls, file_bytes: bytes, filename: str) -> str:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Unable to read image file '{filename}': {str(e)}")

        try:
            import pytesseract
            text = pytesseract.image_to_string(img).strip()
            if not text:
                raise ValueError(
                    "OCR did not detect any readable text in the uploaded image. "
                    "Please ensure the image contains clear, legible syllabus text or upload a PDF/DOCX/TXT file."
                )
            return text
        except Exception as e:
            err_msg = str(e)
            if "tesseract is not installed" in err_msg.lower() or "not found" in err_msg.lower():
                raise ValueError(
                    "Optical Character Recognition (OCR) is not currently available for image files on this system. "
                    "Please upload a standard PDF, DOCX, or text file, or paste your syllabus text directly."
                )
            raise ValueError(f"Failed extracting text from image '{filename}': {err_msg}")

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
            
            text = "\n\n".join(text_parts).strip()
            
            # If standard text extraction yielded nothing, check if it's an image-scanned PDF
            if not text:
                text = cls._extract_pdf_ocr_fallback(reader)

            if not text:
                raise ValueError(
                    "Could not extract readable text from PDF. The document appears empty or contains non-selectable scanned pages. "
                    "Please upload a PDF with selectable text, a DOCX file, or paste the text directly."
                )
            return text
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed parsing PDF document: {str(e)}")

    @classmethod
    def _extract_pdf_ocr_fallback(cls, reader) -> str:
        """Fallback to OCR on embedded page images if pypdf extracts no text."""
        try:
            from PIL import Image
            import pytesseract
            ocr_text = []
            for page in reader.pages:
                for img_obj in page.images:
                    img = Image.open(io.BytesIO(img_obj.data))
                    t = pytesseract.image_to_string(img).strip()
                    if t:
                        ocr_text.append(t)
            return "\n\n".join(ocr_text).strip()
        except Exception:
            return ""

    @classmethod
    def _extract_docx(cls, file_bytes: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            text = "\n".join(paragraphs).strip()
            if not text:
                raise ValueError("DOCX document is empty.")
            return text
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed parsing DOCX document: {str(e)}")

    @classmethod
    def _extract_plain_text(cls, file_bytes: bytes) -> str:
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                return file_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="ignore").strip()


class SyllabusParser:
    """
    Parses extracted syllabus text into structured MODULE -> TOPICS -> SUBTOPICS,
    identifies core/high-yield topics, and establishes conceptual dependencies.
    """

    MODULE_REGEX = re.compile(
        r"^(?:MODULE|UNIT|CHAPTER|PART|WEEK|SECTION|BLOCK)\s*[:\-\u2013\u2014]?\s*([0-9]+|[IVXLCDM]+)?\s*[:\-\u2013\u2014]?\s*(.*)$",
        re.IGNORECASE
    )

    CORE_KEYWORDS = [
        "fundamental", "core", "basic", "architecture", "algorithm",
        "principle", "theorem", "law", "essential", "primary", "foundation",
        "key", "critical", "analysis", "design", "structure", "lifecycle"
    ]

    @classmethod
    def parse_syllabus(cls, raw_text: str) -> List[ModuleDef]:
        if not raw_text or not raw_text.strip():
            return []

        raw_lines = raw_text.splitlines()
        modules: List[ModuleDef] = []
        current_module: Optional[ModuleDef] = None
        current_topic: Optional[TopicDef] = None

        module_counter = 0

        # Check if the document contains explicit module headings anywhere
        has_explicit_modules = any(
            bool(cls.MODULE_REGEX.match(l.strip()))
            for l in raw_lines
            if l.strip() and (len(l.strip()) < 120 or not any(c in l.strip() for c in [",", ";"]))
        )

        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if line indicates a new Module / Unit
            mod_match = cls.MODULE_REGEX.match(stripped)
            if mod_match and (len(stripped) < 120 or not any(c in stripped for c in [",", ";"])):
                mod_num_raw = mod_match.group(1) or ""
                mod_name_part = (mod_match.group(2) or "").strip()

                # If mod_num_raw is empty, check if mod_name_part starts with a number (e.g. "1 Overview of...")
                if not mod_num_raw:
                    lead_match = re.match(r"^([0-9]+|[IVXLCDM]+)\s*[:\-\u2013\u2014]?\s*(.*)$", mod_name_part)
                    if lead_match:
                        mod_num_raw = lead_match.group(1)
                        mod_name_part = lead_match.group(2).strip()

                module_counter += 1
                mod_num_str = mod_num_raw if mod_num_raw else str(module_counter)
                clean_name_part = mod_name_part.strip(" :-\u2013\u2014")
                clean_name = f"Module {mod_num_str}: {clean_name_part}" if clean_name_part else f"Module {mod_num_str}"

                current_module = ModuleDef(
                    name=clean_name,
                    module_number=int(mod_num_str) if mod_num_str.isdigit() else module_counter,
                    description="",
                    topics=[],
                )
                modules.append(current_module)
                current_topic = None
                continue

            # If no module created yet:
            if current_module is None:
                # If explicit module headers exist later in document, skip preamble lines
                if has_explicit_modules:
                    continue
                # If no explicit modules exist in the document, group under Module 1
                module_counter += 1
                current_module = ModuleDef(
                    name="Module 1: Course Curriculum",
                    module_number=module_counter,
                    description="",
                    topics=[],
                )
                modules.append(current_module)

            # Subtopic detection:
            # A line is a subtopic if it explicitly uses sub-item markers (e.g. `a)`, `(i)`, `(a)`, `i.`) 
            # or if stripped begins with `--` or `->` or `>`
            is_explicit_sub_marker = bool(re.match(r"^(?:[a-z]\)|\([a-z]\)|[ivx]+\.|\-\-|\-\>|\>)\s+", stripped, re.IGNORECASE))
            is_deep_subtopic = is_explicit_sub_marker and current_topic is not None

            # Clean bullet markers, numbers, or hyphens at start of line
            clean_text = re.sub(r"^[\-\*\•\d\.\)\(\:\>\s]+", "", stripped).strip()
            if not clean_text or len(clean_text) < 2:
                continue

            # Skip common administrative/preamble headings that are not study topics
            if re.match(
                r"^(?:pre-?requisite|co-?requisite|course objectives?|course outcomes?|student learning outcomes?|syllabus|text ?books?|reference ?books?|evaluation criteria|mode of delivery|instructional objectives?)\b",
                clean_text,
                re.IGNORECASE,
            ):
                continue

            if is_deep_subtopic and current_topic is not None and len(clean_text) < 120:
                if clean_text not in current_topic.subtopics:
                    current_topic.subtopics.append(clean_text)
                continue

            # Check for inline colon subtopics, e.g., "BST: Insertion, Deletion, Searching"
            if ":" in clean_text and not clean_text.lower().startswith("module") and not clean_text.lower().startswith("unit"):
                parts = clean_text.split(":", 1)
                main_title = parts[0].strip()
                subtopic_items = [s.strip() for s in re.split(r"[,;]\s*", parts[1]) if s.strip()]
                is_core = any(kw in main_title.lower() for kw in cls.CORE_KEYWORDS)
                method, diff = cls._classify_method_and_difficulty(main_title)

                current_topic = TopicDef(
                    title=main_title,
                    subtopics=subtopic_items,
                    is_core=is_core,
                    difficulty_level=diff,
                    recommended_study_method=method,
                    conceptual_dependencies=[],
                )
                current_module.topics.append(current_topic)
                continue

            # Regular topic entry
            is_core = any(kw in clean_text.lower() for kw in cls.CORE_KEYWORDS)
            method, diff = cls._classify_method_and_difficulty(clean_text)

            current_topic = TopicDef(
                title=clean_text,
                subtopics=[],
                is_core=is_core,
                difficulty_level=diff,
                recommended_study_method=method,
                conceptual_dependencies=[],
            )
            current_module.topics.append(current_topic)

        # Prune empty modules if other modules have topics
        non_empty = [m for m in modules if len(m.topics) > 0]
        if non_empty:
            modules = non_empty

        # Resolve conceptual dependencies across modules
        for mod in modules:
            cls._resolve_conceptual_dependencies(mod)

        return modules

    @classmethod
    def _classify_method_and_difficulty(cls, title: str) -> tuple[str, str]:
        t = title.lower()
        if any(kw in t for kw in ["tree", "graph", "recursion", "dynamic programming", "proof", "derivation", "quantum", "compiler", "concurrency", "neural", "avl", "heap", "complexity"]):
            return "Feynman Technique", "Hard"
        elif any(kw in t for kw in ["definition", "property", "terminology", "formula", "syntax", "classification", "overview", "types", "notation"]):
            return "Active Recall", "Medium"
        elif any(kw in t for kw in ["implement", "lab", "practice", "exercise", "code", "design", "project", "simulation"]):
            return "52/17", "Medium"
        elif any(kw in t for kw in ["constant", "standard", "protocol", "vocabulary", "dates", "facts"]):
            return "Spaced Repetition", "Easy"
        else:
            return "Pomodoro", "Medium"

    @classmethod
    def _resolve_conceptual_dependencies(cls, mod: ModuleDef):
        """
        Builds the conceptual sequence order for topics in the module.
        Example: Tree basics -> Binary trees -> Traversals -> BST -> AVL
        """
        topic_titles = [t.title for t in mod.topics]
        mod.conceptual_chain = topic_titles

        for i, t in enumerate(mod.topics):
            if i > 0:
                t.conceptual_dependencies = topic_titles[:i]
            else:
                t.conceptual_dependencies = []
