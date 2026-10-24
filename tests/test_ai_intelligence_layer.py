import pytest
from httpx import AsyncClient
from ai.academic.resource_finder import ResourceFinder
from ai.academic.revision_generator import RevisionGenerator
from ai.academic.quiz_generator import QuizGenerator
from ai.academic.weakness_detector import WeaknessDetector
from ai.academic.method_recommender import StudyMethodRecommender
from ai.academic.coach import AICoach


def test_resource_finder_unit():
    """Verify that ResourceFinder categorizes resources and generates verified URLs without hallucination."""
    res = ResourceFinder.find_resources("Binary Search")
    assert res.topic == "Binary Search"
    assert res.domain == "Computer Science"
    assert len(res.resources) >= 5

    categories = [r.category for r in res.resources]
    assert "Videos" in categories
    assert "Educational Websites" in categories
    assert "Documentation" in categories
    assert "Practice" in categories

    # Verify URLs are properly formed
    for r in res.resources:
        assert r.url.startswith("http://") or r.url.startswith("https://")
        assert "Binary+Search" in r.url or "Binary_Search" in r.url or "binary" in r.url.lower()


def test_revision_generator_unit():
    """Verify that RevisionGenerator generates 8-step structured notes with formulas and quick questions."""
    rev = RevisionGenerator.generate_revision("AVL Tree Rotations")
    assert rev.topic_title == "AVL Tree Rotations"
    assert len(rev.definition) > 20
    assert len(rev.core_idea) > 20
    assert len(rev.important_points) >= 3
    assert rev.formulas_or_syntax is not None
    assert len(rev.common_mistakes) >= 2
    assert len(rev.quick_questions) >= 2
    assert len(rev.final_recap) > 20


def test_quiz_generator_and_evaluation_unit():
    """Verify QuizGenerator generates diverse question types and grades student submissions deterministically."""
    quiz = QuizGenerator.generate_quiz("Binary Search Trees", difficulty="Hard", num_questions=5)
    assert quiz.topic_title == "Binary Search Trees"
    assert len(quiz.questions) == 5

    q_types = [q.question_type for q in quiz.questions]
    assert "MCQ" in q_types
    assert any(t in q_types for t in ["Conceptual", "ShortAnswer", "Coding"])

    # Test Evaluation
    student_answers = {
        quiz.questions[0].id: quiz.questions[0].correct_answer,  # Correct
        quiz.questions[1].id: "Wrong Answer",                     # Incorrect
    }
    eval_result = QuizGenerator.evaluate_quiz_submission(
        topic_title=quiz.topic_title,
        questions=quiz.questions[:2],
        student_answers=student_answers,
    )
    assert eval_result.total_score == 1.0
    assert eval_result.max_score == 2.0
    assert eval_result.percentage == 50.0
    assert len(eval_result.weak_areas) > 0


def test_weakness_detector_transparent_scoring():
    """Verify WeaknessDetector uses transparent mathematical scoring model."""
    quiz_data = [
        {"topic_title": "Dynamic Programming", "percentage": 40.0},
        {"topic_title": "Dynamic Programming", "percentage": 45.0},
    ]
    marks_data = [
        {"subject_name": "Algorithms", "scored_marks": 25, "total_marks": 50, "assessment_name": "Midterm", "weightage": 30.0}
    ]
    syllabus_topics = [
        {"title": "Red-Black Trees", "status": "Needs Revision", "is_core": True, "subject_name": "Algorithms"}
    ]

    report = WeaknessDetector.analyze_weaknesses(
        quiz_attempts=quiz_data,
        subject_marks=marks_data,
        syllabus_topics=syllabus_topics,
    )

    assert report.total_weaknesses >= 3
    assert report.critical_count >= 1
    # Check that reasons and mathematical breakdowns are clear
    for w in report.weaknesses:
        assert len(w.reason) > 10
        assert len(w.mathematical_breakdown) > 10
        assert w.recommended_method in ["Feynman Technique", "Active Recall", "Spaced Repetition", "52/17", "Pomodoro"]


def test_study_method_recommender_matrix():
    """Verify StudyMethodRecommender recommends among the 5 core methods based on mastery, topic type, and fatigue."""
    # 1. Struggling student -> Feynman Technique with topic-specific protocol
    rec_struggle = StudyMethodRecommender.recommend_method("Recursion Trees", student_score=45.0)
    assert rec_struggle.primary_method == "Feynman Technique"
    assert any("Recursion Trees" in step for step in rec_struggle.execution_protocol)
    assert len(rec_struggle.practical_exercises) >= 3
    assert len(rec_struggle.expected_outcomes) >= 3
    assert len(rec_struggle.self_assessment_questions) >= 3

    # 2. Binary Search Trees -> Topic specific steps with invariants, deletion/insertion
    rec_bst = StudyMethodRecommender.recommend_method("Binary Search Trees", learning_objective="Deep Understanding")
    assert rec_bst.primary_method in ["52/17", "Feynman Technique", "Pomodoro"]
    bst_steps = " ".join(rec_bst.execution_protocol)
    assert "Binary Search Trees" in bst_steps
    assert "invariant" in bst_steps.lower() or "node" in bst_steps.lower() or "search" in bst_steps.lower()

    # 3. Heavy Coding / Flow with Fatigue -> Adapts to Pomodoro
    rec_fatigued = StudyMethodRecommender.recommend_method(
        "Build Microservices Compiler Project",
        learning_objective="Problem Solving / Coding",
        fatigue_level="Fatigued"
    )
    assert rec_fatigued.primary_method == "Pomodoro"
    assert "fatigue" in rec_fatigued.why_recommended.lower() or "burnout" in rec_fatigued.why_recommended.lower()

    # 4. Long Term Memory / Vocabulary -> Spaced Repetition or Active Recall
    rec_memory = StudyMethodRecommender.recommend_method("Compiler Terminology & Grammar Definitions", learning_objective="Long-Term Retention")
    assert rec_memory.primary_method in ["Spaced Repetition", "Active Recall"]


@pytest.mark.asyncio
async def test_full_ai_endpoints_integration(client: AsyncClient):
    """End-to-end integration test for all AI endpoints."""
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "ai_scholar",
            "email": "scholar@university.edu",
            "full_name": "AI Intelligence Scholar",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Resource Finder Endpoint
    rf_res = await client.get("/api/v1/ai/resources?query=Binary+Search", headers=headers)
    assert rf_res.status_code == 200
    assert len(rf_res.json()["resources"]) >= 5

    # 3. Test Revision Generator Endpoint
    rev_res = await client.post(
        "/api/v1/ai/revision/generate",
        headers=headers,
        json={"topic_title": "Binary Search Trees"},
    )
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert "definition" in rev_data
    assert len(rev_data["important_points"]) >= 2

    # 4. Test Quiz Generation & Submission Endpoint with Database Persistence
    quiz_gen_res = await client.post(
        "/api/v1/ai/quiz/generate",
        headers=headers,
        json={"topic_title": "Binary Search", "difficulty": "Medium", "num_questions": 3},
    )
    assert quiz_gen_res.status_code == 200
    quiz_obj = quiz_gen_res.json()
    questions = quiz_obj["questions"]
    assert len(questions) == 3

    # Submit answers
    submit_res = await client.post(
        "/api/v1/ai/quiz/submit",
        headers=headers,
        json={
            "topic_title": "Binary Search",
            "difficulty": "Medium",
            "questions": questions,
            "student_answers": {
                str(questions[0]["id"]): questions[0]["correct_answer"],
                str(questions[1]["id"]): "Wrong random response",
            },
        },
    )
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["attempt_id"] is not None
    assert submit_data["percentage"] >= 0.0

    # 5. Test Quiz History
    hist_res = await client.get("/api/v1/ai/quiz/history", headers=headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
    assert hist_res.json()[0]["topic_title"] == "Binary Search"

    # 6. Test Weakness Detector Endpoint
    weak_res = await client.get("/api/v1/ai/weaknesses", headers=headers)
    assert weak_res.status_code == 200
    assert "weaknesses" in weak_res.json()

    # 7. Test Study Method Recommender Endpoint
    method_res = await client.post(
        "/api/v1/ai/method/recommend",
        headers=headers,
        json={"topic_title": "AVL Rotations", "student_score": 50.0},
    )
    assert method_res.status_code == 200
    res_json = method_res.json()
    assert res_json["primary_method"] == "Feynman Technique"
    assert len(res_json["practical_exercises"]) >= 3
    assert len(res_json["execution_protocol"]) >= 4

    # 7b. Test empty topic validation error
    empty_topic_res = await client.post(
        "/api/v1/ai/method/recommend",
        headers=headers,
        json={"topic_title": "   "},
    )
    assert empty_topic_res.status_code == 400

    # 8. Test Coach Plan & Study Health Endpoints
    coach_res = await client.get("/api/v1/ai/coach/plan", headers=headers)
    assert coach_res.status_code == 200
    assert "top_priorities" in coach_res.json()
    assert len(coach_res.json()["top_priorities"]) >= 1
    # Check that recommendation includes explanation of WHY
    assert "why_recommended" in coach_res.json()["top_priorities"][0]

    health_res = await client.get("/api/v1/ai/study-health", headers=headers)
    assert health_res.status_code == 200
    assert health_res.json()["overall_score"] > 0.0
