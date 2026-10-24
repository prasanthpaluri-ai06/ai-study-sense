import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  Cpu,
  Flame,
  HeartPulse,
  Play,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { apiRequest } from "../api/client";

export default function Dashboard({ setActivePage, hardwareState }) {
  const [healthScore, setHealthScore] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [weaknesses, setWeaknesses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [health, recsData, assignData, subData, sessionsData] = await Promise.all([
          apiRequest("/ai/study-health").catch(() => null),
          apiRequest("/ai/recommendations").catch(() => ({ recommendations: [], weaknesses: [] })),
          apiRequest("/academic/assignments").catch(() => []),
          apiRequest("/academic/subjects").catch(() => []),
          apiRequest("/sessions/recent?limit=3").catch(() => []),
        ]);

        setHealthScore(health);
        setRecommendations(recsData.recommendations || []);
        setWeaknesses(recsData.weaknesses || []);
        setAssignments(assignData || []);
        setSubjects(subData || []);
        setRecentSessions(sessionsData || []);
      } catch (err) {
        console.error("Error loading dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const triggerHardwareTest = async (posture, led, oled, msg) => {
    try {
      await apiRequest("/hardware/command", {
        method: "POST",
        body: JSON.stringify({
          posture,
          led_state: led,
          oled_animation: oled,
          message: msg,
        }),
      });
    } catch (err) {
      console.error("Hardware test error:", err);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Welcome & Quick Action Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h2 style={{ fontSize: "1.75rem", fontWeight: 700 }}>Student Overview</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
            Real-time academic performance, focus metrics, and hardware state synchronization.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button onClick={() => setActivePage("session")} className="btn-primary">
            <Play size={16} />
            <span>Start Study Session</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Metrics Grid */}
      <div className="grid-4">
        {/* Study Health Score */}
        <div className="card" style={{ borderLeft: "4px solid #4f46e5" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>Study Health Score</span>
            <HeartPulse size={18} color="#4f46e5" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f8fafc" }}>
            {healthScore?.overall_score ?? 84}
            <span style={{ fontSize: "1rem", color: "var(--text-muted)", fontWeight: 400 }}> / 100</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#10b981", marginTop: "0.25rem" }}>
            Non-medical habit composite
          </div>
        </div>

        {/* Focus Score */}
        <div className="card" style={{ borderLeft: "4px solid #06b6d4" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>Focus Quality</span>
            <TrendingUp size={18} color="#06b6d4" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f8fafc" }}>
            {healthScore?.focus ?? 86}%
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Attention & presence metric
          </div>
        </div>

        {/* Posture Score */}
        <div className="card" style={{ borderLeft: "4px solid #10b981" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>Posture Health</span>
            <CheckCircle2 size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f8fafc" }}>
            {healthScore?.posture ?? 80}%
          </div>
          <div style={{ fontSize: "0.75rem", color: "#10b981", marginTop: "0.25rem" }}>
            Current LED: {hardwareState?.led_state || "GREEN"}
          </div>
        </div>

        {/* Study Streak */}
        <div className="card" style={{ borderLeft: "4px solid #f59e0b" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>Study Streak</span>
            <Flame size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f8fafc" }}>
            5 Days
          </div>
          <div style={{ fontSize: "0.75rem", color: "#f59e0b", marginTop: "0.25rem" }}>
            Daily consistency target
          </div>
        </div>
      </div>

      {/* Main Grid: AI Recommendations & Assignments */}
      <div className="grid-2">
        {/* AI Recommendations Card */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Sparkles size={18} color="#4f46e5" />
              <h3 className="card-title">AI Academic Coach Recommendations</h3>
            </div>
            <button
              onClick={() => setActivePage("coach")}
              style={{ background: "transparent", color: "var(--primary)", fontSize: "0.85rem", fontWeight: 500 }}
            >
              Open Coach &rarr;
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {recommendations.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "1rem" }}>
                Complete syllabus topics or assessments to receive tailored recommendations.
              </div>
            ) : (
              recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "#0f172a",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    padding: "1rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.3rem" }}>
                    <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{rec.title}</span>
                    <span
                      style={{
                        background: "rgba(79, 70, 229, 0.2)",
                        color: "#a5b4fc",
                        fontSize: "0.75rem",
                        padding: "2px 8px",
                        borderRadius: "12px",
                      }}
                    >
                      {rec.recommended_method || rec.category}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{rec.content}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Approaching Assignments & Deadlines */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Calendar size={18} color="#06b6d4" />
              <h3 className="card-title">Upcoming Deadlines</h3>
            </div>
            <button
              onClick={() => setActivePage("academics")}
              style={{ background: "transparent", color: "var(--primary)", fontSize: "0.85rem", fontWeight: 500 }}
            >
              Manage &rarr;
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {assignments.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "1rem" }}>
                No pending assignments. Click "Academics" to add your coursework.
              </div>
            ) : (
              assignments.slice(0, 4).map((assign) => (
                <div
                  key={assign.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "#0f172a",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    padding: "0.75rem 1rem",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{assign.title}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {assign.subject_name || "Academic Subject"} &bull; Due: {new Date(assign.due_date).toLocaleDateString()}
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      padding: "3px 8px",
                      borderRadius: "6px",
                      background:
                        assign.priority === "Critical"
                          ? "rgba(239, 68, 68, 0.2)"
                          : assign.priority === "High"
                          ? "rgba(245, 158, 11, 0.2)"
                          : "rgba(16, 185, 129, 0.2)",
                      color:
                        assign.priority === "Critical"
                          ? "#ef4444"
                          : assign.priority === "High"
                          ? "#f59e0b"
                          : "#10b981",
                    }}
                  >
                    {assign.priority}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Hardware & Physical Bot Live Control Deck */}
      <div className="card" style={{ background: "linear-gradient(180deg, #1e293b, #0f172a)" }}>
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Cpu size={18} color="#10b981" />
            <h3 className="card-title">Physical Bot & Hardware Synchronization</h3>
          </div>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            ESP32 + OLED (128x64) + Traffic Light
          </span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
          In live study sessions, laptop computer-vision streams posture state automatically. You can also trigger state transmissions below to test physical hardware feedback:
        </p>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button
            onClick={() => triggerHardwareTest("good", "GREEN", "good_posture", "POSTURE GOOD")}
            className="btn-outline"
            style={{ borderColor: "#10b981", color: "#10b981" }}
          >
            🟢 Test Good Posture (Green LED + ^_^)
          </button>
          <button
            onClick={() => triggerHardwareTest("buffer", "YELLOW", "buffer_warning", "SIT STRAIGHT")}
            className="btn-outline"
            style={{ borderColor: "#f59e0b", color: "#f59e0b" }}
          >
            🟡 Test Buffer Warning (Yellow LED + -_-)
          </button>
          <button
            onClick={() => triggerHardwareTest("bad", "RED", "bad_posture", "POSTURE ALERT")}
            className="btn-outline"
            style={{ borderColor: "#ef4444", color: "#ef4444" }}
          >
            🔴 Test Bad Posture (Red LED + &gt;_&lt;)
          </button>
        </div>
      </div>
    </div>
  );
}
