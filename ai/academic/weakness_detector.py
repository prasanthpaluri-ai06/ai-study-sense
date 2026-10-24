from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WeaknessItem(BaseModel):
    topic: str
    subject_name: Optional[str] = None
    severity: str  # "Critical", "High", "Moderate"
    weakness_score: float  # 0 to 100
    source: str  # "Quiz Performance", "Academic Assessment", "Syllabus Progress", "Spaced Repetition"
    reason: str
    mathematical_breakdown: str
    recommended_action: str
    recommended_method: str


class WeaknessAnalysisReport(BaseModel):
    total_weaknesses: int
    critical_count: int
    high_count: int
    moderate_count: int
    weaknesses: List[WeaknessItem]
    overall_health_diagnosis: str


class WeaknessDetector:
    """
    Identifies academic knowledge gaps and weak topics using a transparent,
    deterministic scoring model across multiple real data sources.
    """

    # Scoring Weights
    WEIGHT_QUIZ = 0.40
    WEIGHT_MARKS = 0.35
    WEIGHT_SYLLABUS = 0.15
    WEIGHT_SPACED_REP = 0.10

    @classmethod
    def analyze_weaknesses(
        cls,
        quiz_attempts: List[Dict[str, Any]],
        subject_marks: List[Dict[str, Any]],
        syllabus_topics: Optional[List[Dict[str, Any]]] = None,
        spaced_rep_items: Optional[List[Dict[str, Any]]] = None,
    ) -> WeaknessAnalysisReport:
        weaknesses: List[WeaknessItem] = []

        # 1. Analyze Quiz Performance (Track scores & repeated errors)
        quiz_by_topic: Dict[str, List[float]] = {}
        for q in quiz_attempts:
            topic = q.get("topic_title", "Unknown Topic").strip()
            pct = float(q.get("percentage", 100.0))
            if topic not in quiz_by_topic:
                quiz_by_topic[topic] = []
            quiz_by_topic[topic].append(pct)

        for topic, scores in quiz_by_topic.items():
            avg_score = sum(scores) / len(scores)
            recent_score = scores[0]  # Assuming first is latest
            if avg_score < 75.0 or recent_score < 70.0:
                # Calculate deterministic deficit
                deficit = max(0.0, 100.0 - recent_score)
                # If multiple failed attempts, increase severity
                repeated_fail_multiplier = 1.0 + (0.15 * (len(scores) - 1)) if len(scores) > 1 and recent_score < 70 else 1.0
                weakness_score = round(min(100.0, deficit * repeated_fail_multiplier), 1)

                if weakness_score >= 70.0:
                    severity = "Critical"
                    rec_method = "Feynman Technique"
                elif weakness_score >= 45.0:
                    severity = "High"
                    rec_method = "Active Recall"
                else:
                    severity = "Moderate"
                    rec_method = "Spaced Repetition"

                weaknesses.append(
                    WeaknessItem(
                        topic=topic,
                        severity=severity,
                        weakness_score=weakness_score,
                        source="Quiz Performance",
                        reason=f"Recent quiz score was {recent_score:.1f}% (average: {avg_score:.1f}% across {len(scores)} attempts).",
                        mathematical_breakdown=f"Score Deficit: (100 - {recent_score:.1f}) = {deficit:.1f} × Repeat Multiplier {repeated_fail_multiplier:.2f} = {weakness_score}",
                        recommended_action=f"Deconstruct core concept using {rec_method} followed by targeted quiz re-test.",
                        recommended_method=rec_method,
                    )
                )

        # 2. Analyze Subject Academic Marks & Assessments
        for m in subject_marks:
            scored = float(m.get("scored_marks", 0))
            total = float(m.get("total_marks", 100))
            assessment_name = m.get("assessment_name", "Assessment")
            subject = m.get("subject_name", "Academic Subject")
            weight = float(m.get("weightage", 1.0) or 1.0)

            pct = (scored / total * 100.0) if total > 0 else 0.0
            if pct < 65.0:
                deficit = 100.0 - pct
                # Higher weight assessment produces higher weakness score
                weight_multiplier = 1.0 + min(0.5, weight / 100.0)
                weakness_score = round(min(100.0, deficit * weight_multiplier), 1)
                severity = "Critical" if weakness_score >= 65.0 else "High" if weakness_score >= 40.0 else "Moderate"

                weaknesses.append(
                    WeaknessItem(
                        topic=f"{subject} ({assessment_name})",
                        subject_name=subject,
                        severity=severity,
                        weakness_score=weakness_score,
                        source="Academic Assessment",
                        reason=f"Assessment '{assessment_name}' scored {pct:.1f}% ({scored}/{total}), which is below the 65% benchmark.",
                        mathematical_breakdown=f"Assessment Deficit: (100 - {pct:.1f}) = {deficit:.1f} with weight factor {weight_multiplier:.2f} = {weakness_score}",
                        recommended_action=f"Review exam solutions and complete 2 focused 52/17 study sessions on {subject}.",
                        recommended_method="52/17",
                    )
                )

        # 3. Analyze Syllabus Topics flagged as 'Needs Revision'
        if syllabus_topics:
            for top in syllabus_topics:
                status = top.get("status", "Not Started")
                title = top.get("title", "Topic")
                is_core = bool(top.get("is_core", False))
                subject = top.get("subject_name", "Course")

                if status == "Needs Revision":
                    weakness_score = 65.0 if is_core else 45.0
                    severity = "High" if is_core else "Moderate"
                    weaknesses.append(
                        WeaknessItem(
                            topic=title,
                            subject_name=subject,
                            severity=severity,
                            weakness_score=weakness_score,
                            source="Syllabus Progress",
                            reason=f"Student manually flagged '{title}' as 'Needs Revision' in syllabus roadmap.",
                            mathematical_breakdown=f"Status: Needs Revision | Core Exam Topic: {is_core} -> Base Score = {weakness_score}",
                            recommended_action=f"Generate 8-step revision notes and conduct active recall self-testing.",
                            recommended_method="Active Recall",
                        )
                    )

        # 4. Analyze Spaced Repetition Flashcard Performance
        if spaced_rep_items:
            for s in spaced_rep_items:
                ease = float(s.get("ease_factor", 2.5))
                reps = int(s.get("repetitions", 0))
                topic = s.get("topic", "Topic")
                if ease < 2.0 or reps == 0:
                    weakness_score = round((2.5 - ease) * 40.0 + (30 if reps == 0 else 0), 1)
                    weaknesses.append(
                        WeaknessItem(
                            topic=topic,
                            severity="Moderate",
                            weakness_score=min(100.0, max(20.0, weakness_score)),
                            source="Spaced Repetition",
                            reason=f"SM-2 Ease Factor is low ({ease:.2f}), indicating repeated recall difficulties.",
                            mathematical_breakdown=f"SM-2 Memory Decay: Ease Factor {ease:.2f} vs Baseline 2.50",
                            recommended_action="Conduct daily spaced repetition review until ease factor stabilizes above 2.3.",
                            recommended_method="Spaced Repetition",
                        )
                    )

        # Sort weaknesses descending by weakness_score
        weaknesses.sort(key=lambda w: w.weakness_score, reverse=True)

        crit_count = sum(1 for w in weaknesses if w.severity == "Critical")
        high_count = sum(1 for w in weaknesses if w.severity == "High")
        mod_count = sum(1 for w in weaknesses if w.severity == "Moderate")

        if crit_count > 0:
            diagnosis = f"Detected {crit_count} Critical and {high_count} High priority knowledge gaps requiring immediate revision."
        elif high_count > 0:
            diagnosis = f"{high_count} High-priority topics identified. Focus on active recall and revision notes."
        elif mod_count > 0:
            diagnosis = f"All major concepts stable. {mod_count} moderate review items to polish before upcoming assessments."
        else:
            diagnosis = "No significant academic weaknesses detected! Academic mastery is on track."

        return WeaknessAnalysisReport(
            total_weaknesses=len(weaknesses),
            critical_count=crit_count,
            high_count=high_count,
            moderate_count=mod_count,
            weaknesses=weaknesses,
            overall_health_diagnosis=diagnosis,
        )
