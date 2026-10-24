from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class DeadlinePrioritizer:
    """
    Transparent AI-assisted deadline prioritization engine.
    Calculates dynamic urgency and importance scores using a deterministic, 
    fully explainable multi-factor formula:
      - Urgency (U): 35%
      - Priority (P): 25%
      - Academic Importance (I): 20%
      - Estimated Effort (E): 10%
      - Current Workload (W): 10%
    """

    PRIORITY_WEIGHTS = {
        "Critical": 100.0,
        "High": 75.0,
        "Medium": 50.0,
        "Low": 25.0,
    }

    @classmethod
    def calculate_urgency_score(cls, due_date: datetime, now: Optional[datetime] = None) -> tuple[float, float, str]:
        """
        Calculates Urgency score based on hours remaining until due date.
        Returns: (urgency_score, hours_remaining, urgency_description)
        """
        if now is None:
            now = datetime.now(timezone.utc)
        
        # Ensure timezone-aware comparison
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        diff = due_date - now
        hours_remaining = diff.total_seconds() / 3600.0

        if hours_remaining < 0:
            # Overdue
            hours_overdue = abs(hours_remaining)
            urgency_score = 100.0
            urgency_desc = f"Overdue by {int(hours_overdue // 24)}d {int(hours_overdue % 24)}h" if hours_overdue >= 24 else f"Overdue by {int(hours_overdue)}h"
        elif hours_remaining <= 24:
            # Due within 24 hours: 90 - 100
            urgency_score = round(90.0 + (24.0 - hours_remaining) / 24.0 * 10.0, 1)
            urgency_desc = f"Due within {max(1, int(hours_remaining))} hours"
        elif hours_remaining <= 72:
            # Due in 1-3 days: 75 - 89
            urgency_score = round(75.0 + (72.0 - hours_remaining) / 48.0 * 14.0, 1)
            urgency_desc = f"Due in {int(hours_remaining // 24)} days ({int(hours_remaining % 24)}h)"
        elif hours_remaining <= 168:
            # Due in 3-7 days: 50 - 74
            urgency_score = round(50.0 + (168.0 - hours_remaining) / 96.0 * 24.0, 1)
            urgency_desc = f"Due in {int(hours_remaining // 24)} days"
        elif hours_remaining <= 336:
            # Due in 1-2 weeks: 25 - 49
            urgency_score = round(25.0 + (336.0 - hours_remaining) / 168.0 * 24.0, 1)
            urgency_desc = f"Due in {int(hours_remaining // 24)} days"
        else:
            # Due in > 2 weeks: 10 - 24
            urgency_score = max(10.0, round(25.0 - (hours_remaining - 336.0) / 168.0 * 5.0, 1))
            urgency_desc = f"Due in {int(hours_remaining // 24)} days"

        return float(urgency_score), float(hours_remaining), urgency_desc

    @classmethod
    def calculate_academic_importance(
        cls,
        subject_target_score: float = 85.0,
        subject_avg_score: Optional[float] = None,
        subject_credits: float = 3.0,
    ) -> tuple[float, str]:
        """
        Calculates academic need based on student performance gap vs target score and subject credit weight.
        """
        base_score = min(100.0, max(20.0, subject_credits * 18.0))  # 3 credits -> 54 base, 4 credits -> 72 base

        if subject_avg_score is not None:
            gap = subject_target_score - subject_avg_score
            if gap > 0:
                # Student is below target: high academic importance to boost grades
                boost = min(35.0, gap * 2.0)
                score = min(100.0, base_score + boost)
                desc = f"Subject average ({subject_avg_score}%) is below target ({subject_target_score}%). High grade recovery priority."
            else:
                # Student is performing well above target
                discount = min(20.0, abs(gap) * 1.0)
                score = max(30.0, base_score - discount)
                desc = f"Subject mastery is on track ({subject_avg_score}% vs {subject_target_score}% target)."
        else:
            score = base_score
            desc = f"Subject carries {subject_credits} academic credits."

        return float(round(score, 1)), desc

    @classmethod
    def calculate_effort_factor(cls, estimated_effort_hours: float, hours_remaining: float) -> tuple[float, str]:
        """
        Higher effort tasks with nearing deadlines require an early start.
        """
        effort_hours = max(0.5, estimated_effort_hours)
        if hours_remaining <= 0:
            effort_score = 100.0
            desc = f"Requires ~{effort_hours}h of work (overdue, start immediately)."
        else:
            ratio = (effort_hours / max(1.0, hours_remaining)) * 100.0
            effort_score = min(100.0, max(20.0, ratio * 2.5 + effort_hours * 5.0))
            desc = f"Requires ~{effort_hours}h effort against {max(1, int(hours_remaining))}h remaining."

        return float(round(effort_score, 1)), desc

    @classmethod
    def calculate_workload_factor(cls, active_tasks_count: int, total_pending_hours: float) -> tuple[float, str]:
        """
        Calculates concurrency pressure from active unfinished tasks.
        """
        workload_score = min(100.0, max(10.0, active_tasks_count * 12.0 + total_pending_hours * 3.0))
        desc = f"Current active workload: {active_tasks_count} pending tasks (~{round(total_pending_hours, 1)}h total effort)."
        return float(round(workload_score, 1)), desc

    @classmethod
    def prioritize_assignment(
        cls,
        assignment: Any,
        subject: Optional[Any],
        all_active_assignments: List[Any],
        subject_avg_score: Optional[float] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generates the full transparent scoring breakdown and reasoning for a single assignment.
        """
        # 1. Urgency (35%)
        urgency_score, hours_remaining, urgency_desc = cls.calculate_urgency_score(assignment.due_date, now)

        # 2. Priority Weight (25%)
        priority_str = assignment.priority or "Medium"
        priority_weight = cls.PRIORITY_WEIGHTS.get(priority_str, 50.0)

        # 3. Academic Importance (20%)
        target_score = getattr(subject, "target_score", 85.0) if subject else 85.0
        credits = getattr(subject, "credits", 3.0) if subject else 3.0
        academic_score, academic_desc = cls.calculate_academic_importance(target_score, subject_avg_score, credits)

        # 4. Estimated Effort (10%)
        effort_hours = getattr(assignment, "estimated_effort_hours", 2.0) or 2.0
        effort_score, effort_desc = cls.calculate_effort_factor(effort_hours, hours_remaining)

        # 5. Workload Factor (10%)
        active_count = len(all_active_assignments)
        total_pending_hours = sum(getattr(a, "estimated_effort_hours", 2.0) or 2.0 for a in all_active_assignments)
        workload_score, workload_desc = cls.calculate_workload_factor(active_count, total_pending_hours)

        # Weighted Composite Score (0 - 100)
        final_score = (
            0.35 * urgency_score +
            0.25 * priority_weight +
            0.20 * academic_score +
            0.10 * effort_score +
            0.10 * workload_score
        )
        final_score = round(final_score, 1)

        # Generate transparent reasoning text
        reasoning_parts = []
        if hours_remaining < 0:
            reasoning_parts.append(f"CRITICAL: Task is overdue by {int(abs(hours_remaining))} hours.")
        elif hours_remaining <= 48:
            reasoning_parts.append(f"High urgency with only {int(hours_remaining)} hours until submission.")
        
        if priority_weight >= 75:
            reasoning_parts.append(f"Marked as {priority_str} academic priority.")
        
        if subject_avg_score and subject_avg_score < target_score:
            reasoning_parts.append(f"Important for grade recovery in {getattr(subject, 'name', 'this subject')}.")
        
        if effort_hours >= 4:
            reasoning_parts.append(f"High-effort project (~{effort_hours}h required) warrants early start.")

        if not reasoning_parts:
            reasoning_parts.append(f"Standard schedule: due in {int(max(1, hours_remaining // 24))} days.")

        recommendation_reason = " ".join(reasoning_parts)

        # Status check for overdue
        is_overdue = hours_remaining < 0 and assignment.status != "Completed"

        return {
            "assignment_id": assignment.id,
            "title": assignment.title,
            "subject_id": assignment.subject_id,
            "subject_name": getattr(subject, "name", "General"),
            "subject_color": getattr(subject, "color", "#5A6E52"),
            "due_date": assignment.due_date,
            "priority": priority_str,
            "status": "Overdue" if is_overdue else assignment.status,
            "progress_percent": assignment.progress_percent,
            "estimated_effort_hours": effort_hours,
            "is_overdue": is_overdue,
            "hours_remaining": round(hours_remaining, 1),
            "priority_score": final_score,
            "score_breakdown": {
                "urgency": {
                    "score": urgency_score,
                    "weight_percent": 35,
                    "detail": urgency_desc,
                },
                "priority": {
                    "score": priority_weight,
                    "weight_percent": 25,
                    "detail": f"{priority_str} priority tier",
                },
                "academic_importance": {
                    "score": academic_score,
                    "weight_percent": 20,
                    "detail": academic_desc,
                },
                "estimated_effort": {
                    "score": effort_score,
                    "weight_percent": 10,
                    "detail": effort_desc,
                },
                "workload_pressure": {
                    "score": workload_score,
                    "weight_percent": 10,
                    "detail": workload_desc,
                },
            },
            "recommendation_reason": recommendation_reason,
        }
