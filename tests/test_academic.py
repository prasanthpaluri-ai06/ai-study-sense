import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_academic_and_syllabus_flow(client: AsyncClient):
    # 1. Register student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "academic_user",
            "email": "acad@test.edu",
            "full_name": "Academic Tester",
            "password": "Password123!",
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a Subject
    sub_res = await client.post(
        "/api/v1/academic/subjects",
        json={"name": "Data Structures", "code": "CS201", "color": "#10B981"},
        headers=headers,
    )
    assert sub_res.status_code == 201
    subject_id = sub_res.json()["id"]

    # 3. Add Marks
    mark_res = await client.post(
        "/api/v1/academic/marks",
        json={
            "subject_id": subject_id,
            "assessment_name": "CAT 1",
            "scored_marks": 42.0,
            "total_marks": 50.0,
        },
        headers=headers,
    )
    assert mark_res.status_code == 201
    assert mark_res.json()["percentage"] == 84.0

    # 4. Upload Syllabus and generate checklist roadmap
    syllabus_text = """
    MODULE 1: Algorithm Analysis
    - Time Complexity
    - Space Complexity
    - Recurrence Relations

    MODULE 2: Trees
    - Binary Trees
    - AVL Trees
    """
    syl_res = await client.post(
        "/api/v1/syllabus/upload",
        json={
            "subject_id": subject_id,
            "title": "Data Structures Syllabus",
            "content_text": syllabus_text,
        },
        headers=headers,
    )
    assert syl_res.status_code == 201

    # 5. Fetch roadmaps
    roadmaps_res = await client.get("/api/v1/syllabus/roadmaps", headers=headers)
    assert roadmaps_res.status_code == 200
    roadmaps = roadmaps_res.json()
    assert len(roadmaps) == 1
    assert len(roadmaps[0]["modules"]) == 2
