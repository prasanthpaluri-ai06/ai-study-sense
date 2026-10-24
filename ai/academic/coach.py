from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ai.academic.weakness_detector import WeaknessItem


class CoachRecommendation(BaseModel):
    title: str
    category: str  # "Urgent Deadline", "Weakness Remediation", "Syllabus Milestone", "Habit & Ergonomics", "Active Review"
    priority: str  # "Critical", "High", "Medium"
    content: str
    why_recommended: str
    action_type: str  # "start_session", "take_quiz", "view_revision", "view_assignment", "view_syllabus"
    action_payload: Dict[str, Any] = {}
    recommended_method: str = "Pomodoro"
    estimated_time_minutes: int = 25


class ComprehensiveCoachReport(BaseModel):
    study_health_score: float
    health_score_breakdown: Dict[str, float]
    health_interpretation: str
    top_priorities: List[CoachRecommendation]
    total_recommendations: int
    weaknesses_summary: Dict[str, Any]
    academics_summary: Dict[str, Any]
    study_pace_summary: Dict[str, Any]


class AICoach:
    """
    Central AI Academic Coach synthesizing signals across marks, deadlines,
    syllabus progress, weak topics, quiz results, study sessions, and posture/focus ergonomics.
    """

    @classmethod
    def calculate_study_health_score(
        cls,
        focus_avg: float = 85.0,
        consistency_avg: float = 80.0,
        academics_avg: float = 82.0,
        posture_avg: float = 78.0,
        task_completion_rate: float = 90.0,
        revision_rate: float = 80.0,
    ) -> Dict[str, Any]:
        """Calculates the composite 0-100 Study Health Score."""
        overall = (
            focus_avg * 0.20
            + consistency_avg * 0.20
            + academics_avg * 0.20
            + posture_avg * 0.15
            + task_completion_rate * 0.15
            + revision_rate * 0.10
        )
        overall = round(min(100.0, max(0.0, overall)), 1)

        if overall >= 85.0:
            interpretation = f"Excellent Study Health ({overall}/100). High focus consistency and steady academic momentum."
        elif overall >= 70.0:
            interpretation = f"Good Study Health ({overall}/100). Maintain consistent daily revision and ergonomic posture habits."
        else:
            interpretation = f"Study Health needs attention ({overall}/100). Address upcoming deadlines and weak topic gaps."

        return {
            "overall_score": overall,
            "focus": round(focus_avg, 1),
            "consistency": round(consistency_avg, 1),
            "academics": round(academics_avg, 1),
            "posture": round(posture_avg, 1),
            "tasks": round(task_completion_rate, 1),
            "revision": round(revision_rate, 1),
            "ai_interpretation": interpretation,
        }

    @classmethod
    def generate_coach_plan(
        cls,
        assignments: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]],
        roadmaps: List[Dict[str, Any]],
        quizzes: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
        health_metrics: Optional[Dict[str, float]] = None,
    ) -> ComprehensiveCoachReport:
        recs: List[CoachRecommendation] = []

        # 1. Evaluate Urgent Deadlines
        overdue_or_urgent = [
            a for a in assignments
            if a.get("status") in ["Overdue", "In Progress", "Not Started"]
        ]
        if overdue_or_urgent:
            top_task = overdue_or_urgent[0]
            status = top_task.get("status")
            priority = top_task.get("priority", "High")
            due = top_task.get("due_date", "Soon")
            title = top_task.get("title", "Assignment")
            subject = top_task.get("subject_name", "Academic Course")

            recs.append(
                CoachRecommendation(
                    title=f"Complete '{title}' ({subject})",
                    category="Urgent Deadline",
                    priority="Critical" if status == "Overdue" or priority == "Critical" else "High",
                    content=f"Task is currently {status} with deadline on {due}. Recommended approach is a 52/17 deep work block.",
                    why_recommended=f"Prioritized due to deadline proximity ({due}) and priority level ({priority}).",
                    action_type="view_assignment",
                    action_payload={"assignment_id": top_task.get("id"), "subject_id": top_task.get("subject_id")},
                    recommended_method="52/17",
                    estimated_time_minutes=52,
                )
            )

        # 2. Evaluate Weak Topics
        if weaknesses:
            top_weak = weaknesses[0]
            topic = top_weak.get("topic", "Core Concept")
            score = top_weak.get("weakness_score", 60.0)
            reason = top_weak.get("reason", "Low quiz or assessment score.")
            rec_method = top_weak.get("recommended_method", "Feynman Technique")

            recs.append(
                CoachRecommendation(
                    title=f"Remediate Knowledge Gap: {topic}",
                    category="Weakness Remediation",
                    priority="Critical" if score >= 70.0 else "High",
                    content=f"{reason} Deconstruct the core idea step-by-step using {rec_method}.",
                    why_recommended=f"Weakness score is {score:.1f}/100. Fixing conceptual gaps early prevents marks loss in final exams.",
                    action_type="take_quiz" if "quiz" in reason.lower() else "view_revision",
                    action_payload={"topic_title": topic, "method": rec_method},
                    recommended_method=rec_method,
                    estimated_time_minutes=30,
                )
            )

        # 3. Evaluate Syllabus Progress (Find Next Pending Core Topic)
        pending_core_topic = None
        for rm in roadmaps:
            for mod in rm.get("modules", []):
                for top in mod.get("topics", []):
                    if not top.get("is_completed") and top.get("status") != "Completed":
                        if top.get("is_core", False) and not pending_core_topic:
                            pending_core_topic = {
                                "topic": top.get("title"),
                                "subject": rm.get("subject_name"),
                                "subject_id": rm.get("subject_id"),
                                "method": top.get("recommended_study_method", "Pomodoro"),
                            }
                            break

        if pending_core_topic:
            recs.append(
                CoachRecommendation(
                    title=f"Learn Next Core Topic: {pending_core_topic['topic']}",
                    category="Syllabus Milestone",
                    priority="High",
                    content=f"Advance through {pending_core_topic['subject']} syllabus by mastering core topic '{pending_core_topic['topic']}'.",
                    why_recommended=f"This topic is flagged as a core exam prerequisite in your syllabus checklist.",
                    action_type="start_session",
                    action_payload={
                        "topic": pending_core_topic["topic"],
                        "subject_id": pending_core_topic["subject_id"],
                        "method": pending_core_topic["method"],
                    },
                    recommended_method=pending_core_topic["method"],
                    estimated_time_minutes=25,
                )
            )

        # 4. Ergonomics / Posture / Focus Habit Check
        health_score_data = cls.calculate_study_health_score(
            focus_avg=health_metrics.get("focus", 85.0) if health_metrics else 85.0,
            consistency_avg=health_metrics.get("consistency", 80.0) if health_metrics else 80.0,
            academics_avg=health_metrics.get("academics", 82.0) if health_metrics else 82.0,
            posture_avg=health_metrics.get("posture", 75.0) if health_metrics else 75.0,
            task_completion_rate=health_metrics.get("tasks", 90.0) if health_metrics else 90.0,
            revision_rate=health_metrics.get("revision", 80.0) if health_metrics else 80.0,
        )

        if health_score_data["posture"] < 75.0:
            recs.append(
                CoachRecommendation(
                    title="Optimize Study Ergonomics & Posture",
                    category="Habit & Ergonomics",
                    priority="Medium",
                    content="Laptop camera analytics detected repeated slumping/forward head posture during recent sessions. Adjust screen height to eye level.",
                    why_recommended="Poor ergonomic posture reduces oxygenation and causes cognitive fatigue after 40+ minutes of study.",
                    action_type="start_session",
                    action_payload={"method": "Pomodoro"},
                    recommended_method="Pomodoro",
                    estimated_time_minutes=25,
                )
            )

        # Fallback if student is fully caught up
        if not recs:
            recs.append(
                CoachRecommendation(
                    title="Maintain Daily Study Streak",
                    category="Active Review",
                    priority="Medium",
                    content="All core deadlines and syllabus topics are up to date! Run a 25-minute Pomodoro revision session.",
                    why_recommended="Consistent daily study blocks build effortless academic momentum.",
                    action_type="start_session",
                    action_payload={"method": "Pomodoro"},
                    recommended_method="Pomodoro",
                    estimated_time_minutes=25,
                )
            )

        return ComprehensiveCoachReport(
            study_health_score=health_score_data["overall_score"],
            health_score_breakdown={
                "focus": health_score_data["focus"],
                "consistency": health_score_data["consistency"],
                "academics": health_score_data["academics"],
                "posture": health_score_data["posture"],
                "tasks": health_score_data["tasks"],
                "revision": health_score_data["revision"],
            },
            health_interpretation=health_score_data["ai_interpretation"],
            top_priorities=recs,
            total_recommendations=len(recs),
            weaknesses_summary={
                "total_weaknesses": len(weaknesses),
                "critical": sum(1 for w in weaknesses if w.get("severity") == "Critical"),
            },
            academics_summary={
                "pending_assignments": len(overdue_or_urgent),
            },
            study_pace_summary={
                "completed_sessions": len(sessions),
            },
        )
