from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.app.core.timezone_utils import today_local_str


class AcademicPlannerEngine:
    """
    Intelligent dynamic study planning and scheduling engine.
    Applies deterministic, explainable scheduling rules:
      - Respects semester boundary dates and active study days (Mon-Sat, etc.).
      - Respects student blackout/holiday/exam dates.
      - Interleaves subjects to maintain multi-course academic momentum.
      - Preserves topic dependencies and module sequence.
      - Schedules assignment working blocks prior to deadlines.
      - Generates workload warnings when topic density exceeds target daily capacity.
      - Supports non-destructive rebalancing with preview.
    """

    WEEKDAY_NAMES = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]

    @classmethod
    def get_valid_study_days(
        cls,
        start_date_str: str,
        end_date_str: str,
        study_days: List[str],
        blackout_date_set: Set[str],
        from_date_str: Optional[str] = None,
    ) -> List[str]:
        """
        Returns list of YYYY-MM-DD dates between start and end that are:
        1. On or after from_date_str (if provided, e.g., today).
        2. In the user's active study_days list.
        3. Not in blackout_date_set.
        """
        try:
            start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return []

        if start_d > end_d:
            return []

        if from_date_str:
            try:
                from_d = datetime.strptime(from_date_str, "%Y-%m-%d").date()
                if from_d > start_d:
                    start_d = from_d
            except ValueError:
                pass

        valid_days: List[str] = []
        curr = start_d
        allowed_weekdays = set(study_days or cls.WEEKDAY_NAMES[:6])

        while curr <= end_d:
            day_str = curr.strftime("%Y-%m-%d")
            weekday_name = cls.WEEKDAY_NAMES[curr.weekday()]
            if weekday_name in allowed_weekdays and day_str not in blackout_date_set:
                valid_days.append(day_str)
            curr += timedelta(days=1)

        return valid_days

    @classmethod
    def plan_topics_and_assignments(
        cls,
        start_date_str: str,
        end_date_str: str,
        study_days: List[str],
        blackout_dates: List[Dict[str, Any]],
        subjects_data: List[Dict[str, Any]],
        assignments_data: List[Dict[str, Any]],
        existing_tasks: List[Dict[str, Any]],
        max_daily_tasks: int = 3,
        from_today: bool = True,
        preserve_manual: bool = True,
    ) -> Dict[str, Any]:
        """
        Computes the complete study plan schedule.
        Returns:
          {
            "tasks_to_create": [...],
            "tasks_to_update": [...],
            "workload_warnings": [...],
            "ai_insights": [...],
            "daily_distribution": {...},
            "stats": {...}
          }
        """
        today_str = today_local_str()
        from_date = today_str if from_today else start_date_str

        blackout_set = {b["date"] for b in blackout_dates}
        valid_days = cls.get_valid_study_days(
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            study_days=study_days,
            blackout_date_set=blackout_set,
            from_date_str=from_date,
        )

        warnings: List[str] = []
        insights: List[Dict[str, Any]] = []

        if not valid_days:
            warnings.append("No active study days found in the remaining semester window. Please extend semester dates or update study days/holidays.")
            return {
                "tasks_to_create": [],
                "tasks_to_update": [],
                "workload_warnings": warnings,
                "ai_insights": [],
                "daily_distribution": {},
                "stats": {"total_days": 0, "available_study_days": 0, "topics_scheduled": 0},
            }

        # 1. Identify existing tasks (completed or manual overrides)
        completed_task_ids = set()
        manual_tasks_by_date: Dict[str, List[Dict[str, Any]]] = {}
        already_scheduled_topics = set()
        already_scheduled_assignments = set()

        for t in existing_tasks:
            if t.get("is_completed"):
                completed_task_ids.add(t["id"])
                if t.get("topic_id"):
                    already_scheduled_topics.add(t["topic_id"])
                if t.get("assignment_id"):
                    already_scheduled_assignments.add(t["assignment_id"])
            elif preserve_manual and t.get("is_manual_override"):
                d = t.get("scheduled_date")
                manual_tasks_by_date.setdefault(d, []).append(t)
                if t.get("topic_id"):
                    already_scheduled_topics.add(t["topic_id"])
                if t.get("assignment_id"):
                    already_scheduled_assignments.add(t["assignment_id"])

        # 2. Extract unfinished topics across subjects
        # Group by subject to allow round-robin interleaving
        subject_topic_queues: Dict[int, List[Dict[str, Any]]] = {}
        total_unfinished_topics = 0

        for subj in subjects_data:
            s_id = subj["id"]
            subject_topic_queues[s_id] = []
            modules = sorted(subj.get("modules", []), key=lambda m: m.get("order_index", 0))
            for mod in modules:
                topics = sorted(mod.get("topics", []), key=lambda t: t.get("order_index", 0))
                for top in topics:
                    t_id = top["id"]
                    # If completed or manually fixed, skip from fresh auto-allocation
                    if top.get("is_completed") or t_id in already_scheduled_topics:
                        continue
                    subject_topic_queues[s_id].append({
                        "subject_id": s_id,
                        "subject_name": subj.get("name"),
                        "subject_code": subj.get("code"),
                        "subject_color": subj.get("color", "#5A6E52"),
                        "module_name": mod.get("name"),
                        "topic_id": t_id,
                        "title": top.get("title"),
                        "task_type": "learning",
                        "priority": "High" if top.get("is_core") else "Medium",
                        "estimated_minutes": 45,
                        "difficulty": top.get("difficulty_level", "Medium"),
                        "dependencies": top.get("conceptual_dependencies") or [],
                    })
                    total_unfinished_topics += 1

        # 3. Filter pending assignments that need dedicated study tasks
        pending_assignments_to_schedule: List[Dict[str, Any]] = []
        for a in assignments_data:
            a_id = a["id"]
            if a.get("status") in ["Completed"] or a_id in already_scheduled_assignments:
                continue
            due_str = str(a.get("due_date", ""))[:10]
            pending_assignments_to_schedule.append({
                "assignment_id": a_id,
                "subject_id": a.get("subject_id"),
                "subject_name": a.get("subject_name"),
                "subject_color": a.get("subject_color", "#8C6D58"),
                "title": f"Assignment: {a.get('title')}",
                "module_name": "Coursework Deadline",
                "task_type": "assignment",
                "priority": a.get("priority", "High"),
                "due_date_str": due_str,
                "estimated_minutes": int(min(180, max(30, float(a.get("estimated_effort_hours", 2.0)) * 60))),
            })

        # 4. Workload Capacity Calculation
        num_days = len(valid_days)
        total_items_to_schedule = total_unfinished_topics + len(pending_assignments_to_schedule)
        avg_workload = round(total_items_to_schedule / max(1, num_days), 2)

        if avg_workload > max_daily_tasks:
            warnings.append(
                f"Workload Warning: {total_items_to_schedule} pending items across {num_days} study days requires ~{avg_workload} tasks/day, exceeding target capacity ({max_daily_tasks}/day). Consider enabling more study days or extending semester duration."
            )
        elif avg_workload > max_daily_tasks * 0.8:
            insights.append({
                "type": "pacing",
                "title": "Moderate Academic Pace",
                "description": f"Average workload is {avg_workload} topics/day across {num_days} study days. Consistent daily effort will keep you fully on track.",
            })
        else:
            insights.append({
                "type": "pacing",
                "title": "Comfortable Pace",
                "description": f"Average workload is {avg_workload} topics/day across {num_days} study days. You have ample buffer for deep revision and practice.",
            })

        # 5. Day-by-Day Scheduling using Fair Interleaving
        # Day capacity tracks how many items scheduled per day
        daily_task_counts: Dict[str, int] = {
            day: len(manual_tasks_by_date.get(day, [])) for day in valid_days
        }
        scheduled_items: List[Dict[str, Any]] = []

        # A. First, schedule assignments before their deadlines
        for assign in pending_assignments_to_schedule:
            due_d = assign["due_date_str"]
            # Find best day: latest available valid study day ON or BEFORE due_d
            eligible_days = [d for d in valid_days if d <= due_d]
            target_day = None
            if eligible_days:
                # Find day with least load
                target_day = min(eligible_days, key=lambda d: daily_task_counts[d])
            else:
                # Due date is before valid days (overdue or today) -> schedule on earliest valid day
                target_day = valid_days[0]

            daily_task_counts[target_day] += 1
            scheduled_items.append({
                "assignment_id": assign["assignment_id"],
                "subject_id": assign["subject_id"],
                "topic_id": None,
                "title": assign["title"],
                "module_name": assign["module_name"],
                "task_type": "assignment",
                "scheduled_date": target_day,
                "priority": assign["priority"],
                "estimated_minutes": assign["estimated_minutes"],
                "is_completed": False,
                "is_manual_override": False,
                "order_index": daily_task_counts[target_day],
            })

        # B. Interleave topics across subjects in Round-Robin fashion
        # Active subject IDs that still have topics
        active_subject_ids = [s_id for s_id in subject_topic_queues if subject_topic_queues[s_id]]

        day_idx = 0
        while any(subject_topic_queues[s_id] for s_id in active_subject_ids):
            target_day = valid_days[day_idx % len(valid_days)]

            # Check if this day has reached daily limit
            if daily_task_counts[target_day] >= max_daily_tasks and total_items_to_schedule <= len(valid_days) * max_daily_tasks:
                # Advance day
                day_idx += 1
                continue

            # Pick next topic from one subject in round-robin order
            found_topic = False
            for _ in range(len(active_subject_ids)):
                subj_id = active_subject_ids[0]
                active_subject_ids = active_subject_ids[1:] + [subj_id]
                queue = subject_topic_queues[subj_id]
                if queue:
                    topic_data = queue.pop(0)
                    daily_task_counts[target_day] += 1
                    scheduled_items.append({
                        "subject_id": topic_data["subject_id"],
                        "topic_id": topic_data["topic_id"],
                        "assignment_id": None,
                        "title": topic_data["title"],
                        "module_name": topic_data["module_name"],
                        "task_type": "learning",
                        "scheduled_date": target_day,
                        "priority": topic_data["priority"],
                        "estimated_minutes": topic_data["estimated_minutes"],
                        "is_completed": False,
                        "is_manual_override": False,
                        "order_index": daily_task_counts[target_day],
                    })
                    found_topic = True
                    break

            if not found_topic:
                break

            day_idx += 1

        # C. Generate AI Insights on Priority & Milestones
        if pending_assignments_to_schedule:
            urgent_count = sum(1 for a in pending_assignments_to_schedule if a.get("priority") in ["Critical", "High"])
            if urgent_count > 0:
                insights.append({
                    "type": "deadline",
                    "title": f"{urgent_count} Priority Coursework Deadlines",
                    "description": "Preparation sessions have been automatically slotted into your calendar ahead of each assignment submission date.",
                })

        return {
            "tasks_to_create": scheduled_items,
            "workload_warnings": warnings,
            "ai_insights": insights,
            "daily_distribution": daily_task_counts,
            "stats": {
                "total_days_in_window": len(valid_days),
                "total_unfinished_topics": total_unfinished_topics,
                "assignments_slotted": len(pending_assignments_to_schedule),
                "average_daily_workload": avg_workload,
            },
        }

    @classmethod
    def rebalance_plan(
        cls,
        valid_days: List[str],
        uncompleted_past_tasks: List[Dict[str, Any]],
        future_tasks: List[Dict[str, Any]],
        max_daily_tasks: int = 3,
        preserve_manual: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculates shift of missed tasks to available future days without overwriting
        completed tasks or manually overridden dates.
        """
        if not valid_days:
            return {
                "shifted_tasks": [],
                "warnings": ["No available study days remaining to redistribute missed tasks."],
                "summary": "Could not rebalance: no available future days in semester.",
            }

        # Track load on valid future days
        day_loads: Dict[str, int] = {d: 0 for d in valid_days}
        locked_task_ids = set()

        # Count future tasks that are manual overrides or completed
        for t in future_tasks:
            d = t.get("scheduled_date")
            if d in day_loads:
                if t.get("is_completed") or (preserve_manual and t.get("is_manual_override")):
                    day_loads[d] += 1
                    locked_task_ids.add(t["id"])

        shifted_tasks: List[Dict[str, Any]] = []

        # Missed tasks need new dates
        for t in uncompleted_past_tasks:
            if t.get("is_completed"):
                continue

            # Pick valid future day with lowest load
            best_day = min(valid_days, key=lambda d: day_loads[d])
            day_loads[best_day] += 1

            shifted_tasks.append({
                "task_id": t["id"],
                "title": t["title"],
                "subject_name": t.get("subject_name"),
                "old_date": t.get("scheduled_date"),
                "new_date": best_day,
                "reason": "Missed past topic scheduled for catch-up",
            })

        warnings = []
        max_load = max(day_loads.values()) if day_loads else 0
        if max_load > max_daily_tasks:
            warnings.append(
                f"Catch-up Alert: Rebalancing increases peak daily load to {max_load} tasks/day. Focus on high priority topics first."
            )

        summary = (
            f"Successfully redistributed {len(shifted_tasks)} missed topics across {len(valid_days)} remaining study days."
            if shifted_tasks else "All topics are currently up to date on your calendar."
        )

        return {
            "shifted_tasks": shifted_tasks,
            "warnings": warnings,
            "total_days_available": len(valid_days),
            "average_daily_workload": round(sum(day_loads.values()) / max(1, len(valid_days)), 2),
            "summary": summary,
        }
