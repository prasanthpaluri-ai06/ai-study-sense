import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  Award,
  CheckCircle,
  Eye,
  Headphones,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  Square,
  Timer,
  Volume2,
} from "lucide-react";
import { apiRequest } from "../api/client";

export default function StudySession({ hardwareState }) {
  const [sessionActive, setSessionActive] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [studyMethod, setStudyMethod] = useState("Pomodoro");
  const [topicName, setTopicName] = useState("");
  const [secondsRemaining, setSecondsRemaining] = useState(25 * 60);
  const [isPaused, setIsPaused] = useState(false);
  const [sessionReport, setSessionReport] = useState(null);
  const [audioCategory, setAudioCategory] = useState("Off");

  // Posture state simulation during study session
  const currentPosture = hardwareState?.posture || "good";
  const currentLed = hardwareState?.led_state || "GREEN";

  useEffect(() => {
    let interval = null;
    if (sessionActive && !isPaused && secondsRemaining > 0) {
      interval = setInterval(() => {
        setSecondsRemaining((prev) => prev - 1);
      }, 1000);
    } else if (secondsRemaining === 0 && sessionActive) {
      handleEndSession();
    }
    return () => clearInterval(interval);
  }, [sessionActive, isPaused, secondsRemaining]);

  const handleStartSession = async () => {
    try {
      const initialMinutes =
        studyMethod === "Pomodoro"
          ? 25
          : studyMethod === "52/17"
          ? 52
          : 30;
      setSecondsRemaining(initialMinutes * 60);

      const res = await apiRequest("/sessions/start", {
        method: "POST",
        body: JSON.stringify({
          topic_name: topicName || "General Study",
          study_method: studyMethod,
        }),
      });

      setActiveSessionId(res.id);
      setSessionActive(true);
      setIsPaused(false);
      setSessionReport(null);
    } catch (err) {
      console.error("Error starting study session:", err);
    }
  };

  const handleEndSession = async () => {
    if (!activeSessionId) return;
    try {
      const res = await apiRequest(`/sessions/${activeSessionId}/end`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      setSessionReport(res);
      setSessionActive(false);
      setActiveSessionId(null);
    } catch (err) {
      console.error("Error ending study session:", err);
    }
  };

  const simulatePostureChange = async (state) => {
    if (!activeSessionId) return;
    const angle = state === "good" ? 12.0 : state === "buffer" ? 28.0 : 42.0;
    try {
      await apiRequest(`/sessions/${activeSessionId}/posture-telemetry`, {
        method: "POST",
        body: JSON.stringify({
          state,
          angle_degrees: angle,
        }),
      });
    } catch (err) {
      console.error("Error logging posture telemetry:", err);
    }
  };

  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 700 }}>Study Session Manager</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Execute structured study methods with real-time posture analysis & ESP32 feedback.
        </p>
      </div>

      <div className="grid-2">
        {/* Left: Study Timer & Controls */}
        <div className="card" style={{ textAlign: "center", padding: "2.5rem 1.5rem" }}>
          {/* Method badge */}
          <div style={{ marginBottom: "1rem" }}>
            <span
              style={{
                background: "rgba(79, 70, 229, 0.2)",
                color: "#a5b4fc",
                padding: "6px 16px",
                borderRadius: "20px",
                fontSize: "0.9rem",
                fontWeight: 600,
              }}
            >
              {studyMethod} Method
            </span>
          </div>

          {/* Large Countdown Display */}
          <div
            style={{
              fontSize: "4.5rem",
              fontWeight: 800,
              fontFamily: "monospace",
              color: "#f8fafc",
              letterSpacing: "-2px",
              margin: "1rem 0",
            }}
          >
            {formatTime(secondsRemaining)}
          </div>

          {/* Configuration Inputs when idle */}
          {!sessionActive && (
            <div style={{ maxWidth: "340px", margin: "0 auto 1.5rem auto", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <input
                type="text"
                placeholder="Topic Name (e.g. Binary Search Trees)"
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
              />
              <select
                value={studyMethod}
                onChange={(e) => setStudyMethod(e.target.value)}
              >
                <option value="Pomodoro">Pomodoro (25m work + 5m rest)</option>
                <option value="52/17">52/17 Method (52m deep work + 17m rest)</option>
                <option value="Active Recall">Active Recall (Recall & Self-Test)</option>
                <option value="Spaced Repetition">Spaced Repetition</option>
                <option value="Feynman Technique">Feynman Technique (Simple Explanation)</option>
              </select>
            </div>
          )}

          {/* Controls */}
          <div style={{ display: "flex", justifyContent: "center", gap: "1rem" }}>
            {!sessionActive ? (
              <button onClick={handleStartSession} className="btn-primary" style={{ padding: "0.75rem 2rem", fontSize: "1rem" }}>
                <Play size={18} />
                <span>Start Session</span>
              </button>
            ) : (
              <>
                <button
                  onClick={() => setIsPaused(!isPaused)}
                  className="btn-outline"
                  style={{ padding: "0.75rem 1.5rem" }}
                >
                  {isPaused ? <Play size={18} /> : <Pause size={18} />}
                  <span>{isPaused ? "Resume" : "Pause"}</span>
                </button>
                <button
                  onClick={handleEndSession}
                  className="btn-outline"
                  style={{ borderColor: "#ef4444", color: "#ef4444", padding: "0.75rem 1.5rem" }}
                >
                  <Square size={18} />
                  <span>End Session</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right: Real-Time Posture & Hardware Telemetry Panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Posture & Hardware Status */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Eye size={18} color="#10b981" />
                <h3 className="card-title">Live Posture & Hardware Monitor</h3>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "1.5rem",
                background: "#0f172a",
                border: "1px solid var(--border)",
                padding: "1.25rem",
                borderRadius: "10px",
                marginBottom: "1rem",
              }}
            >
              {/* Traffic light representation */}
              <div
                style={{
                  width: "60px",
                  height: "60px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.75rem",
                  background:
                    currentLed === "RED"
                      ? "rgba(239, 68, 68, 0.2)"
                      : currentLed === "YELLOW"
                      ? "rgba(245, 158, 11, 0.2)"
                      : "rgba(16, 185, 129, 0.2)",
                  color:
                    currentLed === "RED"
                      ? "#ef4444"
                      : currentLed === "YELLOW"
                      ? "#f59e0b"
                      : "#10b981",
                  border: `2px solid currentColor`,
                }}
              >
                {currentPosture === "good" ? "^_^" : currentPosture === "buffer" ? "-_-" : ">_<"}
              </div>

              <div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, textTransform: "uppercase" }}>
                  Posture State: {currentPosture}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  Traffic Light: <strong>{currentLed}</strong> &bull; ESP32 OLED: <strong>{hardwareState?.oled_animation || "idle"}</strong>
                </div>
              </div>
            </div>

            {sessionActive && (
              <div style={{ marginTop: "0.5rem" }}>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                  Camera Simulation Controls:
                </div>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  <button onClick={() => simulatePostureChange("good")} className="btn-outline" style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}>
                    🟢 Good Posture
                  </button>
                  <button onClick={() => simulatePostureChange("buffer")} className="btn-outline" style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}>
                    🟡 Slouch Warning (Buffer)
                  </button>
                  <button onClick={() => simulatePostureChange("bad")} className="btn-outline" style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}>
                    🔴 Bad Posture Alert
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Ambient Focus Audio */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Headphones size={18} color="#a855f7" />
                <h3 className="card-title">Focus Audio Environment</h3>
              </div>
              <span style={{ fontSize: "0.8rem", color: "#a855f7" }}>{audioCategory}</span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {["Off", "White Noise", "Brown Noise", "Rain Sounds", "Nature", "Lo-Fi Beats"].map((aud) => (
                <button
                  key={aud}
                  onClick={() => setAudioCategory(aud)}
                  className="btn-outline"
                  style={{
                    fontSize: "0.85rem",
                    padding: "0.4rem 0.9rem",
                    background: audioCategory === aud ? "rgba(168, 85, 247, 0.2)" : "transparent",
                    borderColor: audioCategory === aud ? "#a855f7" : "var(--border)",
                    color: audioCategory === aud ? "#c084fc" : "var(--text-main)",
                  }}
                >
                  {aud}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Session Completed Summary Report */}
      {sessionReport && (
        <div className="card" style={{ border: "2px solid #10b981", background: "rgba(16, 185, 129, 0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
            <Award size={24} color="#10b981" />
            <h3 style={{ fontSize: "1.3rem", fontWeight: 700 }}>Study Session Complete Report</h3>
          </div>

          <div className="grid-3" style={{ marginBottom: "1rem" }}>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Study Duration</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{sessionReport.duration_minutes} Mins</div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Posture Score</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#10b981" }}>
                {sessionReport.metric?.posture_score ?? 100}%
              </div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Productivity Score</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#4f46e5" }}>
                {sessionReport.metric?.productivity_score ?? 85} / 100
              </div>
            </div>
          </div>

          <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
            {sessionReport.metric?.ai_feedback_summary}
          </p>
        </div>
      )}
    </div>
  );
}
