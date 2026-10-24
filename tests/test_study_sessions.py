import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from ai.academic.spaced_repetition import SM2Scheduler


def test_sm2_algorithm_calculations():
    """Unit test for SM-2 Spaced Repetition Scheduling Engine."""
    now = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)

    # 1. First review with perfect recall (q=5, rep=0) -> interval should be 1 day
    r1 = SM2Scheduler.calculate_next_review(quality_rating=5, repetition_number=0, ease_factor=2.5, interval_days=0, now=now)
    assert r1["interval_days"] == 1
    assert r1["repetition_number"] == 1
    assert r1["ease_factor"] >= 2.5
    assert r1["is_successful"] is True

    # 2. Second review with good recall (q=4, rep=1) -> interval should be 6 days
    r2 = SM2Scheduler.calculate_next_review(quality_rating=4, repetition_number=1, ease_factor=r1["ease_factor"], interval_days=1, now=now)
    assert r2["interval_days"] == 6
    assert r2["repetition_number"] == 2

    # 3. Third review with good recall (q=4, rep=2) -> interval should be 6 * 2.5 = 15 days
    r3 = SM2Scheduler.calculate_next_review(quality_rating=4, repetition_number=2, ease_factor=2.5, interval_days=6, now=now)
    assert r3["interval_days"] == 15
    assert r3["repetition_number"] == 3

    # 4. Failed recall (q=1) -> resets rep to 0, interval to 1 day, reduces EF
    r_fail = SM2Scheduler.calculate_next_review(quality_rating=1, repetition_number=3, ease_factor=2.5, interval_days=15, now=now)
    assert r_fail["interval_days"] == 1
    assert r_fail["repetition_number"] == 0
    assert r_fail["ease_factor"] < 2.5
    assert r_fail["is_successful"] is False


@pytest.mark.asyncio
async def test_study_session_full_lifecycle(client: AsyncClient):
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "session_student",
            "email": "session@university.edu",
            "full_name": "Session Tester",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Subject
    sub_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers,
        json={"name": "Discrete Mathematics", "code": "MATH201", "color": "#5A6E52"},
    )
    assert sub_res.status_code == 201
    subject_id = sub_res.json()["id"]

    # 3. Test Pomodoro Session Lifecycle (Start -> Pause -> Resume -> End)
    pomo_res = await client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "subject_id": subject_id,
            "topic_name": "Graph Coloring Algorithms",
            "study_method": "Pomodoro",
            "method_metadata": {"work_minutes": 25, "break_minutes": 5, "target_cycles": 4},
        },
    )
    assert pomo_res.status_code == 201
    pomo_session = pomo_res.json()
    assert pomo_session["status"] == "active"
    assert pomo_session["study_method"] == "Pomodoro"
    session_id = pomo_session["id"]

    # Log Posture Telemetry
    posture_res = await client.post(
        f"/api/v1/sessions/{session_id}/posture-telemetry",
        headers=headers,
        json={"state": "good", "angle_degrees": 12.5, "led_color": "GREEN"},
    )
    assert posture_res.status_code == 200

    # Pause Session
    pause_res = await client.post(f"/api/v1/sessions/{session_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # Resume Session
    resume_res = await client.post(f"/api/v1/sessions/{session_id}/resume", headers=headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "active"

    # End Session
    end_res = await client.post(
        f"/api/v1/sessions/{session_id}/end",
        headers=headers,
        json={
            "duration_minutes": 25.0,
            "notes": "Covered 4-color theorem proofs.",
            "method_metadata": {"cycles_completed": 1, "completed_fully": True},
        },
    )
    assert end_res.status_code == 200
    completed = end_res.json()
    assert completed["status"] == "completed"
    assert completed["duration_minutes"] == 25.0
    assert completed["metric"] is not None

    # 4. Test 52/17 Deep Work Session
    deep_res = await client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "subject_id": subject_id,
            "topic_name": "Planar Graphs",
            "study_method": "52/17",
            "method_metadata": {"work_minutes": 52, "break_minutes": 17},
        },
    )
    assert deep_res.status_code == 201
    deep_id = deep_res.json()["id"]

    cancel_res = await client.post(f"/api/v1/sessions/{deep_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # 5. Test Custom Study Session (Configurable focus/break/cycles)
    custom_res = await client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "subject_id": subject_id,
            "topic_name": "Custom Engineering Sprint",
            "study_method": "Custom",
            "method_metadata": {"work_duration_mins": 45, "break_duration_mins": 10, "total_cycles": 3},
        },
    )
    assert custom_res.status_code == 201
    custom_id = custom_res.json()["id"]

    end_custom = await client.post(
        f"/api/v1/sessions/{custom_id}/end",
        headers=headers,
        json={
            "duration_minutes": 45.0,
            "notes": "Custom focus session finished.",
            "method_metadata": {
                "posture_warnings_count": 2,
                "bad_posture_events_count": 1,
                "place_absence_count": 0,
                "phone_use_count": 0,
            },
        },
    )
    assert end_custom.status_code == 200
    assert end_custom.json()["status"] == "completed"

    # 6. Test Active Recall & Feynman Sessions
    feynman_res = await client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "subject_id": subject_id,
            "topic_name": "Eulerian Paths & Bridges",
            "study_method": "Feynman Technique",
            "method_metadata": {
                "step_1_concept": "Explain Eulerian paths in 10-year-old terms",
                "step_2_gaps": "Clarify odd degree vertex conditions",
                "step_3_revision": "Review Seven Bridges of Königsberg",
                "step_4_final_analogy": "A mail carrier walking every street once without backtracking.",
            },
        },
    )
    assert feynman_res.status_code == 201
    feynman_id = feynman_res.json()["id"]

    end_feynman = await client.post(
        f"/api/v1/sessions/{feynman_id}/end",
        headers=headers,
        json={"duration_minutes": 35.0, "notes": "Completed 4-stage Feynman breakdown."},
    )
    assert end_feynman.status_code == 200
    assert end_feynman.json()["status"] == "completed"

    # 6. Test Spaced Repetition Card Lifecycle & Review
    card_res = await client.post(
        "/api/v1/sessions/spaced-repetition/cards",
        headers=headers,
        json={
            "subject_id": subject_id,
            "front_prompt": "What is the condition for an Eulerian Circuit in a connected graph?",
            "back_answer": "Every single vertex must have an even degree.",
        },
    )
    assert card_res.status_code == 201
    card = card_res.json()
    card_id = card["id"]
    assert card["is_due"] is True

    # Review Card with 5 (Perfect Recall)
    review_res = await client.post(
        f"/api/v1/sessions/spaced-repetition/cards/{card_id}/review",
        headers=headers,
        json={"quality_rating": 5},
    )
    assert review_res.status_code == 200
    reviewed_card = review_res.json()
    assert reviewed_card["repetitions_count"] == 1
    assert reviewed_card["interval_days"] == 1
    assert reviewed_card["is_due"] is False

    # 7. Test Recent Sessions History
    history_res = await client.get("/api/v1/sessions/recent", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 3
