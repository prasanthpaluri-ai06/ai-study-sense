import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, ProgressBar } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { focusAudio } from "../../utils/focusAudio";
import { useToast } from "../../context/ToastContext";
import HardwareControlDeck from "../../components/hardware/HardwareControlDeck";
import {
  HeartPulse,
  Clock,
  TrendingUp,
  CheckCircle2,
  Sparkles,
  Calendar,
  AlertTriangle,
  Play,
  Pause,
  ArrowRight,
  Cpu,
  GraduationCap,
  AlertCircle,
  Flame,
  Volume2,
  VolumeX,
  Radio,
  ExternalLink,
  CheckSquare,
  Square,
  Target,
  BookOpen,
} from "lucide-react";
import { formatDate, formatDateTime } from "../../utils/dateUtils";

export default function Dashboard({ setActivePage, hardwareState, setSelectedSessionData }) {
  const [healthScore, setHealthScore] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [weaknesses, setWeaknesses] = useState([]);
  const [academicSummary, setAcademicSummary] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [streakData, setStreakData] = useState({ current_streak_days: 0, longest_streak_days: 0 });
  const [todayTasks, setTodayTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Focus Audio State
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [selectedSound, setSelectedSound] = useState("brown");
  const [audioVolume, setAudioVolume] = useState(0.4);

  const toast = useToast();

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [overviewData, recsData, summaryData, sessionsData, streakRes, plannerToday] = await Promise.all([
          apiRequest("/analytics/overview").catch(() => null),
          apiRequest("/ai/recommendations").catch(() => ({ recommendations: [], weaknesses: [] })),
          apiRequest("/academic/summary").catch(() => null),
          apiRequest("/sessions/recent?limit=4").catch(() => []),
          apiRequest("/analytics/streak").catch(() => ({ current_streak_days: 0, longest_streak_days: 0 })),
          apiRequest("/planner/today").catch(() => []),
        ]);

        if (overviewData?.health_breakdown) {
          setHealthScore(overviewData.health_breakdown);
        }
        setRecommendations(recsData.recommendations || []);
        setWeaknesses(recsData.weaknesses || []);
        setAcademicSummary(summaryData);
        setRecentSessions(sessionsData || []);
        setStreakData(streakRes);
        setTodayTasks(plannerToday || []);
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const handleToggleTodayTask = async (taskId) => {
    try {
      const updated = await apiRequest(`/planner/tasks/${taskId}/toggle`, { method: "PATCH" });
      setTodayTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, is_completed: updated.is_completed } : t))
      );
      toast.success(updated.is_completed ? "Task marked completed!" : "Task marked incomplete");
      // Silently refresh academic summary
      apiRequest("/academic/summary").then(setAcademicSummary).catch(() => {});
    } catch (err) {
      toast.error("Failed to update task.");
    }
  };

  const handleStartTaskSession = (task) => {
    if (setSelectedSessionData) {
      setSelectedSessionData({
        topic: task.title,
        subject_id: task.subject_id,
        method: "Pomodoro",
        duration: 25,
      });
    }
    if (setActivePage) setActivePage("study-session");
  };

  const toggleFocusAudio = () => {
    if (audioPlaying) {
      focusAudio.stop();
      setAudioPlaying(false);
      toast.info("Focus sound paused");
    } else {
      focusAudio.start(selectedSound, audioVolume);
      setAudioPlaying(true);
      toast.success(`Playing ${selectedSound.toUpperCase()} focus sound`);
    }
  };

  const handleSoundChange = (e) => {
    const newSound = e.target.value;
    setSelectedSound(newSound);
    if (audioPlaying) {
      focusAudio.start(newSound, audioVolume);
    }
  };

  const handleVolumeChange = (e) => {
    const vol = parseFloat(e.target.value);
    setAudioVolume(vol);
    focusAudio.setVolume(vol);
  };

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
      toast.success(`Dispatched hardware state: ${led} (${posture.toUpperCase()})`);
    } catch (err) {
      toast.error("Failed sending hardware command");
    }
  };

  const overdueTasks = academicSummary?.overdue_tasks || [];
  const upcomingDeadlines = academicSummary?.upcoming_deadlines || [];
  const topPriorityTask = academicSummary?.top_priority_assignments?.[0];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Welcome Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          paddingBottom: "0.5rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Academic Dashboard
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Real-time study metrics, posture ergonomics, and AI-guided learning priorities.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Button
            variant="outline"
            onClick={() => setActivePage("study-health")}
          >
            Study Health Report
          </Button>
          <Button
            variant="primary"
            icon={Play}
            onClick={() => setActivePage("study-session")}
          >
            Start Session
          </Button>
        </div>
      </div>

      {/* Focus Audio Ambient Sound Bar */}
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "8px",
          padding: "0.85rem 1.25rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          <div
            style={{
              padding: "8px",
              borderRadius: "50%",
              backgroundColor: audioPlaying ? "var(--color-sage)" : "var(--bg-app)",
              color: audioPlaying ? "#FFFFFF" : "var(--text-muted)",
            }}
          >
            <Radio size={18} />
          </div>
          <div>
            <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-main)" }}>
              Focus Audio Generator (Web Audio API)
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Offline synthesized noise to drown out background noise and sustain flow state
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <select
            value={selectedSound}
            onChange={handleSoundChange}
            style={{
              padding: "0.4rem 0.6rem",
              borderRadius: "4px",
              border: "1px solid var(--border-color)",
              backgroundColor: "var(--bg-app)",
              fontSize: "0.85rem",
              color: "var(--text-main)",
            }}
          >
            <option value="brown">Deep Brown Noise</option>
            <option value="white">Pure White Noise</option>
            <option value="rain">Gentle Rain Ambience</option>
            <option value="nature">Forest Breeze</option>
            <option value="lofi">Lo-Fi Harmonic Drone</option>
          </select>

          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Volume2 size={16} color="var(--text-muted)" />
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={audioVolume}
              onChange={handleVolumeChange}
              style={{ width: "80px" }}
            />
          </div>

          <Button
            size="sm"
            variant={audioPlaying ? "outline" : "primary"}
            icon={audioPlaying ? Pause : Play}
            onClick={toggleFocusAudio}
          >
            {audioPlaying ? "Pause Audio" : "Play Noise"}
          </Button>
        </div>
      </div>

      {/* Overdue Task Critical Alert Banner (if any) */}
      {overdueTasks.length > 0 && (
        <div
          style={{
            backgroundColor: "var(--status-bad-bg)",
            border: "1px solid var(--status-bad-border)",
            borderRadius: "8px",
            padding: "0.85rem 1.25rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <AlertCircle size={20} color="var(--color-terracotta)" />
            <div>
              <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--status-bad-text)" }}>
                {overdueTasks.length} Overdue Assignment{overdueTasks.length > 1 ? "s" : ""} Requiring Immediate Submission
              </span>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                {overdueTasks.map((t) => t.title).slice(0, 2).join(", ")}{overdueTasks.length > 2 ? "..." : ""}
              </div>
            </div>
          </div>
          <Button
            size="sm"
            variant="primary"
            style={{ backgroundColor: "var(--color-terracotta)", borderColor: "var(--color-terracotta)" }}
            onClick={() => setActivePage("assignments")}
          >
            Resolve Overdue Tasks &rarr;
          </Button>
        </div>
      )}

      {/* 4 KPI Cards in Solid Pastel Earthy Colors */}
      <div className="grid-cols-4">
        {/* 1. Study Health Score */}
        <Card style={{ borderLeft: "4px solid var(--color-sage)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Study Health</span>
            <HeartPulse size={16} color="var(--color-sage)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)", lineHeight: 1.2 }}>
            {healthScore?.overall_score ?? 84}
            <span style={{ fontSize: "0.95rem", color: "var(--text-muted)", fontWeight: 400 }}> / 100</span>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            Non-medical study habit index
          </div>
        </Card>

        {/* 2. Academic Performance */}
        <Card style={{ borderLeft: "4px solid var(--color-sand)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Academic Mastery</span>
            <GraduationCap size={16} color="var(--color-sand)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)", lineHeight: 1.2 }}>
            {academicSummary?.overall_weighted_gpa_score !== null && academicSummary?.overall_weighted_gpa_score !== undefined
              ? `${academicSummary.overall_weighted_gpa_score}%`
              : "85.0%"}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            Weighted average across {academicSummary?.total_subjects ?? 0} courses
          </div>
        </Card>

        {/* 3. Study Streak */}
        <Card style={{ borderLeft: "4px solid var(--color-terracotta)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Study Streak</span>
            <Flame size={16} color="var(--color-terracotta)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)", lineHeight: 1.2 }}>
            {streakData.current_streak_days} <span style={{ fontSize: "0.95rem", color: "var(--text-muted)", fontWeight: 400 }}>Days</span>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            Best record: {streakData.longest_streak_days} consecutive days
          </div>
        </Card>

        {/* 4. Coursework Tasks & Completion */}
        <Card style={{ borderLeft: "4px solid var(--color-wood)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Coursework</span>
            <Calendar size={16} color="var(--color-wood)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)", lineHeight: 1.2 }}>
            {academicSummary?.pending_assignments_count ?? 0} Pending
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            {academicSummary?.completed_assignments_count ?? 0} completed ({academicSummary?.completion_rate_percent ?? 0}%)
          </div>
        </Card>
      </div>

      {/* Top AI Prioritized Task Banner (if available) */}
      {topPriorityTask && (
        <Card
          style={{
            backgroundColor: "var(--bg-app)",
            border: "1px solid var(--color-sage)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.9rem" }}>
              <div
                style={{
                  padding: "10px",
                  borderRadius: "8px",
                  backgroundColor: "var(--color-sage)",
                  color: "#FFFFFF",
                }}
              >
                <Sparkles size={22} />
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", color: "var(--color-sage)" }}>
                    #1 AI Prioritized Deliverable
                  </span>
                  <Badge variant="danger">Score: {topPriorityTask.priority_score}/100</Badge>
                </div>
                <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-main)", marginTop: "2px" }}>
                  {topPriorityTask.title} ({topPriorityTask.subject_name})
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  {topPriorityTask.recommendation_reason}
                </div>
              </div>
            </div>

            <Button
              variant="primary"
              onClick={() => setActivePage("assignments")}
            >
              Open Assignments &rarr;
            </Button>
          </div>
        </Card>
      )}

      {/* Today's Consolidated Academic Checklist (Requirement 5) */}
      <Card
        title="Today's Academic Checklist"
        subtitle={`All subjects' study tasks scheduled for today (${todayTasks.filter(t => t.is_completed).length}/${todayTasks.length} completed)`}
        icon={Target}
        action={
          <Button size="sm" variant="outline" onClick={() => setActivePage("ai-coach")}>
            Open Academic Planner &rarr;
          </Button>
        }
      >
        {todayTasks.length === 0 ? (
          <div
            style={{
              padding: "1.75rem",
              textAlign: "center",
              backgroundColor: "var(--bg-app)",
              border: "1px dashed var(--border-color)",
              borderRadius: "8px",
            }}
          >
            <CheckCircle2 size={28} color="var(--color-sage)" style={{ margin: "0 auto 0.5rem auto" }} />
            <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)" }}>
              No Study Tasks Scheduled for Today
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: "4px auto 0.75rem auto", maxWidth: "420px" }}>
              You're all caught up for today, or your semester schedule has this day as an off-day. Configure dates or add study tasks in the planner.
            </p>
            <Button size="sm" variant="primary" onClick={() => setActivePage("ai-coach")}>
              Customize Schedule in AI Planner
            </Button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {todayTasks.map((t) => {
              const isDone = t.is_completed;
              return (
                <div
                  key={`dash-task-${t.id}`}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.75rem 1rem",
                    backgroundColor: isDone ? "var(--bg-surface-soft)" : "var(--bg-app)",
                    border: "1px solid var(--border-subtle)",
                    borderLeft: `4px solid ${isDone ? "var(--text-muted)" : t.subject_color || "var(--color-sage)"}`,
                    borderRadius: "6px",
                    gap: "0.75rem",
                    flexWrap: "wrap",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flex: 1, minWidth: "220px" }}>
                    <button
                      onClick={() => handleToggleTodayTask(t.id)}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 0,
                        color: isDone ? "var(--color-sage)" : "var(--text-muted)",
                        display: "flex",
                        alignItems: "center",
                      }}
                      title={isDone ? "Mark incomplete" : "Mark completed"}
                    >
                      {isDone ? <CheckSquare size={20} /> : <Square size={20} />}
                    </button>

                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "2px" }}>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            padding: "1px 6px",
                            borderRadius: "3px",
                            backgroundColor: `${t.subject_color || "#5A6E52"}18`,
                            color: t.subject_color || "var(--color-sage)",
                          }}
                        >
                          {t.subject_name || "General"}
                        </span>
                        <span
                          style={{
                            fontSize: "0.72rem",
                            padding: "1px 5px",
                            borderRadius: "3px",
                            backgroundColor: "var(--bg-surface-soft)",
                            color: "var(--text-muted)",
                            textTransform: "capitalize",
                          }}
                        >
                          {t.task_type}
                        </span>
                        <Badge variant={t.priority === "Critical" ? "danger" : t.priority === "High" ? "warning" : "neutral"}>
                          {t.priority}
                        </Badge>
                      </div>

                      <div
                        style={{
                          fontSize: "0.92rem",
                          fontWeight: 600,
                          color: "var(--text-main)",
                          textDecoration: isDone ? "line-through" : "none",
                          opacity: isDone ? 0.6 : 1,
                        }}
                      >
                        {t.title}
                      </div>

                      {t.module_name && (
                        <div style={{ fontSize: "0.76rem", color: "var(--text-muted)" }}>
                          {t.module_name}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Button
                      size="sm"
                      variant="ghost"
                      icon={BookOpen}
                      onClick={() => setActivePage("roadmap")}
                      title="View syllabus roadmap"
                    >
                      Syllabus
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      icon={Play}
                      onClick={() => handleStartTaskSession(t)}
                    >
                      Study Now
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Main 2-Column Section */}
      <div className="grid-cols-2">
        {/* Left Column: AI Study Coach Recommendations */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <Card
            title="AI Coach Recommendations"
            subtitle="Prioritized study actions synthesized from assignments, quizzes & weaknesses."
            icon={Sparkles}
            action={
              <Button size="sm" variant="ghost" onClick={() => setActivePage("ai-coach")}>
                All Actions &rarr;
              </Button>
            }
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {recommendations.length === 0 ? (
                <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  No active recommendations. Complete a study session or quiz to generate personalized suggestions.
                </div>
              ) : (
                recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "6px",
                      padding: "1rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.3rem" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-main)" }}>
                        {rec.title}
                      </span>
                      <Badge variant="neutral">
                        {rec.recommended_method || rec.category}
                      </Badge>
                    </div>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.6rem" }}>
                      {rec.content}
                    </p>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setActivePage("quiz-generator")}
                      >
                        Take Topic Quiz
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setActivePage("revision-generator")}
                      >
                        Revision Notes
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Identified Weak Areas */}
          {weaknesses.length > 0 && (
            <Card
              title="Identified Knowledge Gaps"
              subtitle="Topics where assessment or quiz scores are below mastery threshold."
              icon={AlertTriangle}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {weaknesses.map((w, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.65rem 0.85rem",
                      backgroundColor: "var(--status-buffer-bg)",
                      border: "1px solid var(--status-buffer-border)",
                      borderRadius: "6px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--status-buffer-text)" }}>
                        {w.topic}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {w.reason}
                      </div>
                    </div>
                    <Badge variant={w.severity === "High" ? "danger" : "warning"}>
                      Score: {w.score}%
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Approaching Deadlines & Recent Study Sessions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Upcoming Assignments */}
          <Card
            title="Approaching Deadlines"
            subtitle="Prioritized coursework due dates"
            icon={Calendar}
            action={
              <Button size="sm" variant="ghost" onClick={() => setActivePage("assignments")}>
                View All &rarr;
              </Button>
            }
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
              {upcomingDeadlines.length === 0 ? (
                <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.88rem" }}>
                  No pending assignments. Click "Assignments" to add tasks.
                </div>
              ) : (
                upcomingDeadlines.map((a) => (
                  <div
                    key={a.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.65rem 0.85rem",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "6px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-main)" }}>
                        {a.title}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {a.subject_name || "Academic Subject"} &bull; Due: {formatDate(a.due_date)}
                      </div>
                    </div>
                    <Badge variant={a.priority === "Critical" ? "danger" : a.priority === "High" ? "warning" : "good"}>
                      {a.priority}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Recent Study Sessions */}
          <Card
            title="Recent Study Activity"
            subtitle="Completed sessions and focus analytics"
            icon={Clock}
            action={
              <Button size="sm" variant="ghost" onClick={() => setActivePage("session-analytics")}>
                History &rarr;
              </Button>
            }
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
              {recentSessions.length === 0 ? (
                <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.88rem" }}>
                  No sessions recorded yet. Start your first session today!
                </div>
              ) : (
                recentSessions.map((s) => (
                  <div
                    key={s.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.65rem 0.85rem",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "6px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "0.88rem", fontWeight: 600 }}>
                        {s.topic_name || "Study Session"} ({s.study_method})
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {s.duration_minutes} mins &bull; {formatDate(s.start_time)}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--color-sage)" }}>
                        Focus: {s.metric?.focus_score ?? 100}%
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        Posture: {s.metric?.posture_score ?? 100}%
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Hardware & ESP32 Live Control Deck */}
      <HardwareControlDeck hardwareState={hardwareState} />
    </div>
  );
}

