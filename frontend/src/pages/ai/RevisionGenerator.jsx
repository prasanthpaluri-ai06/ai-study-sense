import React, { useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  BookMarked,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Lightbulb,
  HelpCircle,
  Eye,
  EyeOff,
  PlayCircle,
  FileQuestion,
  Layers
} from "lucide-react";

export default function RevisionGenerator({ setActivePage, setSelectedSessionData }) {
  const [topic, setTopic] = useState("Binary Search");
  const [revision, setRevision] = useState(null);
  const [revealedAnswers, setRevealedAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleGenerateRevision = async (e) => {
    e?.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setRevealedAnswers({});
    try {
      const res = await apiRequest("/ai/revision/generate", {
        method: "POST",
        body: JSON.stringify({ topic_title: topic.trim() }),
      });
      setRevision(res);
      toast.success(`Generated 8-step revision notes for ${res.topic_title}`);
    } catch (err) {
      toast.error(err.message || "Failed generating revision package.");
    } finally {
      setLoading(false);
    }
  };

  const toggleAnswer = (idx) => {
    setRevealedAnswers((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const startTopicStudy = (topicTitle) => {
    if (setSelectedSessionData) {
      setSelectedSessionData({
        topic: topicTitle,
        method: "Active Recall",
      });
    }
    if (setActivePage) {
      setActivePage("session");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
          AI Revision Notes Generator
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
          Generates comprehensive, high-yield 8-step revision summaries with formulas, pitfall warnings, and interactive active recall prompts.
        </p>
      </div>

      {/* Input Card */}
      <Card>
        <form onSubmit={handleGenerateRevision} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: "260px" }}>
              <input
                type="text"
                className="form-input"
                placeholder="Enter Topic (e.g. Binary Search, AVL Tree Rotations, Dijkstra's Algorithm, Bayes Theorem)"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                required
              />
            </div>
            <Button
              variant="primary"
              type="submit"
              icon={Sparkles}
              loading={loading}
            >
              {loading ? "Generating 8-Step Notes..." : "Generate Revision Package"}
            </Button>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", fontSize: "0.82rem", color: "var(--text-muted)" }}>
            <span>Quick Topics:</span>
            {["Binary Search", "AVL Tree Rotations", "Dijkstra's Algorithm", "Process Scheduling", "Recurrence Relations"].map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTopic(t)}
                style={{
                  background: "var(--bg-app)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "12px",
                  padding: "2px 8px",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  color: "var(--color-sage)",
                  fontWeight: 500,
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {/* 8-Step Revision Package Container */}
      {revision && (
        <Card style={{ borderLeft: "5px solid var(--color-sage)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.25rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border-color)" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <h2 style={{ fontSize: "1.35rem", fontWeight: 800, color: "var(--text-main)" }}>
                  {revision.topic_title}
                </h2>
                <Badge variant="good">High Yield Exam Note</Badge>
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Curriculum Category: <strong>{revision.category || "Academic Concept"}</strong>
              </div>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <Button
                size="sm"
                variant="primary"
                icon={PlayCircle}
                onClick={() => startTopicStudy(revision.topic_title)}
              >
                Study Topic
              </Button>
              <Button
                size="sm"
                variant="outline"
                icon={FileQuestion}
                onClick={() => {
                  if (setActivePage) setActivePage("quiz-generator");
                }}
              >
                Take Quiz
              </Button>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {/* 1. Formal Definition */}
            <div style={{ backgroundColor: "var(--bg-app)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--color-wood)", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                1. Formal Academic Definition
              </h3>
              <p style={{ fontSize: "0.93rem", color: "var(--text-main)", lineHeight: 1.5 }}>
                {revision.definition}
              </p>
            </div>

            {/* 2. Core Mechanism */}
            <div>
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                2. Core Conceptual Mechanism
              </h3>
              <p style={{ fontSize: "0.92rem", color: "var(--text-main)", lineHeight: 1.5 }}>
                {revision.core_idea}
              </p>
            </div>

            {/* 3. Essential Invariants & Properties */}
            <div>
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                3. Key Invariants & Properties
              </h3>
              <ul style={{ paddingLeft: "1.25rem", fontSize: "0.9rem", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                {revision.important_points.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            {/* 4. Formulas & Complexity Guarantees */}
            {revision.formula_or_syntax && (
              <div style={{ backgroundColor: "var(--color-sage-soft)", border: "1px solid var(--status-good-border)", padding: "0.85rem 1rem", borderRadius: "6px" }}>
                <h3 style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--color-sage-hover)", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                  4. Formulas, Recurrences & Complexity
                </h3>
                <pre style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-main)", whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>
                  {revision.formula_or_syntax}
                </pre>
              </div>
            )}

            {/* 5. Illustrative Example */}
            <div style={{ backgroundColor: "var(--bg-app)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                5. Illustrative Step-by-Step Example
              </h3>
              <pre style={{ fontSize: "0.88rem", color: "var(--text-main)", whiteSpace: "pre-wrap", fontFamily: "monospace", margin: 0, lineHeight: 1.5 }}>
                {revision.example}
              </pre>
            </div>

            {/* 6. Common Pitfalls & Traps */}
            <div style={{ backgroundColor: "var(--status-bad-bg)", border: "1px solid var(--status-bad-border)", padding: "0.85rem 1rem", borderRadius: "6px" }}>
              <h3 style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--status-bad-text)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                6. Common Pitfalls & Mistakes to Avoid
              </h3>
              <ul style={{ paddingLeft: "1.25rem", fontSize: "0.88rem", color: "var(--status-bad-text)", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                {revision.common_mistakes.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>

            {/* 7. Active Recall Self-Check Questions */}
            {revision.quick_questions && revision.quick_questions.length > 0 && (
              <div>
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--color-wood)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                  7. Active Recall Quick Check
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  {revision.quick_questions.map((q, qIdx) => {
                    const isRevealed = revealedAnswers[qIdx];
                    return (
                      <div
                        key={qIdx}
                        style={{
                          border: "1px solid var(--border-color)",
                          borderRadius: "6px",
                          padding: "0.75rem 1rem",
                          backgroundColor: "var(--bg-surface)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.75rem" }}>
                          <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-main)" }}>
                            Q{qIdx + 1}: {q.question}
                          </span>
                          <button
                            type="button"
                            onClick={() => toggleAnswer(qIdx)}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "0.3rem",
                              background: "none",
                              border: "none",
                              color: "var(--color-sage)",
                              fontSize: "0.8rem",
                              fontWeight: 600,
                              cursor: "pointer",
                            }}
                          >
                            {isRevealed ? <EyeOff size={14} /> : <Eye size={14} />}
                            {isRevealed ? "Hide Answer" : "Reveal Answer"}
                          </button>
                        </div>

                        {isRevealed && (
                          <div style={{ marginTop: "0.5rem", paddingTop: "0.5rem", borderTop: "1px dashed var(--border-color)", fontSize: "0.85rem", color: "var(--color-sage-hover)" }}>
                            <strong>Answer:</strong> {q.answer}
                            {q.explanation && (
                              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                                <em>{q.explanation}</em>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 8. 30-Second Final Recap */}
            <div style={{ backgroundColor: "var(--status-good-bg)", border: "1px solid var(--status-good-border)", padding: "0.85rem 1rem", borderRadius: "6px" }}>
              <h3 style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--status-good-text)", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                8. 30-Second Final Recap
              </h3>
              <p style={{ fontSize: "0.92rem", fontWeight: 500, color: "var(--status-good-text)", margin: 0, lineHeight: 1.5 }}>
                {revision.quick_recap}
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
