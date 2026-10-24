import pytest
from datetime import datetime, date, timedelta, timezone
from httpx import AsyncClient
from ai.academic.analytics_engine import AnalyticsEngine


def test_productivity_score_calculations():
    """Unit test transparent weighted productivity formula."""
    # 1. High focus, good posture, standard duration, zero distractions
    res_high = AnalyticsEngine.calculate_productivity_score(
        duration_minutes=25.0,
        focus_score=95.0,
        posture_score=90.0,
        distraction_count=0,
        posture_alerts_count=0,
        task_completed=True,
    )
    # Base: 0.40*95 (38) + 0.35*90 (31.5) + 0.25*100 (25) = 94.5 + 5 bonus = 99.5
    score_high = res_high["productivity_score"]
    assert 95 <= score_high <= 100
    assert "Base Score:" in res_high["mathematical_breakdown"]

    # 2. Moderate focus, poor posture, several distractions
    res_mod = AnalyticsEngine.calculate_productivity_score(
        duration_minutes=25.0,
        focus_score=60.0,
        posture_score=50.0,
        distraction_count=4,
        posture_alerts_count=2,
        task_completed=False,
    )
    # Base: 0.40*60 (24) + 0.35*50 (17.5) + 0.25*100 (25) = 66.5. Penalties: 4*2.5 + 2*1.5 = 13. Final = 53.5
    score_mod = res_mod["productivity_score"]
    assert 50 <= score_mod <= 65

    # 3. Minimum lower bound clamping test
    res_zero = AnalyticsEngine.calculate_productivity_score(
        duration_minutes=0.0,
        focus_score=0.0,
        posture_score=0.0,
        distraction_count=50,
        task_completed=False,
    )
    assert res_zero["productivity_score"] >= 10.0


def test_study_streak_calculations():
    """Unit test consecutive active day streak counting and activity map."""
    now = datetime.now(timezone.utc)

    # Case A: Active today, yesterday, 2 days ago -> streak = 3
    dates_3 = [
        now,
        now - timedelta(days=1),
        now - timedelta(days=2),
        now - timedelta(days=5),
    ]
    streak_res = AnalyticsEngine.calculate_study_streak(dates_3)
    assert streak_res["current_streak"] == 3
    assert streak_res["longest_streak"] >= 3
    assert len(streak_res["last_30_days"]) == 30

    # Case B: Inactive today, but active yesterday -> streak = 2 (grace day active)
    dates_grace = [
        now - timedelta(days=1),
        now - timedelta(days=2),
    ]
    streak_grace = AnalyticsEngine.calculate_study_streak(dates_grace)
    assert streak_grace["current_streak"] == 2

    # Case C: Empty records
    empty_streak = AnalyticsEngine.calculate_study_streak([])
    assert empty_streak["current_streak"] == 0
    assert empty_streak["longest_streak"] == 0


@pytest.mark.asyncio
async def test_analytics_api_endpoints(client: AsyncClient):
    """Integration test for analytics endpoints, long-term trends, and session reports."""
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "analytics_student",
            "email": "analytics@university.edu",
            "full_name": "Analytics Pro",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Subject & Session
    sub_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers,
        json={"name": "Computer Networks", "code": "CS401", "color": "#768B6E"},
    )
    assert sub_res.status_code == 201
    subject_id = sub_res.json()["id"]

    start_res = await client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "subject_id": subject_id,
            "topic_name": "TCP Congestion Control",
            "study_method": "Pomodoro",
            "method_metadata": {"work_minutes": 25, "break_minutes": 5},
        },
    )
    assert start_res.status_code == 201
    session_id = start_res.json()["id"]

    # Log posture and end session
    await client.post(
        f"/api/v1/sessions/{session_id}/posture-telemetry",
        headers=headers,
        json={"state": "good", "angle_degrees": 10.0, "led_color": "GREEN"},
    )

    end_res = await client.post(
        f"/api/v1/sessions/{session_id}/end",
        headers=headers,
        json={"duration_minutes": 25.0, "notes": "Studied AIMD & Slow Start."},
    )
    assert end_res.status_code == 200

    # 3. Test GET /api/v1/analytics/overview
    overview_res = await client.get("/api/v1/analytics/overview", headers=headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert "total_study_minutes" in overview
    assert "study_health_breakdown" in overview
    assert overview["study_health_breakdown"]["overall_score"] > 0
    assert overview["total_study_minutes"] >= 25.0

    # 4. Test GET /api/v1/analytics/trends
    daily_trends = await client.get("/api/v1/analytics/trends?timeframe=daily", headers=headers)
    assert daily_trends.status_code == 200
    trends_json = daily_trends.json()
    assert "trend_points" in trends_json
    assert "ai_trend_summary" in trends_json
    assert len(trends_json["trend_points"]) >= 1

    weekly_trends = await client.get("/api/v1/analytics/trends?timeframe=weekly", headers=headers)
    assert weekly_trends.status_code == 200

    # 5. Test GET /api/v1/analytics/streak
    streak_api_res = await client.get("/api/v1/analytics/streak", headers=headers)
    assert streak_api_res.status_code == 200
    streak_obj = streak_api_res.json()
    assert streak_obj["current_streak"] >= 1
    assert len(streak_obj["last_30_days"]) == 30

    # 6. Test GET /api/v1/analytics/session/{id}/report
    report_res = await client.get(f"/api/v1/analytics/session/{session_id}/report", headers=headers)
    assert report_res.status_code == 200
    report_json = report_res.json()
    assert report_json["session_id"] == session_id
    assert "productivity_score" in report_json
    assert "ai_summary" in report_json
    assert "mathematical_breakdown" in report_json

    # 7. Test POST /api/v1/analytics/health/calculate
    calc_health = await client.post("/api/v1/analytics/health/calculate", headers=headers)
    assert calc_health.status_code == 200
    health_data = calc_health.json()
    assert "overall_score" in health_data
    assert "focus" in health_data
    assert "consistency" in health_data
    assert "posture" in health_data
    assert "ai_interpretation" in health_data
