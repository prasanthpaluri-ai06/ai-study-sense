import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_academic_planner_lifecycle_end_to_end(client: AsyncClient):
    # 1. Register student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "planner_student",
            "email": "planner@studysense.ai",
            "full_name": "Planner Student",
            "password": "StrongPassword123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial semester status (unconfigured)
    sem_init = await client.get("/api/v1/planner/semester", headers=headers)
    assert sem_init.status_code == 200
    assert sem_init.json()["is_configured"] is False

    # 3. Create a course subject with syllabus and topics
    subj_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers,
        json={
            "name": "Software Engineering",
            "code": "CS301",
            "semester": "Fall 2026",
            "credits": 4.0,
            "color": "#5A6E52",
        },
    )
    assert subj_res.status_code == 201
    subj_id = subj_res.json()["id"]

    # Upload syllabus text to populate modules and topics
    syl_res = await client.post(
        "/api/v1/syllabus/upload/text",
        headers=headers,
        json={
            "subject_id": subj_id,
            "title": "Software Engineering Curriculum",
            "content_text": """
Module 1: Requirements Engineering
- SRS Documentation
- Use Case Modeling
- Agile User Stories

Module 2: Architectural Design
- Microservices vs Monolith
- Design Patterns: Singleton and Factory
- RESTful API Architecture
""",
        },
    )
    assert syl_res.status_code == 201

    # Create an assignment
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT12:00:00Z")
    assign_res = await client.post(
        "/api/v1/academic/assignments",
        headers=headers,
        json={
            "subject_id": subj_id,
            "title": "Architecture Diagram Submission",
            "due_date": due_date,
            "priority": "High",
            "status": "Not Started",
            "estimated_effort_hours": 3.0,
        },
    )
    assert assign_res.status_code == 201

    # 4. Configure Semester
    start_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end_str = (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d")

    sem_set = await client.post(
        "/api/v1/planner/semester",
        headers=headers,
        json={
            "start_date": start_str,
            "end_date": end_str,
            "study_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "max_daily_tasks": 3,
            "target_study_hours_daily": 3.0,
        },
    )
    assert sem_set.status_code == 200
    assert sem_set.json()["is_configured"] is True

    # 5. Verify Overview Command Center
    overview_res = await client.get("/api/v1/planner/overview", headers=headers)
    assert overview_res.status_code == 200
    overview_data = overview_res.json()
    assert overview_data["is_configured"] is True
    assert overview_data["total_topics_count"] >= 5
    assert len(overview_data["subject_cards"]) == 1
    assert overview_data["subject_cards"][0]["id"] == subj_id

    # 6. Verify Schedule Feed
    sched_res = await client.get(f"/api/v1/planner/schedule?subject_id={subj_id}", headers=headers)
    assert sched_res.status_code == 200
    tasks = sched_res.json()["tasks"]
    assert len(tasks) > 0
    topic_task = next(t for t in tasks if t.get("topic_id") is not None)
    task_id = topic_task["id"]

    # 7. Reschedule a task (manual override)
    new_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d")
    resched_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        headers=headers,
        json={"scheduled_date": new_date},
    )
    assert resched_res.status_code == 200
    assert resched_res.json()["scheduled_date"] == new_date
    assert resched_res.json()["is_manual_override"] is True

    # 8. Toggle Task Completion & check syllabus synchronization
    toggle_res = await client.patch(f"/api/v1/planner/tasks/{task_id}/toggle", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_completed"] is True

    # Check updated overview reflects completed count
    overview_updated = await client.get("/api/v1/planner/overview", headers=headers)
    assert overview_updated.json()["completed_topics_count"] >= 1

    # 9. Add Blackout Date (Holiday / Unavailable)
    holiday_date = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
    blackout_res = await client.post(
        "/api/v1/planner/blackout-dates",
        headers=headers,
        json={
            "date": holiday_date,
            "reason": "Midterm Examination Day",
            "blackout_type": "exam",
        },
    )
    assert blackout_res.status_code == 200
    blackout_id = blackout_res.json()["id"]

    # 10. Rebalance Preview and Apply
    preview_res = await client.post("/api/v1/planner/rebalance/preview", headers=headers)
    assert preview_res.status_code == 200
    assert "shifted_tasks" in preview_res.json()

    apply_res = await client.post("/api/v1/planner/rebalance/apply", headers=headers)
    assert apply_res.status_code == 200

    # 11. Today's Checklist endpoint
    today_res = await client.get("/api/v1/planner/today", headers=headers)
    assert today_res.status_code == 200
    assert isinstance(today_res.json(), list)

    # 12. Delete blackout date
    del_b = await client.delete(f"/api/v1/planner/blackout-dates/{blackout_id}", headers=headers)
    assert del_b.status_code == 200
