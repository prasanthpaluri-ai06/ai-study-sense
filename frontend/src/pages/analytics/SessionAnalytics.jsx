import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState, ProgressBar } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import {
  BarChart2,
  Clock,
  CheckCircle2,
  TrendingUp,
  Play,
  Calendar,
  Sparkles,
  Flame,
  Activity,
  ChevronRight,
  Eye,
  AlertTriangle,
  X,
} from "lucide-react";
import { formatDate, formatDateTime } from "../../utils/dateUtils";

export default function SessionAnalytics({ setActivePage }) {
  const [sessions, setSessions] = useState([]);
  const [trends, setTrends] = useState({ points: [], ai_summary: "", timeframe: "daily" });
  const [streakData, setStreakData] = useState({ current_streak_days: 0, longest_streak_days: 0, recent_30_days_activity: [] });
  const [timeframe, setTimeframe] = useState("daily");
  const [selectedSessionReport, setSelectedSessionReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [recent, trendRes, streakRes] = await Promise.all([
          apiRequest("/sessions/recent?limit=20").catch(() => []),
          apiRequest(`/analytics/trends?timeframe=${timeframe}`).catch(() => ({ points: [], ai_summary: "" })),
          apiRequest("/analytics/streak").catch(() => ({ current_streak_days: 0, longest_streak_days: 0, recent_30_days_activity: [] })),
        ]);
        setSessions(recent);
        setTrends(trendRes);
        setStreakData(streakRes);
      } catch (err) {
        console.error("Error loading analytics data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [timeframe]);

  const viewSessionReport = async (sessionId) => {
    try {
      setReportLoading(true);
      const report = await apiRequest(`/analytics/session/${sessionId}/report`);
      setSelectedSessionReport(report);
    } catch (err) {
      console.error("Error fetching session report:", err);
    } finally {
      setReportLoading(false);
    }
  };

  const totalStudyMinutes = sessions.reduce((acc, s) => acc + (s.duration_minutes || 0), 0);
  const avgPosture =
    sessions.length > 0
      ? Math.round(
          sessions.reduce((acc, s) => acc + (s.metric?.posture_score || 100), 0) / sessions.length
        )
      : 100;
  const avgFocus =
    sessions.length > 0
      ? Math.round(
          sessions.reduce((acc, s) => acc + (s.metric?.focus_score || 100), 0) / sessions.length
        )
      : 100;
  const avgProductivity =
    sessions.length > 0
      ? Math.round(
          sessions.reduce((acc, s) => acc + (s.metric?.productivity_score || 85), 0) / sessions.length
        )
      : 85;

  const maxTrendMins = Math.max(...(trends.points || []).map((p) => p.total_minutes || 0), 60);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Session Analytics & Student Growth
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Transparent study duration metrics, ergonomic posture tracking, productivity scoring, and habit streaks.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Button
            variant={timeframe === "daily" ? "primary" : "outline"}
            size="sm"
            onClick={() => setTimeframe("daily")}
          >
            Daily Trends
          </Button>
          <Button
            variant={timeframe === "weekly" ? "primary" : "outline"}
            size="sm"
            onClick={() => setTimeframe("weekly")}
          >
            Weekly Trends
          </Button>
        </div>
      </div>

      {/* Aggregate KPI Cards */}
      <div className="grid-cols-4">
        <Card style={{ borderLeft: "4px solid var(--color-sage)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
            Total Study Time
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--text-main)", marginTop: "0.25rem" }}>
            {totalStudyMinutes.toFixed(1)} <span style={{ fontSize: "0.9rem", fontWeight: 400 }}>Mins</span>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Across {sessions.length} logged sessions
          </div>
        </Card>

        <Card style={{ borderLeft: "4px solid var(--color-wood)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
            Posture Health Index
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--color-wood)", marginTop: "0.25rem" }}>
            {avgPosture}%
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Traffic light ergonomics rate
          </div>
        </Card>

        <Card style={{ borderLeft: "4px solid var(--color-sand)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
            Focus & Presence
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--color-sand)", marginTop: "0.25rem" }}>
            {avgFocus}%
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Screen engagement ratio
          </div>
        </Card>

        <Card style={{ borderLeft: "4px solid var(--color-terracotta)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
              Study Streak
            </span>
            <Flame size={16} color="var(--color-terracotta)" />
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--color-terracotta)", marginTop: "0.25rem" }}>
            {streakData.current_streak_days} <span style={{ fontSize: "0.9rem", fontWeight: 400 }}>Days</span>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Longest recorded: {streakData.longest_streak_days} days
          </div>
        </Card>
      </div>

      {/* Long-Term Progress Chart & AI Trend Summary */}
      <Card
        title={`${timeframe.toUpperCase()} Study Volume & Ergonomics Trend`}
        subtitle="Time-series tracking of total study duration and posture quality."
        icon={TrendingUp}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* AI Trend Plain Language Summary Banner */}
          <div
            style={{
              padding: "0.85rem 1.15rem",
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
            }}
          >
            <Sparkles size={20} color="var(--color-sage)" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: "0.9rem", color: "var(--text-main)", lineHeight: 1.5 }}>
              <strong>AI Trend Analysis:</strong> {trends.ai_summary || "Maintain regular study sessions to generate detailed AI trend summaries."}
            </div>
          </div>

          {/* SVG/Bar Chart */}
          {(!trends.points || trends.points.length === 0) ? (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
              No trend data available for this timeframe.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  gap: "0.75rem",
                  height: "180px",
                  padding: "1rem 0.5rem 0.5rem 0.5rem",
                  borderBottom: "2px solid var(--border-color)",
                }}
              >
                {trends.points.map((pt, idx) => {
                  const heightPercent = Math.max(8, Math.round((pt.total_minutes / maxTrendMins) * 100));
                  return (
                    <div
                      key={idx}
                      style={{
                        flex: 1,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        height: "100%",
                        justifyContent: "flex-end",
                        gap: "0.35rem",
                      }}
                    >
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        {pt.total_minutes.toFixed(0)}m
                      </span>
                      <div
                        style={{
                          width: "100%",
                          maxWidth: "36px",
                          height: `${heightPercent}%`,
                          backgroundColor: "var(--color-sage)",
                          borderRadius: "4px 4px 0 0",
                          transition: "height 0.3s ease",
                        }}
                        title={`Date: ${pt.date} | Study: ${pt.total_minutes} mins | Focus: ${pt.avg_focus}% | Posture: ${pt.avg_posture}%`}
                      />
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {pt.date.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div style={{ display: "flex", justifyContent: "center", gap: "1.5rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <span style={{ width: "10px", height: "10px", backgroundColor: "var(--color-sage)", borderRadius: "2px" }} />
                  Study Minutes
                </span>
                <span>Max Benchmark: {maxTrendMins.toFixed(0)} mins</span>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* 30-Day Activity Map Grid */}
      <Card
        title="30-Day Consistency Map"
        subtitle="Tracking daily study discipline without judging pace."
        icon={Calendar}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
          {(streakData.recent_30_days_activity || []).map((day, idx) => {
            const hasActivity = day.study_minutes > 0;
            return (
              <div
                key={idx}
                title={`${day.date}: ${day.study_minutes.toFixed(1)} mins (${day.sessions_count} sessions)`}
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "4px",
                  backgroundColor: hasActivity ? "var(--color-sage)" : "var(--bg-app)",
                  border: `1px solid ${hasActivity ? "var(--color-sage)" : "var(--border-color)"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.65rem",
                  color: hasActivity ? "#FFFFFF" : "var(--text-muted)",
                  fontWeight: hasActivity ? 700 : 400,
                  cursor: "default",
                }}
              >
                {day.date.slice(8)}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Sessions History Table & Inspection */}
      <Card
        title="Detailed Session History & Reports"
        subtitle="Inspect individual session productivity formula calculations, posture metrics, and AI coaching reports."
        icon={BarChart2}
      >
        {sessions.length === 0 ? (
          <EmptyState
            icon={BarChart2}
            title="No Completed Study Sessions"
            description="Complete study sessions using the timer to view full ergonomic and focus breakdowns."
            action={
              <Button variant="primary" icon={Play} onClick={() => setActivePage("study-session")}>
                Start New Session
              </Button>
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.8rem", textTransform: "uppercase" }}>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Topic & Method</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Duration</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Focus Quality</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Posture Health</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Productivity Score</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Date</th>
                  <th style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>Report</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.75rem 0.5rem" }}>
                      <div style={{ fontWeight: 600 }}>{s.topic_name || "General Study"}</div>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{s.study_method}</span>
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem" }}>{s.duration_minutes} mins</td>
                    <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600, color: "var(--color-sage)" }}>
                      {s.metric?.focus_score ?? 100}%
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600, color: "var(--color-wood)" }}>
                      {s.metric?.posture_score ?? 100}%
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem" }}>
                      <Badge variant="good">
                        {s.metric?.productivity_score ?? 85} / 100
                      </Badge>
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-muted)" }}>
                      {formatDate(s.start_time)}
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>
                      <Button
                        size="sm"
                        variant="outline"
                        icon={Eye}
                        onClick={() => viewSessionReport(s.id)}
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Session Report Modal */}
      {selectedSessionReport && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-surface)",
              borderRadius: "10px",
              maxWidth: "680px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 10px 25px rgba(0, 0, 0, 0.15)",
              border: "1px solid var(--border-color)",
              padding: "1.75rem",
              display: "flex",
              flexDirection: "column",
              gap: "1.25rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <span style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", color: "var(--color-sage)" }}>
                  Verified Session Report
                </span>
                <h2 style={{ fontSize: "1.35rem", fontWeight: 700, color: "var(--text-main)", marginTop: "2px" }}>
                  {selectedSessionReport.session.topic_name || "Study Session"} ({selectedSessionReport.session.study_method})
                </h2>
                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  Logged: {formatDateTime(selectedSessionReport.session.start_time)}
                </div>
              </div>
              <Button size="sm" variant="ghost" icon={X} onClick={() => setSelectedSessionReport(null)} />
            </div>

            {/* Score Highlight */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-around",
                backgroundColor: "var(--bg-app)",
                padding: "1rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                textAlign: "center",
              }}
            >
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Duration</div>
                <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{selectedSessionReport.session.duration_minutes}m</div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Focus</div>
                <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--color-sand)" }}>
                  {selectedSessionReport.metrics.focus_score}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Posture</div>
                <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--color-wood)" }}>
                  {selectedSessionReport.metrics.posture_score}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Productivity</div>
                <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--color-sage)" }}>
                  {selectedSessionReport.metrics.productivity_score}/100
                </div>
              </div>
            </div>

            {/* Formula Explanation */}
            <div style={{ padding: "0.85rem", backgroundColor: "var(--bg-surface-warm)", borderRadius: "6px", fontSize: "0.82rem", color: "var(--text-muted)" }}>
              <strong>Productivity Score Formula:</strong> 0.40 &times; Focus ({selectedSessionReport.metrics.focus_score}%) + 0.35 &times; Posture ({selectedSessionReport.metrics.posture_score}%) + 0.25 &times; Duration Quality - 2.5 &times; Distractions ({selectedSessionReport.metrics.distractions_count || 0}) = <strong>{selectedSessionReport.metrics.productivity_score} pts</strong>.
            </div>

            {/* AI Session Summary & Recommendations */}
            <div>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "0.4rem" }}>
                AI Session Summary
              </h4>
              <p style={{ fontSize: "0.88rem", color: "var(--text-main)", lineHeight: 1.5 }}>
                {selectedSessionReport.ai_summary}
              </p>
            </div>

            {selectedSessionReport.recommendations && selectedSessionReport.recommendations.length > 0 && (
              <div>
                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "0.4rem" }}>
                  Actionable AI Advice
                </h4>
                <ul style={{ paddingLeft: "1.2rem", fontSize: "0.85rem", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                  {selectedSessionReport.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Button variant="primary" onClick={() => setSelectedSessionReport(null)}>
                Close Report
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
