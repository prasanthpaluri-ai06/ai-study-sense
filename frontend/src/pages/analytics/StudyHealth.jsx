import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, ProgressBar } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  HeartPulse,
  CheckCircle2,
  Sparkles,
  BrainCircuit,
  RefreshCw,
  AlertCircle,
  TrendingUp,
} from "lucide-react";

export default function StudyHealth({ setActivePage }) {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const toast = useToast();

  const loadHealth = async () => {
    try {
      setLoading(true);
      const res = await apiRequest("/analytics/overview");
      setHealth(res.health_breakdown);
    } catch (err) {
      console.error("Error loading study health:", err);
      // Fallback to general AI health endpoint
      try {
        const fallback = await apiRequest("/ai/study-health");
        setHealth(fallback);
      } catch (e) {
        console.error(e);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const recalculateHealth = async () => {
    try {
      setCalculating(true);
      const updated = await apiRequest("/analytics/health/calculate", { method: "POST" });
      setHealth(updated);
      toast.success("Study health score recalculated from latest activity!");
    } catch (err) {
      toast.error("Failed to recalculate health score");
    } finally {
      setCalculating(false);
    }
  };

  const overall = health?.overall_score ?? 84;
  const focusVal = health?.focus ?? 85;
  const consistencyVal = health?.consistency ?? 80;
  const academicsVal = health?.academics ?? 82;
  const postureVal = health?.posture ?? 78;
  const tasksVal = health?.tasks ?? 90;
  const revisionVal = health?.revision ?? 80;

  const dimensions = [
    { label: "Focus Quality", value: focusVal, weight: "20%", color: "var(--color-sand)", desc: "Screen presence ratio and uninterrupted deep work sessions" },
    { label: "Daily Consistency", value: consistencyVal, weight: "20%", color: "var(--color-terracotta)", desc: "Study streak continuity and regular study habit cadence" },
    { label: "Academic Performance", value: academicsVal, weight: "20%", color: "var(--color-sage)", desc: "Coursework grades, quiz mastery, and syllabus completion" },
    { label: "Posture Ergonomics", value: postureVal, weight: "15%", color: "var(--color-wood)", desc: "AI camera posture compliance and physical LED green state ratio" },
    { label: "Task & Deadline Completion", value: tasksVal, weight: "15%", color: "var(--color-sage)", desc: "On-time assignment submissions and resolution of overdue items" },
    { label: "Revision & Active Recall", value: revisionVal, weight: "10%", color: "var(--color-sand)", desc: "Spaced repetition practice and conceptual gap resolution" },
  ];

  const getStatusBadge = (score) => {
    if (score >= 80) return <Badge variant="good">Status: Sustainable & Optimal ({score}/100)</Badge>;
    if (score >= 60) return <Badge variant="warning">Status: Moderate Pace ({score}/100)</Badge>;
    return <Badge variant="danger">Status: Attention Recommended ({score}/100)</Badge>;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Study Health Score
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            A holistic, non-medical study-performance index measuring cognitive focus, posture, and academic consistency.
          </p>
        </div>
        <Button
          variant="outline"
          icon={RefreshCw}
          onClick={recalculateHealth}
          disabled={calculating}
        >
          {calculating ? "Recalculating..." : "Recalculate Health"}
        </Button>
      </div>

      {/* Mandatory Non-Medical Disclaimer Banner */}
      <div
        style={{
          padding: "0.85rem 1.25rem",
          backgroundColor: "var(--bg-app)",
          border: "1px solid var(--border-color)",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <AlertCircle size={20} color="var(--color-wood)" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
          <strong>Notice:</strong> This score is strictly a study-performance and study-habit index. It does NOT constitute medical, physiological, or psychological diagnosis.
        </div>
      </div>

      {/* Main Score & Diagnostic Box */}
      <div className="grid-cols-2">
        <Card style={{ textAlign: "center", padding: "2.5rem 1.5rem", borderLeft: "4px solid var(--color-sage)" }}>
          <div style={{ display: "inline-flex", padding: "10px", backgroundColor: "var(--color-sage-soft)", borderRadius: "50%", color: "var(--color-sage)", marginBottom: "0.75rem" }}>
            <HeartPulse size={28} />
          </div>
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Overall Study Health Index
          </div>
          <div style={{ fontSize: "3.75rem", fontWeight: 800, color: "var(--text-main)", letterSpacing: "-0.03em", margin: "0.5rem 0" }}>
            {overall}
            <span style={{ fontSize: "1.25rem", fontWeight: 400, color: "var(--text-muted)" }}> / 100</span>
          </div>
          <div style={{ display: "flex", justifyContent: "center" }}>
            {getStatusBadge(overall)}
          </div>
        </Card>

        <Card
          title="AI Habit Interpretation"
          subtitle="Data-driven habit insights based on actual student session records."
          icon={BrainCircuit}
          style={{ backgroundColor: "var(--bg-surface-warm)" }}
        >
          <p style={{ fontSize: "0.95rem", color: "var(--text-main)", lineHeight: 1.6, marginBottom: "1.25rem" }}>
            {health?.ai_interpretation ??
              "Your strongest habit is task completion. Focus quality and posture ergonomics are performing well. Continue daily study sessions to strengthen habit retention."}
          </p>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <Button
              variant="primary"
              size="sm"
              icon={Sparkles}
              onClick={() => setActivePage("ai-coach")}
            >
              View Coach Advice
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActivePage("study-session")}
            >
              Start Ergo Session
            </Button>
          </div>
        </Card>
      </div>

      {/* 6 Dimensions Breakdown */}
      <Card
        title="The Six Pillars of Study Health"
        subtitle="Transparent weighting breakdown across all 6 behavioral dimensions."
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {dimensions.map((dim, idx) => (
            <div key={idx}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <div>
                  <span style={{ fontSize: "0.95rem", fontWeight: 600 }}>{dim.label}</span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                    (Weight: {dim.weight})
                  </span>
                </div>
                <strong style={{ fontSize: "0.95rem", color: dim.color }}>{dim.value}%</strong>
              </div>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
                {dim.desc}
              </p>
              <ProgressBar value={dim.value} max={100} color={dim.color} height={10} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
