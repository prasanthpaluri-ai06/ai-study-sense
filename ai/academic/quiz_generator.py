from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuizQuestionItem(BaseModel):
    id: int
    question_text: str
    question_type: str  # "MCQ", "ShortAnswer", "Conceptual", "Coding"
    options: List[str] = []  # For MCQ
    correct_answer: str
    explanation: str
    difficulty: str = "Medium"
    hints: Optional[str] = None
    sample_code_or_io: Optional[str] = None


class QuizGeneratedResponse(BaseModel):
    topic_title: str
    difficulty: str
    total_questions: int
    questions: List[QuizQuestionItem]


class QuizEvaluationItem(BaseModel):
    question_id: int
    student_answer: str
    is_correct: bool
    score: float
    feedback: str


class QuizSubmissionResult(BaseModel):
    attempt_id: Optional[int] = None
    topic_title: str
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    weak_areas: List[str]
    strong_areas: List[str]
    recommendation: str
    evaluations: List[QuizEvaluationItem]


class QuizGenerator:
    """
    Intelligent academic quiz generator producing MCQs, short answer, conceptual,
    and coding questions tailored to topic and difficulty level.
    """

    @classmethod
    def generate_quiz(
        cls,
        topic_title: str,
        difficulty: str = "Medium",
        num_questions: int = 5,
    ) -> QuizGeneratedResponse:
        clean_topic = topic_title.strip()
        t_low = clean_topic.lower()
        diff = difficulty.capitalize() if difficulty else "Medium"

        questions: List[QuizQuestionItem] = []

        if "binary search" in t_low and "tree" not in t_low:
            questions = [
                QuizQuestionItem(
                    id=1,
                    question_text="What is the fundamental prerequisite condition for applying Binary Search to an array?",
                    question_type="MCQ",
                    options=[
                        "The array elements must be monotonically sorted in advance",
                        "The array elements must all be distinct prime numbers",
                        "The array size must be an exact power of 2",
                        "The array must be stored in contiguous GPU texture memory",
                    ],
                    correct_answer="The array elements must be monotonically sorted in advance",
                    explanation="Binary search relies on ordering to discard half of the search space at each iteration.",
                    difficulty="Easy",
                ),
                QuizQuestionItem(
                    id=2,
                    question_text="Why is `mid = low + (high - low) // 2` used instead of `(low + high) // 2`?",
                    question_type="Conceptual",
                    options=[
                        "To prevent 32-bit signed integer overflow when low + high exceeds INT_MAX",
                        "To force floating point division instead of truncation",
                        "Because the CPU arithmetic logic unit executes addition faster than subtraction",
                        "To ensure the middle index is always an odd number",
                    ],
                    correct_answer="To prevent 32-bit signed integer overflow when low + high exceeds INT_MAX",
                    explanation="In typed languages (C/C++/Java), adding two large positive indices can exceed 2^31 - 1 and wrap into negative numbers.",
                    difficulty="Medium",
                ),
                QuizQuestionItem(
                    id=3,
                    question_text="What is the worst-case time complexity of Binary Search on a sorted array of size N?",
                    question_type="MCQ",
                    options=["O(1)", "O(log N)", "O(N)", "O(N log N)"],
                    correct_answer="O(log N)",
                    explanation="Each comparison halves the remaining search interval, yielding log2(N) steps.",
                    difficulty="Easy",
                ),
                QuizQuestionItem(
                    id=4,
                    question_text="Explain what happens if the loop condition is written as `while (low < high)` instead of `while (low <= high)` in a standard exact-match binary search.",
                    question_type="ShortAnswer",
                    options=[],
                    correct_answer="The algorithm terminates before checking the final single remaining element (when low == high), potentially returning -1 even if the target exists.",
                    explanation="When low == high, exactly one candidate element remains; `while (low < high)` skips evaluating this index.",
                    difficulty="Hard",
                ),
                QuizQuestionItem(
                    id=5,
                    question_text="Write the core loop for binary search that returns the first occurrence index of a target with duplicates.",
                    question_type="Coding",
                    options=[],
                    correct_answer="When nums[mid] == target, record result = mid and continue searching left with high = mid - 1.",
                    explanation="Continuing the search in the left subarray ensures finding the lowest index of the duplicate target.",
                    difficulty="Hard",
                    sample_code_or_io="Input: nums = [1, 2, 2, 2, 3], target = 2\nOutput: 1 (first occurrence index)",
                ),
            ]
        elif "tree" in t_low or "bst" in t_low or "avl" in t_low:
            questions = [
                QuizQuestionItem(
                    id=1,
                    question_text="Which tree traversal visits the nodes of a Binary Search Tree in non-decreasing sorted order?",
                    question_type="MCQ",
                    options=["Inorder Traversal (Left, Root, Right)", "Preorder Traversal (Root, Left, Right)", "Postorder Traversal (Left, Right, Root)", "Level-order Traversal (BFS)"],
                    correct_answer="Inorder Traversal (Left, Root, Right)",
                    explanation="Because BST keys satisfy Left < Root < Right, inorder traversal outputs keys in sorted sequence.",
                    difficulty="Easy",
                ),
                QuizQuestionItem(
                    id=2,
                    question_text="What is the allowed range of Balance Factors for any node in a strictly valid AVL Tree?",
                    question_type="MCQ",
                    options=["{-1, 0, +1}", "{0, 1, 2}", "{-2, 0, +2}", "Any integer between -10 and +10"],
                    correct_answer="{-1, 0, +1}",
                    explanation="Balance Factor is defined as Height(Left) - Height(Right) and must stay within {-1, 0, +1}.",
                    difficulty="Medium",
                ),
                QuizQuestionItem(
                    id=3,
                    question_text="What is the worst-case time complexity for searching in an un-balanced Binary Search Tree?",
                    question_type="MCQ",
                    options=["O(N) (degenerates to a linked list)", "O(log N)", "O(1)", "O(N^2)"],
                    correct_answer="O(N) (degenerates to a linked list)",
                    explanation="Skewed insertions (e.g. sorted input into naive BST) produce a linear degenerate chain of depth N.",
                    difficulty="Medium",
                ),
                QuizQuestionItem(
                    id=4,
                    question_text="What double rotation is required when an insertion occurs in the right subtree of the left child (LR case)?",
                    question_type="Conceptual",
                    options=[
                        "Left rotation on left child, followed by Right rotation on unbalanced node",
                        "Right rotation on right child, followed by Left rotation on parent",
                        "Two consecutive Right rotations on the root node",
                        "No rotation; color flipping is sufficient",
                    ],
                    correct_answer="Left rotation on left child, followed by Right rotation on unbalanced node",
                    explanation="A zigzag LR condition requires first straightening the child with a Left rotation, then restoring balance with a Right rotation.",
                    difficulty="Hard",
                ),
                QuizQuestionItem(
                    id=5,
                    question_text="Given a BST, describe how to delete a node that has TWO children.",
                    question_type="ShortAnswer",
                    options=[],
                    correct_answer="Find the in-order successor (minimum in right subtree) or in-order predecessor, replace the node's value with it, and recursively delete the successor node.",
                    explanation="The inorder successor has at most one child, simplifying the recursive deletion.",
                    difficulty="Hard",
                ),
            ]
        else:
            # Universal Dynamic Academic Quiz
            questions = [
                QuizQuestionItem(
                    id=1,
                    question_text=f"What is the foundational principle underlying {clean_topic}?",
                    question_type="MCQ",
                    options=[
                        f"Establishing invariant structural guarantees and reducing computational complexity for {clean_topic}",
                        "Executing random brute-force passes across memory addresses",
                        "Hardcoding static lookup arrays without dynamic parameterization",
                        "Bypassing all mathematical bounds and validation constraints",
                    ],
                    correct_answer=f"Establishing invariant structural guarantees and reducing computational complexity for {clean_topic}",
                    explanation=f"{clean_topic} establishes rigorous invariant principles for consistency and efficiency.",
                    difficulty="Easy",
                ),
                QuizQuestionItem(
                    id=2,
                    question_text=f"Under what conditions does {clean_topic} achieve optimal efficiency?",
                    question_type="MCQ",
                    options=[
                        "When all input preconditions, invariants, and resource boundaries are strictly satisfied",
                        "Only when executed on multi-node distributed clusters",
                        "When all numerical values are negative floating point integers",
                        "When data structures are left completely unsorted",
                    ],
                    correct_answer="When all input preconditions, invariants, and resource boundaries are strictly satisfied",
                    explanation="Precondition verification is mandatory for correctness and peak performance.",
                    difficulty="Medium",
                ),
                QuizQuestionItem(
                    id=3,
                    question_text=f"What is the most frequent misconception or bug encountered when working with {clean_topic}?",
                    question_type="MCQ",
                    options=[
                        "Failing to handle boundary/termination conditions and off-by-one errors",
                        "Incorrect audio driver configuration",
                        "Excessive CSS margin spacing",
                        "Overclocking the system graphics card",
                    ],
                    correct_answer="Failing to handle boundary/termination conditions and off-by-one errors",
                    explanation="Boundary limits and invariant maintenance are the most common source of errors in academic exams.",
                    difficulty="Medium",
                ),
                QuizQuestionItem(
                    id=4,
                    question_text=f"Explain how you would verify the correctness of a solution using {clean_topic}.",
                    question_type="Conceptual",
                    options=[],
                    correct_answer=f"Formulate induction base cases, demonstrate inductive invariant maintenance across each state transition, and verify boundary limits.",
                    explanation="Inductive invariant proof guarantees correctness over all valid inputs.",
                    difficulty="Hard",
                ),
                QuizQuestionItem(
                    id=5,
                    question_text=f"State a practical real-world scenario where {clean_topic} is applied in engineering systems.",
                    question_type="ShortAnswer",
                    options=[],
                    correct_answer=f"Optimizing lookup and transformation pipelines, resource management, and database query indexing.",
                    explanation=f"Applied in production systems to maintain deterministic bounds and reliable execution.",
                    difficulty="Hard",
                ),
            ]

        # Filter by difficulty if desired, or return requested count
        selected = questions[:num_questions]

        return QuizGeneratedResponse(
            topic_title=clean_topic,
            difficulty=diff,
            total_questions=len(selected),
            questions=selected,
        )

    @classmethod
    def evaluate_quiz_submission(
        cls,
        topic_title: str,
        questions: List[QuizQuestionItem],
        student_answers: Dict[int, str],
    ) -> QuizSubmissionResult:
        evaluations: List[QuizEvaluationItem] = []
        total_score = 0.0
        max_score = float(len(questions))
        weak_areas: List[str] = []
        strong_areas: List[str] = []

        for q in questions:
            user_ans = student_answers.get(q.id, "").strip()
            is_correct = False
            score = 0.0
            feedback = ""

            if q.question_type == "MCQ":
                if user_ans and user_ans.lower() == q.correct_answer.strip().lower():
                    is_correct = True
                    score = 1.0
                    feedback = "Correct! " + q.explanation
                else:
                    feedback = f"Incorrect. Correct answer: '{q.correct_answer}'. {q.explanation}"
            else:
                # Semantic / keyword heuristic evaluation for ShortAnswer/Conceptual/Coding
                if not user_ans:
                    feedback = f"No answer provided. Expected: {q.correct_answer}"
                else:
                    # Check for overlap of key concept terms
                    keywords = [w.lower() for w in re_words(q.correct_answer) if len(w) > 4]
                    user_words = [w.lower() for w in re_words(user_ans) if len(w) > 4]
                    matches = set(keywords).intersection(set(user_words))
                    if len(matches) >= 2 or (len(keywords) < 2 and len(matches) >= 1):
                        is_correct = True
                        score = 1.0
                        feedback = "Well articulated answer. Captures core mechanism!"
                    elif len(matches) == 1:
                        score = 0.5
                        feedback = f"Partially correct. Note: {q.correct_answer}"
                    else:
                        score = 0.0
                        feedback = f"Missed key conceptual points. Reference: {q.correct_answer}"

            total_score += score
            if is_correct:
                strong_areas.append(f"{q.question_type} ({q.difficulty}): Question {q.id}")
            else:
                weak_areas.append(f"{q.question_type} on {topic_title} (Q{q.id})")

            evaluations.append(
                QuizEvaluationItem(
                    question_id=q.id,
                    student_answer=user_ans,
                    is_correct=is_correct,
                    score=score,
                    feedback=feedback,
                )
            )

        pct = round((total_score / max_score * 100.0) if max_score > 0 else 0.0, 1)
        passed = pct >= 70.0

        if pct >= 85.0:
            rec = f"Mastery demonstrated ({pct}%). Schedule next review with Spaced Repetition in 6 days."
        elif pct >= 60.0:
            rec = f"Moderate understanding ({pct}%). Conduct an Active Recall session on missed questions."
        else:
            rec = f"Knowledge gaps detected ({pct}%). Revise using Feynman Technique to rebuild foundational concepts."

        return QuizSubmissionResult(
            topic_title=topic_title,
            total_score=total_score,
            max_score=max_score,
            percentage=pct,
            passed=passed,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            recommendation=rec,
            evaluations=evaluations,
        )


def re_words(text: str) -> List[str]:
    import re
    return re.findall(r"\b[A-Za-z0-9_]+\b", text)
