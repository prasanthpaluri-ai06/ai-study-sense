from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from backend.app.core.timezone_utils import today_local_date, to_local_datetime


class SessionPerformanceReport(BaseModel):
    session_id: int
    topic_name: str
    study_method: str
    duration_minutes: float
    focus_score: float
    posture_score: float
    productivity_score: float
    good_posture_seconds: int
    buffer_posture_seconds: int
    bad_posture_seconds: int
    distraction_count: int
    posture_alerts_count: int
    mathematical_breakdown: str
    ai_summary: str


class TrendDataPoint(BaseModel):
    label: str  # e.g. "Mon", "Oct 05", "Week 1"
    date_str: str
    study_minutes: float
    focus_score: float
    posture_score: float
    productivity_score: float
    quizzes_taken: int
    quiz_avg_percentage: float


class LongTermAnalyticsReport(BaseModel):
    timeframe: str  # daily, weekly, monthly
    total_study_minutes: float
    total_study_hours: float
    total_sessions: int
    average_focus_score: float
    average_posture_score: float
    average_productivity_score: float
    current_streak_days: int
    longest_streak_days: int
    activity_calendar: List[Dict[str, Any]]  # List of { date: "YYYY-MM-DD", minutes: X, active: bool }
    trend_points: List[TrendDataPoint]
    ai_trend_summary: str


class AnalyticsEngine:
    """
    Computes deterministic session productivity scores, study streaks,
    aggregated daily/weekly/monthly trends, and natural-language summaries.
    """

    @classmethod
    def calculate_productivity_score(
        cls,
        duration_minutes: float,
        focus_score: float,
        posture_score: float,
        distraction_count: int = 0,
        posture_alerts_count: int = 0,
        task_completed: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculates a transparent, weighted productivity score (0-100).
        Formula:
          Base = (0.40 * Focus) + (0.35 * Posture) + (0.25 * DurationQuality)
          Penalties = (Distractions * 2.5) + (PostureAlerts * 1.5)
          Productivity = Base - Penalties + TaskBonus
        """
        # Duration quality: optimal between 20 and 60 minutes
        if duration_minutes >= 20.0:
            duration_factor = min(100.0, (duration_minutes / 25.0) * 85.0 + 15.0)
        else:
            duration_factor = (duration_minutes / 20.0) * 80.0

        base_score = (0.40 * focus_score) + (0.35 * posture_score) + (0.25 * duration_factor)
        penalties = (distraction_count * 2.5) + (posture_alerts_count * 1.5)
        task_bonus = 5.0 if task_completed else 0.0

        final_score = round(min(100.0, max(10.0, base_score - penalties + task_bonus)), 1)

        breakdown = (
            f"Base Score: (0.40 × {focus_score:.1f}% Focus) + (0.35 × {posture_score:.1f}% Posture) + "
            f"(0.25 × {duration_factor:.1f}% Duration) = {base_score:.1f}. "
            f"Deductions: -{penalties:.1f} ({distraction_count} distractions, {posture_alerts_count} alerts). "
            f"Task Bonus: +{task_bonus:.1f} -> Final Productivity: {final_score}/100."
        )

        return {
            "productivity_score": final_score,
            "base_score": round(base_score, 1),
            "penalties": round(penalties, 1),
            "mathematical_breakdown": breakdown,
        }

    @classmethod
    def calculate_study_streak(cls, session_dates: List[datetime], tz_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates active study streak, longest streak, and last 30-day activity map.
        Streak represents consecutive active study days in user's local timezone.
        """
        if not session_dates:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "total_study_days": 0,
                "last_30_days": [],
            }

        # Normalize dates to local date strings
        date_set = set()
        for dt in session_dates:
            if dt:
                loc_dt = to_local_datetime(dt, tz_name)
                date_set.add(loc_dt.strftime("%Y-%m-%d"))

        today = today_local_date(tz_name)
        
        # Calculate current streak
        current_streak = 0
        check_date = today
        # If no study today, check if study happened yesterday to keep streak active
        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        if today_str not in date_set and yesterday_str in date_set:
            check_date = today - timedelta(days=1)

        while check_date.strftime("%Y-%m-%d") in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate longest historical streak
        sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in date_set])
        longest_streak = 0
        temp_streak = 0
        prev_date = None

        for d in sorted_dates:
            if prev_date is None:
                temp_streak = 1
            elif (d - prev_date).days == 1:
                temp_streak += 1
            elif (d - prev_date).days > 1:
                temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)
            prev_date = d

        longest_streak = max(longest_streak, current_streak)

        # 30-day activity calendar
        last_30_days = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            last_30_days.append({
                "date": d_str,
                "active": d_str in date_set,
                "day_name": d.strftime("%a"),
                "day_number": d.day,
            })

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_study_days": len(date_set),
            "last_30_days": last_30_days,
        }

    @classmethod
    def aggregate_long_term_trends(
        cls,
        sessions: List[Dict[str, Any]],
        quizzes: List[Dict[str, Any]],
        timeframe: str = "daily",  # daily, weekly, monthly
        tz_name: Optional[str] = None,
    ) -> LongTermAnalyticsReport:
        """
        Aggregates session, posture, focus, and quiz telemetry into chronological trend points.
        """
        today = today_local_date(tz_name)

        # Extract session dates for streak calculation
        session_dts = []
        for s in sessions:
            st = s.get("start_time")
            if isinstance(st, datetime):
                session_dts.append(st)
            elif isinstance(st, str):
                try:
                    session_dts.append(datetime.fromisoformat(st.replace("Z", "+00:00")))
                except Exception:
                    pass

        streak_info = cls.calculate_study_streak(session_dts, tz_name=tz_name)

        def _get_local_day_str(val):
            if isinstance(val, datetime):
                return to_local_datetime(val, tz_name).strftime("%Y-%m-%d")
            elif isinstance(val, str):
                try:
                    dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                    return to_local_datetime(dt, tz_name).strftime("%Y-%m-%d")
                except Exception:
                    return str(val)[:10]
            return ""

        # Bucket sessions into days or weeks
        trend_points: List[TrendDataPoint] = []
        
        if timeframe == "daily":
            # Last 7 days
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                label = day.strftime("%a")  # Mon, Tue, etc.

                # Filter matching sessions
                matching_sess = [
                    s for s in sessions
                    if s.get("start_time") and _get_local_day_str(s["start_time"]) == day_str
                ]

                # Filter matching quizzes
                matching_quiz = [
                    q for q in quizzes
                    if q.get("created_at") and _get_local_day_str(q["created_at"]) == day_str
                ]

                mins = sum(s.get("duration_minutes", 0) for s in matching_sess)
                focus_avg = (
                    sum(s.get("focus_score", 100) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 100.0
                )
                posture_avg = (
                    sum(s.get("posture_score", 100) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 100.0
                )
                prod_avg = (
                    sum(s.get("productivity_score", 85) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 85.0
                )
                quiz_avg = (
                    sum(q.get("percentage", 0) for q in matching_quiz) / len(matching_quiz)
                    if matching_quiz else 0.0
                )

                trend_points.append(
                    TrendDataPoint(
                        label=label,
                        date_str=day_str,
                        study_minutes=round(mins, 1),
                        focus_score=round(focus_avg, 1),
                        posture_score=round(posture_avg, 1),
                        productivity_score=round(prod_avg, 1),
                        quizzes_taken=len(matching_quiz),
                        quiz_avg_percentage=round(quiz_avg, 1),
                    )
                )
        else:
            # 4 Weekly periods
            for w in range(3, -1, -1):
                start_w = today - timedelta(days=(w + 1) * 7)
                end_w = today - timedelta(days=w * 7)
                label = f"Week {4 - w}"

                matching_sess = [
                    s for s in sessions
                    if s.get("start_time") and (
                        start_w <= (s["start_time"].date() if isinstance(s["start_time"], datetime) else datetime.fromisoformat(str(s["start_time"])[:10]).date()) <= end_w
                    )
                ]

                mins = sum(s.get("duration_minutes", 0) for s in matching_sess)
                focus_avg = (
                    sum(s.get("focus_score", 100) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 100.0
                )
                posture_avg = (
                    sum(s.get("posture_score", 100) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 100.0
                )
                prod_avg = (
                    sum(s.get("productivity_score", 85) for s in matching_sess) / len(matching_sess)
                    if matching_sess else 85.0
                )

                trend_points.append(
                    TrendDataPoint(
                        label=label,
                        date_str=f"{start_w.strftime('%b %d')} - {end_w.strftime('%b %d')}",
                        study_minutes=round(mins, 1),
                        focus_score=round(focus_avg, 1),
                        posture_score=round(posture_avg, 1),
                        productivity_score=round(prod_avg, 1),
                        quizzes_taken=0,
                        quiz_avg_percentage=0.0,
                    )
                )

        total_mins = sum(s.get("duration_minutes", 0) for s in sessions)
        avg_focus = (
            sum(s.get("focus_score", 100) for s in sessions) / len(sessions)
            if sessions else 100.0
        )
        avg_posture = (
            sum(s.get("posture_score", 100) for s in sessions) / len(sessions)
            if sessions else 100.0
        )
        avg_prod = (
            sum(s.get("productivity_score", 85) for s in sessions) / len(sessions)
            if sessions else 85.0
        )

        # AI trend summary in plain language
        if total_mins > 120:
            summary = (
                f"You have maintained strong consistency with a {streak_info['current_streak']}-day active study streak "
                f"and {total_mins / 60:.1f} hours logged. Focus quality is holding steady at {avg_focus:.0f}%, "
                f"and posture ergonomics scored {avg_posture:.0f}% with the ESP32 traffic light."
            )
        elif total_mins > 0:
            summary = (
                f"Good initial progress with {len(sessions)} recorded study sessions. "
                f"Maintain consistent 25-minute Pomodoro intervals to build your study streak."
            )
        else:
            summary = "No study sessions recorded yet. Launch your first study block to start tracking long-term trends."

        return LongTermAnalyticsReport(
            timeframe=timeframe,
            total_study_minutes=round(total_mins, 1),
            total_study_hours=round(total_mins / 60.0, 2),
            total_sessions=len(sessions),
            average_focus_score=round(avg_focus, 1),
            average_posture_score=round(avg_posture, 1),
            average_productivity_score=round(avg_prod, 1),
            current_streak_days=streak_info["current_streak"],
            longest_streak_days=streak_info["longest_streak"],
            activity_calendar=streak_info["last_30_days"],
            trend_points=trend_points,
            ai_trend_summary=summary,
        )
