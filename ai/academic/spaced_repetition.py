from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


class SM2Scheduler:
    """
    SuperMemo-2 (SM-2) Spaced Repetition Scheduling Engine.
    Calculates repetition count, ease factor, interval in days, and next review date
    based on recall quality score (0 to 5).
    """

    MIN_EASE_FACTOR = 1.3
    DEFAULT_EASE_FACTOR = 2.5

    @classmethod
    def calculate_next_review(
        cls,
        quality_rating: int,  # 0 to 5
        repetition_number: int = 0,
        ease_factor: float = DEFAULT_EASE_FACTOR,
        interval_days: int = 0,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculates the next SM-2 interval and update parameters.
        Quality Rating (q):
          5: Perfect response, complete recall
          4: Correct response with hesitation
          3: Correct response with difficulty
          2: Incorrect response, but easy recall upon seeing answer
          1: Incorrect response, familiar with material
          0: Complete blackout
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        q = max(0, min(5, int(quality_rating)))
        ef = max(cls.MIN_EASE_FACTOR, float(ease_factor))
        rep = max(0, int(repetition_number))

        if q >= 3:
            # Successful recall
            if rep == 0:
                next_interval = 1
            elif rep == 1:
                next_interval = 6
            else:
                next_interval = max(1, int(round(interval_days * ef)))
            next_rep = rep + 1
        else:
            # Failed recall: reset repetition cycle
            next_rep = 0
            next_interval = 1

        # Update Ease Factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(cls.MIN_EASE_FACTOR, round(new_ef, 2))

        next_review_date = now + timedelta(days=next_interval)

        quality_descriptions = {
            5: "Perfect recall without hesitation",
            4: "Correct response after brief thought",
            3: "Correct response with significant difficulty",
            2: "Incorrect, but quickly remembered upon reveal",
            1: "Incorrect, barely remembered",
            0: "Complete blackout / forgot concept",
        }

        return {
            "quality_rating": q,
            "quality_description": quality_descriptions.get(q, ""),
            "repetition_number": next_rep,
            "ease_factor": new_ef,
            "interval_days": next_interval,
            "next_review_date": next_review_date,
            "is_successful": q >= 3,
        }
