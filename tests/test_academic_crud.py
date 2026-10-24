import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_academic_management_crud(client: AsyncClient):
    # 1. Register Student 1
    reg1_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice_acad",
            "email": "acad1@university.edu",
            "full_name": "Alice Academic",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "institution": "Tech Institute",
            "course": "Computer Science",
            "year": "3rd Year",
            "semester": "Semester 5",
        },
    )
    assert reg1_res.status_code == 201
    token1 = reg1_res.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Register Student 2 for User Isolation verification
    reg2_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob_acad",
            "email": "acad2@university.edu",
            "full_name": "Bob Isolation",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "institution": "Tech Institute",
            "course": "Electrical Eng",
            "year": "2nd Year",
            "semester": "Semester 3",
        },
    )
    assert reg2_res.status_code == 201
    token2 = reg2_res.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 2. Student 1 Creates Subjects across Semesters
    sub1_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers1,
        json={
            "name": "Design & Analysis of Algorithms",
            "code": "CS301",
            "semester": "Semester 5",
            "credits": 4.0,
            "color": "#5A6E52",
            "target_score": 90.0,
            "description": "Core computer science algorithms and complexity theory.",
        },
    )
    assert sub1_res.status_code == 201
    sub1 = sub1_res.json()
    sub1_id = sub1["id"]
    assert sub1["semester"] == "Semester 5"
    assert sub1["credits"] == 4.0

    sub2_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers1,
        json={
            "name": "Database Management Systems",
            "code": "CS302",
            "semester": "Semester 5",
            "credits": 3.0,
            "color": "#BA644A",
            "target_score": 85.0,
        },
    )
    assert sub2_res.status_code == 201
    sub2_id = sub2_res.json()["id"]

    # 3. User Isolation Check: Student 2 cannot see Student 1's subjects
    u2_subs = await client.get("/api/v1/academic/subjects", headers=headers2)
    assert u2_subs.status_code == 200
    assert len(u2_subs.json()) == 0

    # 4. List Subjects with Semester Filter for Student 1
    list_res = await client.get("/api/v1/academic/subjects?semester=Semester%205", headers=headers1)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 2

    # 5. Edit Subject
    edit_sub_res = await client.put(
        f"/api/v1/academic/subjects/{sub1_id}",
        headers=headers1,
        json={"target_score": 92.0, "code": "CS301-A"},
    )
    assert edit_sub_res.status_code == 200
    assert edit_sub_res.json()["target_score"] == 92.0
    assert edit_sub_res.json()["code"] == "CS301-A"

    # User 2 cannot edit User 1's subject
    u2_edit_res = await client.put(
        f"/api/v1/academic/subjects/{sub1_id}",
        headers=headers2,
        json={"target_score": 50.0},
    )
    assert u2_edit_res.status_code == 404

    # 6. Record Configurable Assessment Marks (Configurable Weighting System)
    # Mark 1: CAT 1 (20% weightage) -> 45/50 (90%)
    m1_res = await client.post(
        "/api/v1/academic/marks",
        headers=headers1,
        json={
            "subject_id": sub1_id,
            "assessment_name": "Continuous Assessment Test 1",
            "assessment_type": "CAT/internal",
            "scored_marks": 45.0,
            "total_marks": 50.0,
            "weightage_percent": 20.0,
            "notes": "Dynamic programming and greedy algorithms.",
        },
    )
    assert m1_res.status_code == 201
    m1 = m1_res.json()
    assert m1["percentage"] == 90.0
    assert m1["weighted_contribution"] == 18.0
    m1_id = m1["id"]

    # Mark 2: Lab Assessment (15% weightage) -> 28/30 (93.33%)
    m2_res = await client.post(
        "/api/v1/academic/marks",
        headers=headers1,
        json={
            "subject_id": sub1_id,
            "assessment_name": "Graph Theory Lab",
            "assessment_type": "Lab",
            "scored_marks": 28.0,
            "total_marks": 30.0,
            "weightage_percent": 15.0,
        },
    )
    assert m2_res.status_code == 201

    # Mark 3: Midterm (25% weightage) -> 88/100 (88.0%)
    m3_res = await client.post(
        "/api/v1/academic/marks",
        headers=headers1,
        json={
            "subject_id": sub1_id,
            "assessment_name": "Midterm Examination",
            "assessment_type": "Midterm",
            "scored_marks": 88.0,
            "total_marks": 100.0,
            "weightage_percent": 25.0,
        },
    )
    assert m3_res.status_code == 201

    # 7. List Marks and Verify Performance Breakdown
    marks_list = await client.get(f"/api/v1/academic/marks?subject_id={sub1_id}", headers=headers1)
    assert marks_list.status_code == 200
    assert len(marks_list.json()) == 3

    perf_res = await client.get("/api/v1/academic/marks/performance", headers=headers1)
    assert perf_res.status_code == 200
    perf_data = perf_res.json()
    sub1_perf = next((p for p in perf_data if p["subject_id"] == sub1_id), None)
    assert sub1_perf is not None
    assert sub1_perf["marks_count"] == 3
    assert sub1_perf["total_weightage_used"] == 60.0  # 20 + 15 + 25
    assert sub1_perf["weighted_average"] is not None

    # User 2 cannot access Student 1's marks
    u2_marks = await client.get("/api/v1/academic/marks", headers=headers2)
    assert len(u2_marks.json()) == 0

    # 8. Edit Mark
    edit_mark_res = await client.put(
        f"/api/v1/academic/marks/{m1_id}",
        headers=headers1,
        json={"scored_marks": 48.0},
    )
    assert edit_mark_res.status_code == 200
    assert edit_mark_res.json()["percentage"] == 96.0

    # 9. Create Assignments with Priorities, Due Dates, and Estimated Effort
    now = datetime.now(timezone.utc)
    # Urgent assignment due in 12 hours
    asgn1_res = await client.post(
        "/api/v1/academic/assignments",
        headers=headers1,
        json={
            "subject_id": sub1_id,
            "title": "Divide & Conquer Algorithm Analysis Writeup",
            "description": "Solve Recurrence Relations and submit GitHub repo.",
            "due_date": (now + timedelta(hours=12)).isoformat(),
            "priority": "Critical",
            "status": "In Progress",
            "progress_percent": 40,
            "estimated_effort_hours": 3.5,
            "notes": "Include Big-O proof steps.",
        },
    )
    assert asgn1_res.status_code == 201
    asgn1 = asgn1_res.json()
    asgn1_id = asgn1["id"]
    assert asgn1["is_overdue"] is False
    assert asgn1["estimated_effort_hours"] == 3.5

    # Assignment due in 5 days
    asgn2_res = await client.post(
        "/api/v1/academic/assignments",
        headers=headers1,
        json={
            "subject_id": sub2_id,
            "title": "SQL Normalization Schema Design",
            "due_date": (now + timedelta(days=5)).isoformat(),
            "priority": "Medium",
            "status": "Not Started",
            "progress_percent": 0,
            "estimated_effort_hours": 2.0,
        },
    )
    assert asgn2_res.status_code == 201
    asgn2_id = asgn2_res.json()["id"]

    # Overdue assignment
    asgn3_res = await client.post(
        "/api/v1/academic/assignments",
        headers=headers1,
        json={
            "subject_id": sub2_id,
            "title": "ER Diagram Submission",
            "due_date": (now - timedelta(days=2)).isoformat(),
            "priority": "High",
            "status": "In Progress",
            "progress_percent": 20,
            "estimated_effort_hours": 1.5,
        },
    )
    assert asgn3_res.status_code == 201
    assert asgn3_res.json()["is_overdue"] is True
    assert asgn3_res.json()["status"] == "Overdue"

    # 10. Test AI-Assisted Prioritizer Endpoint
    prioritized_res = await client.get("/api/v1/academic/assignments/prioritized", headers=headers1)
    assert prioritized_res.status_code == 200
    prioritized_tasks = prioritized_res.json()
    assert len(prioritized_tasks) >= 3
    # Top task should have a higher priority score due to urgency / overdue status
    top_task = prioritized_tasks[0]
    assert "priority_score" in top_task
    assert "score_breakdown" in top_task
    assert "urgency" in top_task["score_breakdown"]
    assert "recommendation_reason" in top_task
    assert len(top_task["recommendation_reason"]) > 0

    # 11. Test Academic Dashboard Summary Endpoint
    summary_res = await client.get("/api/v1/academic/summary", headers=headers1)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_subjects"] >= 2
    assert summary["total_assignments"] >= 3
    assert summary["overdue_assignments_count"] >= 1
    assert summary["overall_academic_average"] is not None

    # 12. Update Assignment Status to Completed
    update_asgn_res = await client.patch(
        f"/api/v1/academic/assignments/{asgn1_id}",
        headers=headers1,
        json={"status": "Completed", "progress_percent": 100},
    )
    assert update_asgn_res.status_code == 200
    assert update_asgn_res.json()["status"] == "Completed"
    assert update_asgn_res.json()["progress_percent"] == 100

    # 13. View Subject Detail View
    detail_res = await client.get(f"/api/v1/academic/subjects/{sub1_id}", headers=headers1)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["marks"]) >= 3
    assert len(detail["assignments"]) >= 1

    # 14. Delete Subject and Cascade Check
    del_sub2 = await client.delete(f"/api/v1/academic/subjects/{sub2_id}", headers=headers1)
    assert del_sub2.status_code == 200

    # Verify assignments under deleted subject are removed
    get_asgn2 = await client.get("/api/v1/academic/assignments", headers=headers1)
    assert not any(a["id"] == asgn2_id for a in get_asgn2.json())
