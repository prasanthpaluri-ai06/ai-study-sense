import urllib.parse
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResourceItem(BaseModel):
    category: str  # "Videos", "Educational Websites", "Documentation", "Articles", "Practice"
    title: str
    url: str
    source: str
    description: str
    is_external: bool = True


class ResourceFinderResponse(BaseModel):
    topic: str
    domain: str
    ai_guidance: str
    resources: List[ResourceItem]


class ResourceFinder:
    """
    Curates authoritative, reliable academic resources for syllabus topics without fabricating URLs.
    Uses verified search engines and educational platforms with query parameters.
    """

    DOMAINS = {
        "computer_science": [
            "algorithm", "tree", "graph", "binary", "sort", "search", "stack", "queue",
            "heap", "dynamic programming", "recursion", "array", "linked list", "hash",
            "database", "sql", "normalization", "operating system", "process", "thread",
            "deadlock", "memory", "paging", "network", "tcp", "udp", "ip", "routing",
            "compiler", "automata", "turing", "complexity", "oop", "class", "design pattern"
        ],
        "mathematics": [
            "calculus", "derivative", "integral", "matrix", "eigenvalue", "vector",
            "linear algebra", "probability", "bayes", "distribution", "statistics",
            "differential equation", "fourier", "laplace", "discrete math", "combinatorics"
        ],
        "physics_electronics": [
            "circuit", "transistor", "diode", "semiconductor", "amplifier", "logic gate",
            "electromagnetism", "maxwell", "quantum", "thermodynamics", "optics", "kinematics",
            "signal", "modulation", "filter"
        ]
    }

    @classmethod
    def detect_domain(cls, topic: str) -> str:
        t_low = topic.lower()
        for domain, keywords in cls.DOMAINS.items():
            if any(kw in t_low for kw in keywords):
                return domain
        return "general_academic"

    @classmethod
    def find_resources(cls, topic: str) -> ResourceFinderResponse:
        topic_clean = topic.strip()
        encoded_query = urllib.parse.quote_plus(topic_clean)
        wiki_title = urllib.parse.quote(topic_clean.replace(" ", "_"))
        domain = cls.detect_domain(topic_clean)

        resources: List[ResourceItem] = []

        # 1. Video Resources
        resources.append(
            ResourceItem(
                category="Videos",
                title=f"{topic_clean} - Visual Conceptual Explanation",
                url=f"https://www.youtube.com/results?search_query={encoded_query}+concept+explained",
                source="YouTube Academic",
                description=f"Curated video lectures, animations, and step-by-step visual breakdowns for {topic_clean}.",
            )
        )
        resources.append(
            ResourceItem(
                category="Videos",
                title=f"MIT OpenCourseWare: {topic_clean}",
                url=f"https://ocw.mit.edu/search/?q={encoded_query}",
                source="MIT OpenCourseWare",
                description=f"University-level lecture videos, course notes, and assignments from MIT.",
            )
        )
        resources.append(
            ResourceItem(
                category="Videos",
                title=f"NPTEL & Khan Academy: {topic_clean}",
                url=f"https://www.khanacademy.org/search?page_search_query={encoded_query}",
                source="Khan Academy",
                description="Structured foundational tutorials with interactive practice modules.",
            )
        )

        # 2. Educational Websites & Conceptual Overviews
        if domain == "computer_science":
            resources.append(
                ResourceItem(
                    category="Educational Websites",
                    title=f"GeeksforGeeks: {topic_clean} Tutorial & Implementations",
                    url=f"https://www.geeksforgeeks.org/search?q={encoded_query}",
                    source="GeeksforGeeks",
                    description="Comprehensive explanation with code examples in C++, Java, Python, and complexity analysis.",
                )
            )
            resources.append(
                ResourceItem(
                    category="Educational Websites",
                    title=f"Programiz: Learn {topic_clean}",
                    url=f"https://www.programiz.com/search?query={encoded_query}",
                    source="Programiz",
                    description="Beginner-friendly visual guides and interactive playgrounds.",
                )
            )
        else:
            resources.append(
                ResourceItem(
                    category="Educational Websites",
                    title=f"LibreTexts Academic Library: {topic_clean}",
                    url=f"https://libretexts.org/search/?q={encoded_query}",
                    source="LibreTexts",
                    description="Open-access peer-reviewed college textbook chapters and lecture modules.",
                )
            )
            resources.append(
                ResourceItem(
                    category="Educational Websites",
                    title=f"Brilliant / Wolfram MathWorld: {topic_clean}",
                    url=f"https://mathworld.wolfram.com/search/?query={encoded_query}",
                    source="Wolfram MathWorld",
                    description="Rigorous mathematical and theoretical foundations with exact definitions.",
                )
            )

        # 3. Documentation & Reference
        resources.append(
            ResourceItem(
                category="Documentation",
                title=f"Wikipedia Academic Reference: {topic_clean}",
                url=f"https://en.wikipedia.org/wiki/{wiki_title}",
                source="Wikipedia Reference",
                description="Comprehensive academic overview, formal definitions, historical context, and bibliography.",
            )
        )
        if domain == "computer_science":
            resources.append(
                ResourceItem(
                    category="Documentation",
                    title=f"DevDocs & Standard API Reference: {topic_clean}",
                    url=f"https://devdocs.io/#q={encoded_query}",
                    source="DevDocs",
                    description="Fast, searchable API and standard library documentation.",
                )
            )

        # 4. Practice & Problem Sets
        if domain == "computer_science":
            resources.append(
                ResourceItem(
                    category="Practice",
                    title=f"LeetCode Problem Set: {topic_clean}",
                    url=f"https://leetcode.com/problemset/all/?search={encoded_query}",
                    source="LeetCode",
                    description=f"Solve real interview and academic coding challenges tagged with {topic_clean}.",
                )
            )
            resources.append(
                ResourceItem(
                    category="Practice",
                    title=f"HackerRank Practice Challenges: {topic_clean}",
                    url=f"https://www.hackerrank.com/domains?q={encoded_query}",
                    source="HackerRank",
                    description="Algorithmic problem tracks with automated test runners.",
                )
            )
        else:
            resources.append(
                ResourceItem(
                    category="Practice",
                    title=f"Quizlet Flashcard Sets: {topic_clean}",
                    url=f"https://quizlet.com/search?query={encoded_query}&type=sets",
                    source="Quizlet",
                    description="Student-tested flashcard decks and spaced-repetition prompts.",
                )
            )

        # 5. Articles & In-Depth Guides
        resources.append(
            ResourceItem(
                category="Articles",
                title=f"In-Depth Articles & Technical Deep Dives: {topic_clean}",
                url=f"https://medium.com/search?q={encoded_query}",
                source="Medium / Tech Publications",
                description="Real-world engineering case studies, intuitive explanations, and deep-dive comparisons.",
            )
        )

        guidance = (
            f"To master '{topic_clean}', start by watching a conceptual lecture on YouTube/MIT OCW. "
            f"Next, consult the formal definitions and invariant properties on Wikipedia/GeeksforGeeks. "
            f"Finally, solidify your understanding by completing 3-5 hands-on practice problems."
        )

        return ResourceFinderResponse(
            topic=topic_clean,
            domain=domain.replace("_", " ").title(),
            ai_guidance=guidance,
            resources=resources,
        )
