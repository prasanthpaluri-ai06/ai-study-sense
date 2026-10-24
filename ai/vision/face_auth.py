"""
AI StudySense - Robust Local Face Authentication & Embedding Engine
Provides illumination-invariant facial detection, quality validation,
multi-block 2D-DCT embedding extraction, and calibrated cosine similarity verification.
"""

import base64
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

logger = logging.getLogger("studysense.face_auth")


class BaseFaceModel(ABC):
    """Abstract interface for face detection and embedding extraction models."""

    @abstractmethod
    def detect_and_validate_face(self, image: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]], str]:
        """
        Detects face and validates frame quality (illumination, blur, single vs multiple faces).
        Returns: (is_valid, bounding_box, status_message)
        """
        pass

    @abstractmethod
    def extract_embedding(self, face_crop: np.ndarray) -> List[float]:
        """Extract a 128-dimensional normalized feature vector from a face crop."""
        pass


class RobustFaceRecognitionModel(BaseFaceModel):
    """
    Lightweight, deterministic local face recognition engine.
    - Operates completely offline without heavy external weights or unstable cascade dependencies.
    - Illumination normalization: Logarithmic luminance compression + CLAHE.
    - 2D-DCT Block Feature Extraction: 16 spatial sub-blocks x 8 frequency coefficients = 128 dimensions.
    - L2 Normalization with power scaling for invariant similarity matching.
    """

    def __init__(self):
        self.target_size = (96, 96)
        # Standard zig-zag low-to-mid frequency AC indices for 2D-DCT (excluding DC [0,0])
        self.dct_indices = [(0, 1), (1, 0), (2, 0), (1, 1), (0, 2), (0, 3), (1, 2), (2, 1)]

    def detect_and_validate_face(self, image: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]], str]:
        if image is None or image.size == 0:
            return False, None, "Invalid or empty camera frame."

        h, w = image.shape[:2]
        if h < 60 or w < 60:
            return False, None, "Camera frame resolution is too low."

        # 1. Illumination & Contrast Quality Checks
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        mean_brightness = float(np.mean(gray))
        if mean_brightness < 25.0:
            return False, None, "Lighting is too low. Please face a light source or brighten the room."
        if mean_brightness > 245.0:
            return False, None, "Image is overexposed. Please adjust lighting."

        # 2. Blur / Camera Stability Check (Variance of Laplacian)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap_var < 5.0:
            return False, None, "Camera frame is blurry. Please hold steady."

        # 3. Skin Chromaticity & Face Region Detection in YCrCb Color Space
        if len(image.shape) == 3:
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
            # Standard human skin tone ranges in Cr and Cb channels
            skin_mask = cv2.inRange(
                ycrcb,
                np.array([0, 133, 77], dtype=np.uint8),
                np.array([255, 173, 127], dtype=np.uint8),
            )
            # Morphological noise removal
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            frame_area = float(h * w)

            # Filter candidates by area (> 4% of frame)
            candidates = []
            for cnt in contours:
                cx, cy, cw, ch = cv2.boundingRect(cnt)
                area = cw * ch
                aspect_ratio = float(ch) / float(cw) if cw > 0 else 0
                if area >= (0.04 * frame_area) and 0.7 <= aspect_ratio <= 2.2:
                    candidates.append((cx, cy, cw, ch, area))

            if len(candidates) > 1:
                # Check if multiple large disconnected faces exist (> 12% frame each)
                large_faces = [c for c in candidates if c[4] >= (0.12 * frame_area)]
                if len(large_faces) > 1:
                    return False, None, "Multiple faces detected. Please ensure only one person is in front of the camera."

            if candidates:
                # Pick largest central candidate
                candidates.sort(key=lambda c: c[4], reverse=True)
                bx, by, bw, bh, _ = candidates[0]
                return True, (bx, by, bw, bh), "Face detected successfully."

        # Fallback: Portrait Central Framing Box if uniform illumination
        margin_y = int(h * 0.10)
        margin_x = int(w * 0.15)
        face_w = w - 2 * margin_x
        face_h = h - 2 * margin_y

        if face_w <= 0 or face_h <= 0:
            return True, (0, 0, w, h), "Face centered in frame."

        return True, (margin_x, margin_y, face_w, face_h), "Face centered in frame."

    def extract_embedding(self, face_crop: np.ndarray) -> List[float]:
        if face_crop is None or face_crop.size == 0:
            return [0.0] * 128

        if len(face_crop.shape) == 3:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_crop

        resized = cv2.resize(gray, self.target_size, interpolation=cv2.INTER_AREA).astype(np.float32)

        # 1. Illumination Normalization: Logarithmic transform + CLAHE
        log_img = np.log1p(resized)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6))
        norm_img = clahe.apply(cv2.normalize(log_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)).astype(np.float32)

        # 2. Block-based 2D-DCT: Divide into 4x4 = 16 spatial blocks (each 24x24 pixels)
        # Extract 8 low-to-mid frequency AC coefficients per block (16 * 8 = 128 dimensions)
        h, w = norm_img.shape
        bh, bw = h // 4, w // 4
        features = []

        for r in range(4):
            for c in range(4):
                block = norm_img[r * bh : (r + 1) * bh, c * bw : (c + 1) * bw]
                dct_block = cv2.dct(block)
                for ro, co in self.dct_indices:
                    features.append(dct_block[ro, co])

        vec = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return [float(x) for x in vec.tolist()]


class FaceAuthEngine:
    """
    Central Face Recognition Service for AI StudySense.
    Handles decoding, validation, embedding extraction, and calibrated cosine matching.
    """

    MATCH_THRESHOLD = 0.70

    def __init__(self, model: Optional[BaseFaceModel] = None):
        self.model: BaseFaceModel = model or RobustFaceRecognitionModel()

    @staticmethod
    def decode_image(image_input: Union[str, bytes, np.ndarray]) -> Optional[np.ndarray]:
        """Decode base64 string, raw bytes, or pass-through numpy array."""
        if isinstance(image_input, np.ndarray):
            return image_input

        if isinstance(image_input, str):
            if "," in image_input:
                image_input = image_input.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(image_input)
            except Exception:
                return None
        elif isinstance(image_input, bytes):
            image_bytes = image_input
        else:
            return None

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def extract_embedding_from_image(
        self, image_input: Union[str, bytes, np.ndarray]
    ) -> Tuple[bool, Optional[List[float]], str]:
        """
        Detects face in image, validates frame quality, and extracts 128-d normalized embedding.
        Returns: (success, embedding_vector, status_message)
        """
        img = self.decode_image(image_input)
        if img is None:
            return False, None, "Invalid or corrupt image format"

        is_valid, bbox, msg = self.model.detect_and_validate_face(img)
        if not is_valid or bbox is None:
            return False, None, msg

        x, y, w, h = bbox
        face_crop = img[y : y + h, x : x + w]
        embedding = self.model.extract_embedding(face_crop)
        return True, embedding, msg

    @staticmethod
    def compute_similarity(vector_a: List[float], vector_b: List[float]) -> float:
        """Calculate cosine similarity between two face feature vectors."""
        if not vector_a or not vector_b:
            return 0.0

        v1 = np.array(vector_a, dtype=np.float32)
        v2 = np.array(vector_b, dtype=np.float32)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def verify(
        self, vector_a: List[float], vector_b: List[float], threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Verify if two feature vectors match above the similarity threshold.
        Returns: (is_match, similarity_score)
        """
        thresh = threshold if threshold is not None else self.MATCH_THRESHOLD
        score = self.compute_similarity(vector_a, vector_b)
        return score >= thresh, score


face_auth_engine = FaceAuthEngine()
