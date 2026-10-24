import React, { useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  BookOpen,
  Clock,
  Play,
  Sparkles,
  Repeat,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
  Target,
  BrainCircuit,
  Zap,
  SlidersHorizontal,
} from "lucide-react";

export const STUDY_METHODS_DATA = [
  {
    id: "Pomodoro",
    name: "1. Pomodoro Technique",
    category: "High-Focus Sprints",
    timing: "25 min Focus + 5 min Break (Configurable Cycles)",
    bestFor: "Building study momentum, beating procrastination, maintaining consistent focus during intense problem sets.",
    whyUseful:
      "Prevents cognitive fatigue through structured micro-intervals. The strict separation of focus and rest maintains mental stamina over multi-hour study blocks.",
    structure: ["25m Focus Sprint", "5m Short Break", "25m Focus Sprint", "5m Short Break", "15-30m Long Rest (after 4 cycles)"],
    color: "var(--color-sage)",
    icon: Clock,
  },
  {
    id: "52/17",
    name: "2. 52 / 17 Deep Work",
    category: "Deep Engineering Flow",
    timing: "52 min Deep Study + 17 min Restorative Break",
    bestFor: "Complex coding projects, heavy mathematical derivations, algorithmic problem solving, and architecture design.",
    whyUseful:
      "Based on ultradian rhythm research: 25-minute timers can interrupt flow states in complex engineering tasks. 52 minutes allows deep immersion, paired with 17 minutes of complete cognitive rest.",
    structure: ["52m Immersive Deep Flow", "17m Complete Screen Disengagement"],
    color: "var(--color-terracotta)",
    icon: Sparkles,
  },
  {
    id: "Active Recall",
    name: "3. Active Recall",
    category: "Memory & Neural Retrieval",
    timing: "Interactive Prompt & Self-Testing Workflow",
    bestFor: "Memorizing definitions, formulas, algorithms, anatomy/structures, and preparing for exams without passive re-reading.",
    whyUseful:
      "Retrieval practice forces the brain to reconstruct neural pathways, increasing long-term retention up to 50% compared to passive highlighting or note re-reading.",
    structure: ["Inspect Question Prompt", "Attempt Memory Retrieval", "Reveal Target Answer", "Evaluate Accuracy"],
    color: "var(--color-wood)",
    icon: CheckCircle2,
  },
  {
    id: "Spaced Repetition",
    name: "4. Spaced Repetition (SM-2)",
    category: "Long-Term Retention",
    timing: "Adaptive Review Intervals (Day 1, 6, 15, 36...)",
    bestFor: "Retaining entire semester syllabi, high-yield constants, vocabulary, and core conceptual frameworks across weeks and months.",
    whyUseful:
      "Applies the SuperMemo-2 (SM-2) mathematical decay formula to schedule reviews at the exact moment before forgetting, maximizing memory stability with minimum study time.",
    structure: ["Review Prompt", "Rate Recall (0 to 5)", "SM-2 Calculates Ease Factor & Next Review Date"],
    color: "var(--color-sand)",
    icon: Repeat,
  },
  {
    id: "Feynman Technique",
    name: "5. Feynman Technique",
    category: "Deep Conceptual Mastery",
    timing: "4-Stage Guided Simplification Canvas",
    bestFor: "Mastering complex, abstract, or difficult concepts and pinpointing hidden knowledge gaps.",
    whyUseful:
      "Formulated by Nobel laureate Richard Feynman: 'If you cannot explain a concept in simple, jargon-free terms to a child, you do not truly understand it.' Forces foundational comprehension.",
    structure: ["1. Explain Simply", "2. Identify Jargon & Gaps", "3. Research Reference Materials", "4. Craft Simple Analogy"],
    color: "var(--color-sage)",
    icon: HelpCircle,
  },
  {
    id: "Custom",
    name: "6. Custom Study Session",
    category: "Personalized Protocol",
    timing: "Configurable Focus & Break Durations",
    bestFor: "Tailoring focus sprints to your personal attention span, course difficulty, or specific timetable blocks.",
    whyUseful:
      "Gives full control over work sprint length (e.g. 15–90 mins), short break length, and cycle counts for individualized study pacing.",
    structure: ["Custom Work Block", "Custom Break Block", "Custom Repeating Cycles"],
    color: "var(--color-terracotta)",
    icon: SlidersHorizontal,
  },
];

export default function StudyMethods({ setActivePage, onSelectMethod, setSelectedSessionData }) {
  const [topicInput, setTopicInput] = useState("Binary Search Trees");
  const [learningObjective, setLearningObjective] = useState("Deep Understanding");
  const [fatigueLevel, setFatigueLevel] = useState("Normal");
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [recommending, setRecommending] = useState(false);
  const toast = useToast();

  const handleRecommendMethod = async (e) => {
    e?.preventDefault();
    if (!topicInput.trim()) return;
    setRecommending(true);
    try {
      const res = await apiRequest("/ai/method/recommend", {
        method: "POST",
        body: JSON.stringify({
          topic_title: topicInput.trim(),
          learning_objective: learningObjective,
          fatigue_level: fatigueLevel,
        }),
      });
      setAiRecommendation(res);
      toast.success(`Recommended ${res.primary_method} for ${res.topic_title}`);
    } catch (err) {
      toast.error(err.message || "Failed to recommend study method.");
    } finally {
      setRecommending(false);
    }
  };

  const handleLaunchMethod = (methodId, topic = "") => {
    const chosenTopic = topic || topicInput || "Core Concept";
    if (onSelectMethod) {
      onSelectMethod(methodId, {
        topic: chosenTopic,
        method: methodId,
      });
    }
    if (setSelectedSessionData) {
      setSelectedSessionData({
        topic: chosenTopic,
        method: methodId,
      });
    }
    if (setActivePage) {
      setActivePage("study-session");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
          The Five Core Study Methods
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
          Explore the five science-backed study frameworks and use AI to match the optimal method for any topic and mastery level.
        </p>
      </div>

      {/* AI Method Recommender Card */}
      <Card
        title="AI Study Method Recommender"
        subtitle="Get a personalized recommendation among the 5 methods based on topic complexity, fatigue, and learning goals."
        icon={BrainCircuit}
      >
        <form onSubmit={handleRecommendMethod} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ flex: 2, minWidth: "220px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Topic / Subject *
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. AVL Rotations, Recursion, Operating System Paging"
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                required
              />
            </div>

            <div style={{ flex: 1, minWidth: "160px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Learning Objective
              </label>
              <select
                className="form-select"
                value={learningObjective}
                onChange={(e) => setLearningObjective(e.target.value)}
              >
                <option value="Deep Understanding">Deep Conceptual Understanding</option>
                <option value="First Time Learning">First Time Learning</option>
                <option value="Exam Prep / Rapid Revision">Exam Prep / Rapid Revision</option>
                <option value="Long-Term Retention">Long-Term Retention</option>
                <option value="Problem Solving / Coding">Problem Solving / Deep Flow</option>
              </select>
            </div>

            <div style={{ flex: 1, minWidth: "130px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Fatigue Level
              </label>
              <select
                className="form-select"
                value={fatigueLevel}
                onChange={(e) => setFatigueLevel(e.target.value)}
              >
                <option value="Normal">Normal Energy</option>
                <option value="High">High Energy</option>
                <option value="Fatigued">Tired / Low Energy</option>
              </select>
            </div>
          </div>

          <Button
            variant="primary"
            type="submit"
            icon={Sparkles}
            loading={recommending}
            style={{ alignSelf: "flex-start" }}
          >
            {recommending ? "Analyzing Learning Profile..." : "Recommend Optimal Study Method"}
          </Button>
        </form>

        {/* AI Recommendation Result */}
        {aiRecommendation && (
          <div style={{ marginTop: "1.25rem", padding: "1.25rem", backgroundColor: "var(--color-sage-soft)", borderRadius: "6px", border: "1px solid var(--status-good-border)", display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-sage-hover)" }}>
                    Recommended: {aiRecommendation.primary_method}
                  </h3>
                  <Badge variant="good">
                    {aiRecommendation.confidence_score}% Match
                  </Badge>
                  <Badge variant="neutral">
                    {aiRecommendation.topic_title}
                  </Badge>
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  Objective: <strong>{aiRecommendation.learning_objective || learningObjective}</strong> &bull; Energy: <strong>{aiRecommendation.fatigue_level || fatigueLevel}</strong>
                  {aiRecommendation.secondary_method && (
                    <> &bull; Follow-Up: <strong>{aiRecommendation.secondary_method}</strong></>
                  )}
                  {" "}&bull; Estimated Duration: <strong>{aiRecommendation.estimated_duration_minutes} mins</strong>
                </div>
              </div>

              <Button
                variant="primary"
                icon={Play}
                onClick={() => handleLaunchMethod(aiRecommendation.primary_method, aiRecommendation.topic_title)}
              >
                Launch {aiRecommendation.primary_method} Session
              </Button>
            </div>

            {/* Why Recommended & Scientific Rationale */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
              <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--color-terracotta)", textTransform: "uppercase", marginBottom: "4px" }}>
                  Why This Fits Your Goal:
                </div>
                <p style={{ fontSize: "0.86rem", color: "var(--text-main)", lineHeight: 1.45, margin: 0 }}>
                  {aiRecommendation.why_recommended}
                </p>
              </div>

              <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--color-wood)", textTransform: "uppercase", marginBottom: "4px" }}>
                  Cognitive Science Rationale:
                </div>
                <p style={{ fontSize: "0.86rem", color: "var(--text-main)", lineHeight: 1.45, margin: 0 }}>
                  {aiRecommendation.scientific_rationale}
                </p>
              </div>
            </div>

            {/* Step-by-Step Execution Protocol */}
            <div style={{ backgroundColor: "var(--bg-app)", padding: "0.9rem 1.1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-main)", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.5rem" }}>
                <Target size={16} color="var(--color-sage-hover)" />
                Topic-Specific Step-by-Step Execution Protocol:
              </div>
              <ol style={{ paddingLeft: "1.25rem", margin: 0, fontSize: "0.88rem", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                {aiRecommendation.execution_protocol.map((step, sIdx) => (
                  <li key={sIdx} style={{ lineHeight: 1.45 }}>{step}</li>
                ))}
              </ol>
            </div>

            {/* Practical Exercises & Expected Outcomes */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
              {aiRecommendation.practical_exercises?.length > 0 && (
                <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem 1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--color-terracotta)", textTransform: "uppercase", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <Zap size={14} /> Practical Exercises:
                  </div>
                  <ul style={{ paddingLeft: "1.1rem", margin: 0, fontSize: "0.84rem", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    {aiRecommendation.practical_exercises.map((ex, exIdx) => (
                      <li key={exIdx} style={{ lineHeight: 1.4 }}>{ex}</li>
                    ))}
                  </ul>
                </div>
              )}

              {aiRecommendation.expected_outcomes?.length > 0 && (
                <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem 1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--color-sage-hover)", textTransform: "uppercase", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <CheckCircle2 size={14} /> Expected Learning Outcomes:
                  </div>
                  <ul style={{ paddingLeft: "1.1rem", margin: 0, fontSize: "0.84rem", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    {aiRecommendation.expected_outcomes.map((out, outIdx) => (
                      <li key={outIdx} style={{ lineHeight: 1.4 }}>{out}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Self-Assessment Diagnostic Questions */}
            {aiRecommendation.self_assessment_questions?.length > 0 && (
              <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem 1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--color-wood)", textTransform: "uppercase", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <HelpCircle size={14} /> Self-Assessment Questions Before Session Wrap-Up:
                </div>
                <ul style={{ paddingLeft: "1.1rem", margin: 0, fontSize: "0.84rem", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                  {aiRecommendation.self_assessment_questions.map((q, qIdx) => (
                    <li key={qIdx} style={{ lineHeight: 1.4 }}>{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 5 Core Methods Catalog */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {STUDY_METHODS_DATA.map((method) => {
          const Icon = method.icon;
          return (
            <Card
              key={method.id}
              style={{
                borderLeft: `5px solid ${method.color}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "0.75rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-main)" }}>
                      {method.name}
                    </h3>
                    <Badge variant="neutral">{method.category}</Badge>
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "3px" }}>
                    <strong>Best for:</strong> {method.bestFor}
                  </div>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  icon={Play}
                  onClick={() => handleLaunchMethod(method.id)}
                >
                  Start {method.id} Session
                </Button>
              </div>

              <div style={{ backgroundColor: "var(--bg-app)", padding: "0.85rem 1rem", borderRadius: "6px", marginBottom: "0.9rem", border: "1px solid var(--border-color)" }}>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "3px" }}>
                  Why & When This Method is Useful:
                </div>
                <p style={{ fontSize: "0.88rem", color: "var(--text-main)", lineHeight: 1.5 }}>
                  {method.whyUseful}
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  fontSize: "0.85rem",
                  color: "var(--text-muted)",
                }}
              >
                <div>
                  <strong>Structure:</strong> {method.structure.join(" ➔ ")}
                </div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)" }}>
                  {method.timing}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
