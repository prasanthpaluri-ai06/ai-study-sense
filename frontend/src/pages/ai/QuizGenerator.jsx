import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  FileQuestion,
  Sparkles,
  CheckCircle2,
  XCircle,
  RotateCcw,
  History,
  Award,
  AlertTriangle,
  PlayCircle,
  HelpCircle,
  Code2,
  FileText
} from "lucide-react";

export default function QuizGenerator({ setActivePage, setSelectedSessionData }) {
  const [topic, setTopic] = useState("Binary Search");
  const [difficulty, setDifficulty] = useState("Medium");
  const [numQuestions, setNumQuestions] = useState(5);
  const [quizData, setQuizData] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submissionResult, setSubmissionResult] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [activeTab, setActiveTab] = useState("take"); // 'take' or 'history'
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const toast = useToast();

  useEffect(() => {
    loadQuizHistory();
  }, []);

  const loadQuizHistory = async () => {
    try {
      const hist = await apiRequest("/ai/quiz/history");
      setHistoryList(hist || []);
    } catch (err) {
      console.error("Error loading quiz history:", err);
    }
  };

  const handleGenerateQuiz = async (e) => {
    e?.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setSubmissionResult(null);
    setSelectedAnswers({});
    try {
      const res = await apiRequest("/ai/quiz/generate", {
        method: "POST",
        body: JSON.stringify({
          topic_title: topic.trim(),
          difficulty: difficulty,
          num_questions: parseInt(numQuestions),
        }),
      });
      setQuizData(res);
      toast.success(`Generated ${res.questions.length}-question ${difficulty} quiz!`);
    } catch (err) {
      toast.error(err.message || "Failed generating quiz.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizData) return;
    setSubmitting(true);
    try {
      const payload = {
        topic_title: quizData.topic_title,
        difficulty: quizData.difficulty,
        questions: quizData.questions,
        student_answers: selectedAnswers,
      };
      const res = await apiRequest("/ai/quiz/submit", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setSubmissionResult(res);
      toast.success(`Quiz evaluated! Score: ${res.percentage}%`);
      loadQuizHistory();
    } catch (err) {
      toast.error(err.message || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  const startRemediationSession = (topicTitle, method) => {
    if (setSelectedSessionData) {
      setSelectedSessionData({
        topic: topicTitle,
        method: method || "Feynman Technique",
      });
    }
    if (setActivePage) {
      setActivePage("session");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            AI Topic Quiz & Evaluation
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Generates MCQs, conceptual prompts, and coding challenges with instant grading and knowledge gap analysis.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => setActiveTab("take")}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "take" ? "var(--color-sage)" : "var(--border-color)",
              backgroundColor: activeTab === "take" ? "var(--bg-surface)" : "transparent",
              fontWeight: activeTab === "take" ? 700 : 500,
              color: activeTab === "take" ? "var(--color-sage)" : "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.88rem",
            }}
          >
            <Sparkles size={16} /> Take Quiz
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("history");
              loadQuizHistory();
            }}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "history" ? "var(--color-sage)" : "var(--border-color)",
              backgroundColor: activeTab === "history" ? "var(--bg-surface)" : "transparent",
              fontWeight: activeTab === "history" ? 700 : 500,
              color: activeTab === "history" ? "var(--color-sage)" : "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.88rem",
            }}
          >
            <History size={16} /> Quiz History ({historyList.length})
          </button>
        </div>
      </div>

      {activeTab === "history" ? (
        <Card title="Past Quiz Attempts & Knowledge Gap History" icon={History}>
          {historyList.length === 0 ? (
            <EmptyState
              icon={FileQuestion}
              title="No Past Quiz Attempts"
              description="Generate and take your first topic quiz to track your accuracy and mastery trends."
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {historyList.map((hist) => {
                const passed = hist.percentage >= 70;
                return (
                  <div
                    key={hist.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.85rem 1rem",
                      backgroundColor: "var(--bg-app)",
                      borderRadius: "6px",
                      border: "1px solid var(--border-color)",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-main)" }}>
                          {hist.topic_title}
                        </span>
                        <Badge variant={passed ? "good" : "bad"}>
                          {hist.percentage}% ({hist.score}/{hist.total_score})
                        </Badge>
                      </div>
                      <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "2px" }}>
                        Taken on: {hist.created_at} &bull; {hist.recommendation}
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setTopic(hist.topic_title);
                        setActiveTab("take");
                        handleGenerateQuiz();
                      }}
                    >
                      Retake Quiz
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Generator Form */}
          <Card>
            <form onSubmit={handleGenerateQuiz} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <div style={{ flex: 3, minWidth: "240px" }}>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                    Syllabus Topic *
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Binary Search, AVL Rotations, Dijkstra's Algorithm, Recurrence Relations"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    required
                  />
                </div>

                <div style={{ flex: 1, minWidth: "130px" }}>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                    Difficulty
                  </label>
                  <select
                    className="form-select"
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                  >
                    <option value="Easy">Easy (Foundational)</option>
                    <option value="Medium">Medium (Standard)</option>
                    <option value="Hard">Hard (Deep Reasoning)</option>
                  </select>
                </div>

                <div style={{ flex: 1, minWidth: "120px" }}>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                    Questions
                  </label>
                  <select
                    className="form-select"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                  >
                    <option value="3">3 Questions</option>
                    <option value="5">5 Questions</option>
                    <option value="8">8 Questions</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  <span>Quick Topics:</span>
                  {["Binary Search", "AVL Trees", "Dijkstra", "Process Scheduling"].map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => setTopic(tag)}
                      style={{
                        background: "var(--bg-app)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "10px",
                        padding: "2px 7px",
                        fontSize: "0.78rem",
                        cursor: "pointer",
                        color: "var(--color-sage)",
                      }}
                    >
                      {tag}
                    </button>
                  ))}
                </div>

                <Button
                  variant="primary"
                  type="submit"
                  icon={Sparkles}
                  loading={loading}
                >
                  {loading ? "Generating Quiz..." : "Generate AI Quiz"}
                </Button>
              </div>
            </form>
          </Card>

          {/* Submission Result Score Banner */}
          {submissionResult && (
            <Card style={{ backgroundColor: submissionResult.passed ? "var(--status-good-bg)" : "var(--status-warning-bg)", border: `1px solid ${submissionResult.passed ? "var(--status-good-border)" : "var(--status-warning-border)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <Award size={24} color={submissionResult.passed ? "var(--color-sage)" : "var(--color-terracotta)"} />
                    <h2 style={{ fontSize: "1.3rem", fontWeight: 800, color: "var(--text-main)" }}>
                      Evaluation Score: {submissionResult.percentage}% ({submissionResult.total_score}/{submissionResult.max_score})
                    </h2>
                    <Badge variant={submissionResult.passed ? "good" : "danger"}>
                      {submissionResult.passed ? "Mastery Demonstrated" : "Needs Remediation"}
                    </Badge>
                  </div>
                  <p style={{ fontSize: "0.92rem", color: "var(--text-main)", marginTop: "6px", lineHeight: 1.5 }}>
                    <strong>AI Recommendation:</strong> {submissionResult.recommendation}
                  </p>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  icon={PlayCircle}
                  onClick={() => startRemediationSession(quizData.topic_title, "Feynman Technique")}
                >
                  Start Remediation Session
                </Button>
              </div>
            </Card>
          )}

          {/* Active Quiz Questions */}
          {quizData && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
                  Quiz: {quizData.topic_title} ({quizData.difficulty} Level)
                </h3>
                <Badge variant="neutral">{quizData.questions.length} Questions</Badge>
              </div>

              {quizData.questions.map((q, idx) => {
                const evalItem = submissionResult?.evaluations?.find((e) => e.question_id === q.id);

                return (
                  <Card key={q.id} style={{ borderLeft: evalItem ? (evalItem.is_correct ? "4px solid var(--color-sage)" : "4px solid var(--color-terracotta)") : "1px solid var(--border-color)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                      <h4 style={{ fontSize: "0.98rem", fontWeight: 700, color: "var(--text-main)", flex: 1 }}>
                        {idx + 1}. {q.question_text}
                      </h4>
                      <Badge variant="neutral">{q.question_type}</Badge>
                    </div>

                    {/* Question Type: MCQ */}
                    {q.question_type === "MCQ" || q.options?.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                        {q.options.map((opt, oIdx) => {
                          const isSelected = selectedAnswers[q.id] === opt;
                          const isCorrect = q.correct_answer === opt;

                          let optBg = "var(--bg-app)";
                          let optBorder = "var(--border-color)";
                          let optText = "var(--text-main)";

                          if (submissionResult) {
                            if (isCorrect) {
                              optBg = "var(--status-good-bg)";
                              optBorder = "var(--status-good-border)";
                              optText = "var(--status-good-text)";
                            } else if (isSelected && !isCorrect) {
                              optBg = "var(--status-bad-bg)";
                              optBorder = "var(--status-bad-border)";
                              optText = "var(--status-bad-text)";
                            }
                          } else if (isSelected) {
                            optBg = "var(--color-sage-soft)";
                            optBorder = "var(--color-sage)";
                          }

                          return (
                            <label
                              key={oIdx}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.75rem",
                                padding: "0.65rem 0.85rem",
                                borderRadius: "6px",
                                backgroundColor: optBg,
                                border: `1px solid ${optBorder}`,
                                color: optText,
                                fontSize: "0.9rem",
                                cursor: submissionResult ? "default" : "pointer",
                              }}
                            >
                              <input
                                type="radio"
                                name={`q_${q.id}`}
                                checked={isSelected}
                                disabled={Boolean(submissionResult)}
                                onChange={() => setSelectedAnswers({ ...selectedAnswers, [q.id]: opt })}
                              />
                              <span>{opt}</span>
                            </label>
                          );
                        })}
                      </div>
                    ) : (
                      /* Question Type: Short Answer / Conceptual / Coding */
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {q.sample_code_or_io && (
                          <pre style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem 0.8rem", borderRadius: "4px", fontSize: "0.82rem", color: "var(--text-muted)", margin: 0 }}>
                            {q.sample_code_or_io}
                          </pre>
                        )}
                        <textarea
                          className="form-textarea"
                          rows={3}
                          placeholder="Type your structured solution or conceptual explanation..."
                          value={selectedAnswers[q.id] || ""}
                          disabled={Boolean(submissionResult)}
                          onChange={(e) => setSelectedAnswers({ ...selectedAnswers, [q.id]: e.target.value })}
                        />
                      </div>
                    )}

                    {/* Evaluated Feedback */}
                    {evalItem && (
                      <div
                        style={{
                          marginTop: "0.85rem",
                          padding: "0.75rem",
                          backgroundColor: evalItem.is_correct ? "var(--status-good-bg)" : "var(--status-bad-bg)",
                          border: `1px solid ${evalItem.is_correct ? "var(--status-good-border)" : "var(--status-bad-border)"}`,
                          borderRadius: "6px",
                          fontSize: "0.85rem",
                        }}
                      >
                        <div style={{ fontWeight: 700, color: evalItem.is_correct ? "var(--status-good-text)" : "var(--status-bad-text)", marginBottom: "2px" }}>
                          {evalItem.is_correct ? "✓ Correct Solution" : "✗ Needs Review"}
                        </div>
                        <div style={{ color: "var(--text-main)" }}>
                          {evalItem.feedback}
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}

              {/* Action Buttons */}
              <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
                {!submissionResult ? (
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleSubmitQuiz}
                    loading={submitting}
                  >
                    Submit Answers for Evaluation
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    icon={RotateCcw}
                    onClick={handleGenerateQuiz}
                  >
                    Generate New Quiz
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
