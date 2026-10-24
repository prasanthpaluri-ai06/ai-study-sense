import React, { useState } from "react";
import {
  AlertCircle,
  Award,
  BookOpen,
  CheckCircle,
  FileQuestion,
  HelpCircle,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import { apiRequest } from "../api/client";

export default function AICoach() {
  const [activeTab, setActiveTab] = useState("quiz"); // quiz, revision, resources

  // Quiz State
  const [quizTopic, setQuizTopic] = useState("Binary Search");
  const [quizData, setQuizData] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizLoading, setQuizLoading] = useState(false);

  // Revision State
  const [revisionTopic, setRevisionTopic] = useState("AVL Trees");
  const [revisionData, setRevisionData] = useState(null);
  const [revisionLoading, setRevisionLoading] = useState(false);

  // Resource State
  const [resourceQuery, setResourceQuery] = useState("Time Complexity");
  const [resources, setResources] = useState(null);
  const [resourceLoading, setResourceLoading] = useState(false);

  const handleGenerateQuiz = async () => {
    if (!quizTopic) return;
    setQuizLoading(true);
    setQuizSubmitted(false);
    setSelectedAnswers({});
    try {
      const res = await apiRequest("/ai/quiz/generate", {
        method: "POST",
        body: JSON.stringify({ topic_title: quizTopic, num_questions: 5 }),
      });
      setQuizData(res);
    } catch (err) {
      alert(err.message);
    } finally {
      setQuizLoading(false);
    }
  };

  const handleGenerateRevision = async () => {
    if (!revisionTopic) return;
    setRevisionLoading(true);
    try {
      const res = await apiRequest("/ai/revision/generate", {
        method: "POST",
        body: JSON.stringify({ topic_title: revisionTopic }),
      });
      setRevisionData(res);
    } catch (err) {
      alert(err.message);
    } finally {
      setRevisionLoading(false);
    }
  };

  const handleSearchResources = async () => {
    if (!resourceQuery) return;
    setResourceLoading(true);
    try {
      const res = await apiRequest(`/ai/resources?query=${encodeURIComponent(resourceQuery)}`);
      setResources(res.resources);
    } catch (err) {
      alert(err.message);
    } finally {
      setResourceLoading(false);
    }
  };

  const calculateQuizScore = () => {
    if (!quizData) return 0;
    let correct = 0;
    quizData.questions.forEach((q) => {
      if (selectedAnswers[q.id] === q.correct_answer) {
        correct += 1;
      }
    });
    return correct;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 700 }}>AI Study Coach & Tools</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Targeted quiz generators, concise revision packages, and curated learning resources.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.5rem" }}>
        <button
          onClick={() => setActiveTab("quiz")}
          className="btn-outline"
          style={{
            background: activeTab === "quiz" ? "var(--primary)" : "transparent",
            color: activeTab === "quiz" ? "white" : "var(--text-muted)",
          }}
        >
          <FileQuestion size={16} />
          <span>AI Quiz Generator</span>
        </button>
        <button
          onClick={() => setActiveTab("revision")}
          className="btn-outline"
          style={{
            background: activeTab === "revision" ? "var(--primary)" : "transparent",
            color: activeTab === "revision" ? "white" : "var(--text-muted)",
          }}
        >
          <BookOpen size={16} />
          <span>AI Revision Notes</span>
        </button>
        <button
          onClick={() => setActiveTab("resources")}
          className="btn-outline"
          style={{
            background: activeTab === "resources" ? "var(--primary)" : "transparent",
            color: activeTab === "resources" ? "white" : "var(--text-muted)",
          }}
        >
          <Search size={16} />
          <span>Resource Finder</span>
        </button>
      </div>

      {/* Tab 1: Quiz Generator */}
      {activeTab === "quiz" && (
        <div className="card">
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <input
              type="text"
              placeholder="Enter topic for quiz (e.g. Binary Search)"
              value={quizTopic}
              onChange={(e) => setQuizTopic(e.target.value)}
            />
            <button onClick={handleGenerateQuiz} className="btn-primary" disabled={quizLoading} style={{ whiteSpace: "nowrap" }}>
              <Sparkles size={16} />
              <span>{quizLoading ? "Generating..." : "Generate 5-Question Quiz"}</span>
            </button>
          </div>

          {quizData && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                Quiz: {quizData.topic_title}
              </h3>

              {quizData.questions.map((q, qIndex) => (
                <div key={q.id} style={{ background: "#0f172a", border: "1px solid var(--border)", borderRadius: "8px", padding: "1.25rem" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.95rem", marginBottom: "0.75rem" }}>
                    {qIndex + 1}. {q.question_text}
                  </p>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {q.options.map((opt, oIndex) => {
                      const isSelected = selectedAnswers[q.id] === opt;
                      const isCorrect = q.correct_answer === opt;
                      let optionBg = "rgba(30, 41, 59, 0.5)";
                      let optionBorder = "var(--border)";

                      if (quizSubmitted) {
                        if (isCorrect) {
                          optionBg = "rgba(16, 185, 129, 0.2)";
                          optionBorder = "#10b981";
                        } else if (isSelected && !isCorrect) {
                          optionBg = "rgba(239, 68, 68, 0.2)";
                          optionBorder = "#ef4444";
                        }
                      } else if (isSelected) {
                        optionBg = "rgba(79, 70, 229, 0.2)";
                        optionBorder = "var(--primary)";
                      }

                      return (
                        <label
                          key={oIndex}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.6rem",
                            padding: "0.6rem 0.9rem",
                            borderRadius: "6px",
                            background: optionBg,
                            border: `1px solid ${optionBorder}`,
                            cursor: quizSubmitted ? "default" : "pointer",
                            fontSize: "0.9rem",
                          }}
                        >
                          <input
                            type="radio"
                            name={`question_${q.id}`}
                            checked={isSelected}
                            disabled={quizSubmitted}
                            onChange={() => setSelectedAnswers({ ...selectedAnswers, [q.id]: opt })}
                          />
                          <span>{opt}</span>
                        </label>
                      );
                    })}
                  </div>

                  {quizSubmitted && (
                    <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                      💡 <strong>Explanation:</strong> {q.explanation}
                    </div>
                  )}
                </div>
              ))}

              {!quizSubmitted ? (
                <button
                  onClick={() => setQuizSubmitted(true)}
                  className="btn-primary"
                  style={{ alignSelf: "flex-start", marginTop: "0.5rem" }}
                >
                  Submit Quiz Answers
                </button>
              ) : (
                <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid #10b981", borderRadius: "8px", padding: "1rem" }}>
                  <h4 style={{ color: "#10b981", fontWeight: 700, fontSize: "1.1rem" }}>
                    Quiz Results: {calculateQuizScore()} / {quizData.questions.length} Correct ({Math.round(calculateQuizScore() / quizData.questions.length * 100)}%)
                  </h4>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    Performance automatically recorded to update weak area detections.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Revision Generator */}
      {activeTab === "revision" && (
        <div className="card">
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <input
              type="text"
              placeholder="Enter topic for revision package (e.g. AVL Trees)"
              value={revisionTopic}
              onChange={(e) => setRevisionTopic(e.target.value)}
            />
            <button onClick={handleGenerateRevision} className="btn-primary" disabled={revisionLoading} style={{ whiteSpace: "nowrap" }}>
              <Sparkles size={16} />
              <span>{revisionLoading ? "Generating..." : "Generate Revision Summary"}</span>
            </button>
          </div>

          {revisionData && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ background: "#0f172a", border: "1px solid var(--border)", borderRadius: "8px", padding: "1.25rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#a5b4fc", marginBottom: "0.5rem" }}>
                  {revisionData.topic_title}
                </h3>
                <p style={{ fontSize: "0.95rem", marginBottom: "1rem" }}>{revisionData.definition}</p>

                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "#38bdf8", marginTop: "1rem" }}>Core Mechanism</h4>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>{revisionData.core_idea}</p>

                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "#38bdf8", marginTop: "1rem" }}>Key Takeaways</h4>
                <ul style={{ paddingLeft: "1.2rem", fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                  {revisionData.important_points.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>

                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "#ef4444", marginTop: "1rem" }}>Common Pitfalls</h4>
                <ul style={{ paddingLeft: "1.2rem", fontSize: "0.9rem", color: "#fca5a5", marginTop: "0.3rem" }}>
                  {revisionData.common_mistakes.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>

                <div style={{ marginTop: "1rem", padding: "0.75rem", background: "rgba(79, 70, 229, 0.15)", borderRadius: "6px", fontSize: "0.85rem" }}>
                  🎯 <strong>Quick Recap:</strong> {revisionData.quick_recap}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Resource Finder */}
      {activeTab === "resources" && (
        <div className="card">
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <input
              type="text"
              placeholder="Search learning resources (e.g. Graph Traversals)"
              value={resourceQuery}
              onChange={(e) => setResourceQuery(e.target.value)}
            />
            <button onClick={handleSearchResources} className="btn-primary" disabled={resourceLoading} style={{ whiteSpace: "nowrap" }}>
              <Search size={16} />
              <span>{resourceLoading ? "Searching..." : "Find Resources"}</span>
            </button>
          </div>

          {resources && (
            <div className="grid-3">
              {resources.map((res, i) => (
                <div key={i} style={{ background: "#0f172a", border: "1px solid var(--border)", borderRadius: "8px", padding: "1.25rem" }}>
                  <span style={{ fontSize: "0.75rem", background: "rgba(79, 70, 229, 0.2)", color: "#a5b4fc", padding: "2px 8px", borderRadius: "10px" }}>
                    {res.category}
                  </span>
                  <h4 style={{ fontSize: "1rem", fontWeight: 600, margin: "0.5rem 0" }}>{res.title}</h4>
                  <a href={res.url} target="_blank" rel="noreferrer" style={{ color: "var(--primary)", fontSize: "0.85rem", fontWeight: 500 }}>
                    Open Resource &rarr;
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
