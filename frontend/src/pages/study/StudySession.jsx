import React, { useEffect, useState, useRef } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { Modal } from "../../components/common/Modal";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Play,
  Pause,
  Square,
  XCircle,
  Timer,
  Eye,
  Award,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  Clock,
  HelpCircle,
  Repeat,
  Layers,
  SlidersHorizontal,
  Coffee,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Smartphone,
  UserX,
  ShieldCheck,
} from "lucide-react";
import LaptopCameraHUD from "../../components/camera/LaptopCameraHUD";

export default function StudySession({
  hardwareState,
  initialMethod = "Pomodoro",
  initialSessionData = null,
  setActivePage = null,
}) {
  // Session Lifecycle State
  const [sessionActive, setSessionActive] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [studyMethod, setStudyMethod] = useState(initialMethod || "Pomodoro");
  const [subjectId, setSubjectId] = useState("");
  const [topicName, setTopicName] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);
  const [todayTasks, setTodayTasks] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  // Timer & Cycle States
  const [timerMode, setTimerMode] = useState("work"); // work | break | long_break
  const [secondsRemaining, setSecondsRemaining] = useState(25 * 60);
  const [isPaused, setIsPaused] = useState(false);
  const [currentCycle, setCurrentCycle] = useState(1);
  const [totalCycles, setTotalCycles] = useState(4);
  const [workDurationMins, setWorkDurationMins] = useState(25);
  const [breakDurationMins, setBreakDurationMins] = useState(5);

  // High-Precision Wall-Clock Timer Tracking (Drift-Free)
  const timerStartTimeRef = useRef(null);
  const initialSecondsRemainingRef = useRef(25 * 60);
  const totalActiveElapsedMsRef = useRef(0);
  const lastActiveResumeTimeRef = useRef(null);

  // Real-Time Event Counters from Vision Engine
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [sessionMetrics, setSessionMetrics] = useState({
    postureWarnings: 0,
    badPostureEvents: 0,
    placeAbsenceEvents: 0,
    phoneUseEvents: 0,
  });

  // Method-Specific Interactive States
  // 1. Active Recall:
  const [recallPrompts, setRecallPrompts] = useState([
    {
      prompt: "What is the primary characteristic of a Balanced Binary Search Tree?",
      answer: "The height difference between left and right subtrees (balance factor) is at most 1 for all nodes (O(log n) search/insert).",
      recalled: null,
    },
    {
      prompt: "State the Time Complexity of HeapSort in the worst case.",
      answer: "O(n log n) time in all cases with O(1) auxiliary space.",
      recalled: null,
    },
  ]);
  const [currentRecallIdx, setCurrentRecallIdx] = useState(0);
  const [showRecallAnswer, setShowRecallAnswer] = useState(false);
  const [customPromptInput, setCustomPromptInput] = useState("");
  const [customAnswerInput, setCustomAnswerInput] = useState("");

  // 2. Spaced Repetition (SM-2):
  const [srCards, setSrCards] = useState([]);
  const [currentSrIdx, setCurrentSrIdx] = useState(0);
  const [showSrAnswer, setShowSrAnswer] = useState(false);

  // 3. Feynman Technique:
  const [feynmanStage, setFeynmanStage] = useState(1);
  const [feynmanExplanation, setFeynmanExplanation] = useState("");
  const [feynmanGaps, setFeynmanGaps] = useState("");
  const [feynmanRevision, setFeynmanRevision] = useState("");
  const [feynmanAnalogy, setFeynmanAnalogy] = useState("");

  // End Session Confirmation Modal & Notes
  const [showEndModal, setShowEndModal] = useState(false);
  const [sessionNotes, setSessionNotes] = useState("");
  const [sessionReport, setSessionReport] = useState(null);
  const [audioMode, setAudioMode] = useState("Off");
  const [loading, setLoading] = useState(false);

  const toast = useToast();

  const currentPosture = hardwareState?.posture || "good";
  const currentLed = hardwareState?.led_state || "GREEN";

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (initialSessionData) {
      if (initialSessionData.method) {
        setStudyMethod(initialSessionData.method);
        applyDefaultTimerForMethod(initialSessionData.method);
      }
      if (initialSessionData.topic) {
        setTopicName(initialSessionData.topic);
      }
      if (initialSessionData.duration) {
        setWorkDurationMins(initialSessionData.duration);
        setSecondsRemaining(initialSessionData.duration * 60);
      }
      if (initialSessionData.break_duration) {
        setBreakDurationMins(initialSessionData.break_duration);
      }
      if (initialSessionData.cycles) {
        setTotalCycles(initialSessionData.cycles);
      }
    } else if (initialMethod) {
      setStudyMethod(initialMethod);
      applyDefaultTimerForMethod(initialMethod);
    }
  }, [initialMethod, initialSessionData]);

  async function loadInitialData() {
    try {
      const [subs, recents, cards, todayPlan] = await Promise.all([
        apiRequest("/academic/subjects").catch(() => []),
        apiRequest("/sessions/recent?limit=8").catch(() => []),
        apiRequest("/sessions/spaced-repetition/cards?only_due=false").catch(() => []),
        apiRequest("/planner/today").catch(() => []),
      ]);
      setSubjects(subs || []);
      setRecentSessions(recents || []);
      setSrCards(cards || []);
      setTodayTasks(Array.isArray(todayPlan) ? todayPlan : []);
      if (subs && subs.length > 0 && !subjectId) {
        setSubjectId(String(subs[0].id));
      }
    } catch (err) {
      console.error("Initial data load error:", err);
    }
  }

  const handleSelectTodayTask = (task) => {
    setSelectedTaskId(task.id);
    if (task.subject_id) {
      setSubjectId(String(task.subject_id));
    }
    if (task.title) {
      setTopicName(task.title);
    }
    toast.success(`Selected "${task.title}" for study session.`);
  };

  const handleToggleTodayTask = async (taskId) => {
    try {
      const updated = await apiRequest(`/planner/tasks/${taskId}/toggle`, { method: "PATCH" });
      setTodayTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)));
      if (updated.is_completed) {
        toast.success(`Completed "${updated.title}"!`);
      }
    } catch (e) {
      toast.error("Failed updating task status.");
    }
  };

  const applyDefaultTimerForMethod = (method) => {
    if (method === "Pomodoro") {
      setWorkDurationMins(25);
      setBreakDurationMins(5);
      setTotalCycles(4);
      setSecondsRemaining(25 * 60);
      setTimerMode("work");
    } else if (method === "52/17") {
      setWorkDurationMins(52);
      setBreakDurationMins(17);
      setTotalCycles(2);
      setSecondsRemaining(52 * 60);
      setTimerMode("work");
    } else if (method === "Active Recall") {
      setWorkDurationMins(30);
      setBreakDurationMins(5);
      setSecondsRemaining(30 * 60);
      setTimerMode("work");
    } else if (method === "Spaced Repetition") {
      setWorkDurationMins(20);
      setBreakDurationMins(5);
      setSecondsRemaining(20 * 60);
      setTimerMode("work");
    } else if (method === "Feynman Technique") {
      setWorkDurationMins(40);
      setBreakDurationMins(5);
      setSecondsRemaining(40 * 60);
      setTimerMode("work");
    } else if (method === "Custom") {
      setWorkDurationMins(30);
      setBreakDurationMins(10);
      setTotalCycles(3);
      setSecondsRemaining(30 * 60);
      setTimerMode("work");
    }
  };

  // High-Precision Drift-Free Timer Countdown Engine
  useEffect(() => {
    let interval = null;
    if (sessionActive && !isPaused && secondsRemaining > 0) {
      timerStartTimeRef.current = Date.now();
      initialSecondsRemainingRef.current = secondsRemaining;

      interval = setInterval(() => {
        const elapsedSec = Math.floor((Date.now() - timerStartTimeRef.current) / 1000);
        const rem = Math.max(0, initialSecondsRemainingRef.current - elapsedSec);
        setSecondsRemaining(rem);
        if (rem === 0) {
          clearInterval(interval);
          handleTimerIntervalFinished();
        }
      }, 250);
    } else if (secondsRemaining === 0 && sessionActive) {
      handleTimerIntervalFinished();
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [sessionActive, isPaused, timerMode, currentCycle]);

  const handleTimerIntervalFinished = () => {
    if (studyMethod === "Pomodoro" || studyMethod === "Custom") {
      if (timerMode === "work") {
        if (currentCycle < totalCycles) {
          setTimerMode("break");
          setSecondsRemaining(breakDurationMins * 60);
          if (activeSessionId) {
            apiRequest(`/sessions/${activeSessionId}/break?break_duration_mins=${breakDurationMins}`, { method: "POST" }).catch(() => {});
          }
          toast.info(`Cycle ${currentCycle} complete! Take a ${breakDurationMins}-minute break.`);
        } else {
          setTimerMode("long_break");
          setSecondsRemaining(15 * 60);
          if (activeSessionId) {
            apiRequest(`/sessions/${activeSessionId}/break?break_duration_mins=15`, { method: "POST" }).catch(() => {});
          }
          toast.success("All configured cycles complete! Take a 15-minute rest.");
        }
      } else {
        const nextCycle = currentCycle + 1;
        setCurrentCycle(nextCycle > totalCycles ? 1 : nextCycle);
        setTimerMode("work");
        setSecondsRemaining(workDurationMins * 60);
        if (activeSessionId) {
          apiRequest(`/sessions/${activeSessionId}/break-end?work_duration_mins=${workDurationMins}`, { method: "POST" }).catch(() => {});
        }
        toast.info(`Break complete. Resuming Focus Cycle ${nextCycle > totalCycles ? 1 : nextCycle}!`);
      }
    } else if (studyMethod === "52/17") {
      if (timerMode === "work") {
        setTimerMode("break");
        setSecondsRemaining(17 * 60);
        if (activeSessionId) {
          apiRequest(`/sessions/${activeSessionId}/break?break_duration_mins=17`, { method: "POST" }).catch(() => {});
        }
        toast.info("52-minute Deep Work sprint finished! Disengage from screens for 17 minutes.");
      } else {
        setTimerMode("work");
        setSecondsRemaining(52 * 60);
        if (activeSessionId) {
          apiRequest(`/sessions/${activeSessionId}/break-end?work_duration_mins=52`, { method: "POST" }).catch(() => {});
        }
        toast.info("17-minute rest complete. Resuming deep work flow.");
      }
    } else {
      toast.success("Study session timer target reached!");
    }
  };

  // Start Session
  const handleStartSession = async () => {
    if (!isCalibrated) {
      toast.warning("Mandatory Posture Calibration: Please complete Step 1 (GOOD POSTURE FRAME) and Step 2 (BAD POSTURE FRAME) in the Camera HUD before starting the study session.");
      return;
    }

    setLoading(true);
    try {
      // Reset live vision telemetry for clean session tracking
      try {
        await apiRequest("/vision/reset-session-events", { method: "POST" });
      } catch (e) {
        // Continue even if reset endpoint is quiet
      }

      const metadata = {
        studyMethod,
        workDurationMins,
        breakDurationMins,
        totalCycles,
        isCustom: studyMethod === "Custom",
      };

      const res = await apiRequest("/sessions/start", {
        method: "POST",
        body: JSON.stringify({
          subject_id: subjectId ? parseInt(subjectId) : null,
          topic_name: topicName.trim() || `${studyMethod} Session`,
          study_method: studyMethod,
          method_metadata: metadata,
        }),
      });

      setActiveSessionId(res.id);
      setSessionActive(true);
      setIsPaused(false);
      setSessionReport(null);
      setCurrentCycle(1);

      // Initialize wall-clock tracking
      totalActiveElapsedMsRef.current = 0;
      lastActiveResumeTimeRef.current = Date.now();
      timerStartTimeRef.current = Date.now();
      initialSecondsRemainingRef.current = secondsRemaining;

      setSessionMetrics({
        postureWarnings: 0,
        badPostureEvents: 0,
        placeAbsenceEvents: 0,
        phoneUseEvents: 0,
      });
      toast.success(`Active ${studyMethod} session initiated. Camera monitoring & IoT hardware synced.`);
    } catch (err) {
      toast.error(err.message || "Failed starting study session.");
    } finally {
      setLoading(false);
    }
  };

  // Pause / Resume Session (Drift-Free Active Time Tracking)
  const handleTogglePause = async () => {
    if (!activeSessionId) return;
    try {
      const now = Date.now();
      if (!isPaused) {
        await apiRequest(`/sessions/${activeSessionId}/pause`, { method: "POST" });
        if (lastActiveResumeTimeRef.current) {
          totalActiveElapsedMsRef.current += (now - lastActiveResumeTimeRef.current);
        }
        setIsPaused(true);
        toast.info("Session paused.");
      } else {
        await apiRequest(`/sessions/${activeSessionId}/resume`, { method: "POST" });
        lastActiveResumeTimeRef.current = now;
        timerStartTimeRef.current = now;
        initialSecondsRemainingRef.current = secondsRemaining;
        setIsPaused(false);
        toast.info("Session resumed.");
      }
    } catch (err) {
      toast.error("Failed toggling session pause state.");
    }
  };

  // Transition to Manual Break
  const handleTakeBreak = async () => {
    try {
      if (timerMode === "work") {
        setTimerMode("break");
        setSecondsRemaining(breakDurationMins * 60);
        if (activeSessionId) {
          await apiRequest(`/sessions/${activeSessionId}/break?break_duration_mins=${breakDurationMins}`, { method: "POST" });
        }
        toast.info(`Switched to restorative break (${breakDurationMins}m). ESP32 display set to calming break animation.`);
      } else {
        setTimerMode("work");
        setSecondsRemaining(workDurationMins * 60);
        if (activeSessionId) {
          await apiRequest(`/sessions/${activeSessionId}/break-end?work_duration_mins=${workDurationMins}`, { method: "POST" });
        }
        toast.info("Switched back to focus sprint. Hardware set to green flow state.");
      }
    } catch (err) {
      console.warn("Could not synchronize break state with backend:", err);
    }
  };

  // End / Finalize Session
  const handleConfirmEndSession = async () => {
    if (!activeSessionId) return;
    setShowEndModal(false);
    try {
      // Pull verified vision telemetry from backend
      let visionSummary = null;
      try {
        visionSummary = await apiRequest("/vision/session-summary");
      } catch (e) {
        console.warn("Could not fetch vision summary:", e);
      }

      // Calculate actual elapsed study time excluding paused intervals
      const now = Date.now();
      const currentActiveMs = totalActiveElapsedMsRef.current + (
        (!isPaused && lastActiveResumeTimeRef.current) ? (now - lastActiveResumeTimeRef.current) : 0
      );
      const computedDurationMinutes = Math.max(0.1, Number((currentActiveMs / (1000 * 60)).toFixed(2)));

      const finalMetadata = {
        studyMethod,
        cycles_completed: currentCycle,
        work_duration_mins: workDurationMins,
        break_duration_mins: breakDurationMins,
        posture_warnings_count: sessionMetrics.postureWarnings,
        bad_posture_events_count: visionSummary?.confirmed_bad_alerts ?? sessionMetrics.badPostureEvents,
        bad_posture_seconds: visionSummary?.bad_posture_seconds ?? 0,
        place_absence_count: visionSummary?.absence_events_count ?? sessionMetrics.placeAbsenceEvents,
        absence_history: visionSummary?.absence_history ?? [],
        phone_use_count: visionSummary?.phone_events_count ?? sessionMetrics.phoneUseEvents,
        phone_history: visionSummary?.phone_history ?? [],
        active_recall_data: studyMethod === "Active Recall" ? recallPrompts : null,
        feynman_notes:
          studyMethod === "Feynman Technique"
            ? {
                explanation: feynmanExplanation,
                gaps: feynmanGaps,
                revision: feynmanRevision,
                analogy: feynmanAnalogy,
              }
            : null,
      };

      const res = await apiRequest(`/sessions/${activeSessionId}/end`, {
        method: "POST",
        body: JSON.stringify({
          duration_minutes: computedDurationMinutes,
          method_metadata: finalMetadata,
          notes: sessionNotes.trim() || null,
        }),
      });

      setSessionReport({
        ...res,
        liveMetrics: sessionMetrics,
        visionSummary: visionSummary,
      });
      setSessionActive(false);
      setActiveSessionId(null);
      setIsPaused(false);
      toast.success("Study session finalized & performance report generated!");
      loadInitialData();
    } catch (err) {
      toast.error("Error finalizing study session.");
    }
  };

  // Cancel / Abandon Session
  const handleCancelSession = async () => {
    if (!activeSessionId) return;
    try {
      await apiRequest(`/sessions/${activeSessionId}/cancel`, { method: "POST" });
      setSessionActive(false);
      setActiveSessionId(null);
      setIsPaused(false);
      toast.warning("Study session discarded.");
      loadInitialData();
    } catch (err) {
      toast.error("Failed cancelling session.");
    }
  };

  // Spaced Repetition Review Handler
  const handleReviewSrCard = async (rating) => {
    const currentCard = srCards[currentSrIdx];
    if (!currentCard) return;

    try {
      await apiRequest(`/sessions/spaced-repetition/cards/${currentCard.id}/review`, {
        method: "POST",
        body: JSON.stringify({ quality_rating: rating }),
      });
      setShowSrAnswer(false);
      if (currentSrIdx + 1 < srCards.length) {
        setCurrentSrIdx(currentSrIdx + 1);
      } else {
        toast.success("All due review cards completed for this deck!");
      }
      loadInitialData();
    } catch (err) {
      toast.error("Failed recording card review.");
    }
  };

  // Active Recall Handlers
  const handleAddCustomPrompt = (e) => {
    e.preventDefault();
    if (!customPromptInput.trim()) return;
    setRecallPrompts([
      ...recallPrompts,
      { prompt: customPromptInput.trim(), answer: customAnswerInput.trim() || "Self-evaluate notes", recalled: null },
    ]);
    setCustomPromptInput("");
    setCustomAnswerInput("");
    toast.success("Self-testing prompt added to recall deck.");
  };

  const handleRateRecall = (status) => {
    const updated = [...recallPrompts];
    updated[currentRecallIdx].recalled = status;
    setRecallPrompts(updated);
    setShowRecallAnswer(false);
    if (currentRecallIdx + 1 < recallPrompts.length) {
      setCurrentRecallIdx(currentRecallIdx + 1);
    }
  };

  const formatTime = (totalSecs) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Live Study Session Engine
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Real-time vision tracking, local posture ergonomics, corner timer, and wireless ESP32 IoT telemetry.
          </p>
        </div>

        {sessionActive && (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <Button
              variant="outline"
              icon={isPaused ? Play : Pause}
              onClick={handleTogglePause}
            >
              {isPaused ? "Resume Session" : "Pause Session"}
            </Button>
            <Button
              variant="outline"
              icon={Coffee}
              onClick={handleTakeBreak}
            >
              {timerMode === "work" ? "Take Break" : "Resume Work"}
            </Button>
            <Button
              variant="primary"
              icon={Square}
              onClick={() => setShowEndModal(true)}
            >
              End Session
            </Button>
            <Button
              variant="ghost"
              icon={XCircle}
              style={{ color: "var(--color-terracotta)" }}
              onClick={handleCancelSession}
            >
              Discard
            </Button>
          </div>
        )}
      </div>

      {/* Today's Academic Checklist & Topic Selection */}
      {!sessionActive && (
        <Card
          title="Today's Study Checklist & Topic Selection"
          subtitle={`Synchronized with real-world calendar (${new Date().toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}). Pick a scheduled topic to load it directly into your live study session.`}
          icon={BookOpen}
        >
          {todayTasks.length === 0 ? (
            <div
              style={{
                padding: "1rem 1.25rem",
                borderRadius: "8px",
                backgroundColor: "var(--bg-app)",
                border: "1px dashed var(--border-color)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                flexWrap: "wrap",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <Clock size={20} color="var(--color-wood)" />
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-main)" }}>
                    No planned tasks specifically assigned for today's date
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    You can pick any subject and enter a custom study topic below, or visit AI Study Coach to generate a full semester plan.
                  </div>
                </div>
              </div>
              {setActivePage && (
                <Button
                  variant="outline"
                  size="sm"
                  icon={ArrowRight}
                  onClick={() => setActivePage("planner")}
                >
                  Open AI Planner
                </Button>
              )}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
                  gap: "0.75rem",
                }}
              >
                {todayTasks.map((t) => {
                  const isSelected = selectedTaskId === t.id || topicName === t.title;
                  return (
                    <div
                      key={t.id}
                      style={{
                        padding: "0.85rem 1rem",
                        borderRadius: "8px",
                        backgroundColor: isSelected ? "var(--bg-card)" : "var(--bg-app)",
                        border: isSelected
                          ? "2px solid var(--color-sage)"
                          : "1px solid var(--border-color)",
                        boxShadow: isSelected ? "0 2px 8px rgba(106, 126, 99, 0.15)" : "none",
                        display: "flex",
                        flexDirection: "column",
                        gap: "0.5rem",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <span
                            style={{
                              width: "10px",
                              height: "10px",
                              borderRadius: "50%",
                              backgroundColor: t.subject_color || "var(--color-wood)",
                              display: "inline-block",
                              flexShrink: 0,
                            }}
                          />
                          <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                            {t.subject_name || "Course Subject"}
                          </span>
                        </div>
                        <Badge variant={t.is_completed ? "good" : "neutral"} style={{ fontSize: "0.75rem" }}>
                          {t.is_completed ? "Completed" : `${t.estimated_minutes || 30} mins`}
                        </Badge>
                      </div>

                      <div
                        style={{
                          fontSize: "0.92rem",
                          fontWeight: 600,
                          color: "var(--text-main)",
                          textDecoration: t.is_completed ? "line-through" : "none",
                          opacity: t.is_completed ? 0.7 : 1,
                        }}
                      >
                        {t.title}
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.25rem", gap: "0.5rem" }}>
                        <button
                          type="button"
                          onClick={() => handleToggleTodayTask(t.id)}
                          style={{
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "0.35rem",
                            fontSize: "0.8rem",
                            color: t.is_completed ? "var(--color-sage)" : "var(--text-muted)",
                            padding: 0,
                          }}
                        >
                          <CheckCircle2 size={15} color={t.is_completed ? "var(--color-sage)" : "var(--text-muted)"} />
                          <span>{t.is_completed ? "Completed" : "Mark done"}</span>
                        </button>

                        <Button
                          variant={isSelected ? "primary" : "outline"}
                          size="sm"
                          icon={isSelected ? CheckCircle2 : ArrowRight}
                          onClick={() => handleSelectTodayTask(t)}
                        >
                          {isSelected ? "Selected" : "Select Topic"}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Pre-Session Setup Deck (When idle) */}
      {!sessionActive && (
        <Card
          title="Configure Live Study Session"
          subtitle="Select course subject, topic, and choose among the 5 science-backed study frameworks or customize your own."
          icon={SlidersHorizontal}
        >
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
            <div className="form-group">
              <label className="form-label">Course / Subject *</label>
              <select
                className="form-select"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
              >
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} {s.code ? `(${s.code})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Specific Study Topic</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Dynamic Programming, AVL Rotations, Operating Systems"
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Study Method</label>
              <select
                className="form-select"
                value={studyMethod}
                onChange={(e) => {
                  setStudyMethod(e.target.value);
                  applyDefaultTimerForMethod(e.target.value);
                }}
              >
                <option value="Pomodoro">1. Pomodoro (25m Focus + 5m Break)</option>
                <option value="52/17">2. 52/17 Deep Work (52m Work + 17m Break)</option>
                <option value="Active Recall">3. Active Recall (Closed-Book Retrieval)</option>
                <option value="Spaced Repetition">4. Spaced Repetition (SM-2 Adaptive)</option>
                <option value="Feynman Technique">5. Feynman Technique (Simple Analogy)</option>
                <option value="Custom">6. Custom Session (User Configured)</option>
              </select>
            </div>
          </div>

          {/* Method-Specific / Custom Duration Configuration */}
          {(studyMethod === "Pomodoro" || studyMethod === "Custom") && (
            <div
              style={{
                backgroundColor: "var(--bg-app)",
                padding: "0.85rem 1rem",
                borderRadius: "6px",
                border: "1px solid var(--border-color)",
                marginBottom: "1.25rem",
                display: "flex",
                gap: "1.25rem",
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-main)" }}>
                {studyMethod === "Custom" ? "Custom Session Durations:" : "Pomodoro Interval Settings:"}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
                <span>Focus Sprint:</span>
                <input
                  type="number"
                  min="5"
                  max="120"
                  className="form-input"
                  style={{ width: "70px", padding: "0.25rem 0.5rem" }}
                  value={workDurationMins}
                  onChange={(e) => {
                    const v = parseInt(e.target.value) || 25;
                    setWorkDurationMins(v);
                    setSecondsRemaining(v * 60);
                  }}
                />
                <span>mins</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
                <span>Rest Break:</span>
                <input
                  type="number"
                  min="1"
                  max="45"
                  className="form-input"
                  style={{ width: "70px", padding: "0.25rem 0.5rem" }}
                  value={breakDurationMins}
                  onChange={(e) => setBreakDurationMins(parseInt(e.target.value) || 5)}
                />
                <span>mins</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
                <span>Target Cycles:</span>
                <input
                  type="number"
                  min="1"
                  max="12"
                  className="form-input"
                  style={{ width: "60px", padding: "0.25rem 0.5rem" }}
                  value={totalCycles}
                  onChange={(e) => setTotalCycles(parseInt(e.target.value) || 4)}
                />
              </div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
              <ShieldCheck size={16} color={isCalibrated ? "var(--color-sage)" : "var(--color-wood)"} />
              <span>{isCalibrated ? "✓ Posture calibrated with dual reference frames" : "⚠ Complete sequential calibration below before starting"}</span>
            </div>
            <Button
              variant={isCalibrated ? "primary" : "outline"}
              size="lg"
              icon={Play}
              onClick={handleStartSession}
              loading={loading}
              style={!isCalibrated ? { borderColor: "var(--color-wood)", color: "var(--color-wood)" } : {}}
            >
              {isCalibrated ? `Start Live ${studyMethod} Session` : `Calibrate Posture Below to Start`}
            </Button>
          </div>
        </Card>
      )}

      {/* Main 2-Column Live Session Area */}
      <div className="grid-cols-2">
        {/* Left Column: Live Webcam HUD & Corner Floating Timer */}
        <LaptopCameraHUD
          sessionId={activeSessionId}
          sessionActive={sessionActive}
          timerFormatted={formatTime(secondsRemaining)}
          timerMode={timerMode}
          studyMethod={studyMethod}
          onMetricsUpdate={(newMetrics) => setSessionMetrics(newMetrics)}
          onCalibrationComplete={() => setIsCalibrated(true)}
        />

        {/* Right Column: Master Focus Deck & IoT Hardware Status */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Master Big Timer & State Display */}
          <Card style={{ textAlign: "center", padding: "1.75rem 1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
              <Badge variant={timerMode === "work" ? "good" : "warning"} style={{ fontSize: "0.85rem", padding: "0.35rem 0.9rem" }}>
                {studyMethod} &bull; {timerMode === "work" ? "FOCUS SPRINT" : timerMode === "break" ? "SHORT REST" : "LONG REST"}
              </Badge>
              {(studyMethod === "Pomodoro" || studyMethod === "Custom") && sessionActive && (
                <Badge variant="neutral">Cycle {currentCycle} of {totalCycles}</Badge>
              )}
            </div>

            <div
              style={{
                fontSize: "4.5rem",
                fontWeight: 800,
                fontFamily: "monospace",
                color: timerMode === "work" ? "var(--text-main)" : "var(--color-terracotta)",
                letterSpacing: "-0.04em",
                margin: "0.25rem 0 0.75rem 0",
                lineHeight: 1,
              }}
            >
              {formatTime(secondsRemaining)}
            </div>

            <div style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
              <strong>{topicName || "Academic Study"}</strong> &bull; {subjects.find((s) => String(s.id) === String(subjectId))?.name || "Course Subject"}
            </div>

            {sessionActive && (
              <div style={{ display: "flex", justifyContent: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                <Button
                  variant="outline"
                  size="sm"
                  icon={isPaused ? Play : Pause}
                  onClick={handleTogglePause}
                >
                  {isPaused ? "Resume" : "Pause"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={Coffee}
                  onClick={handleTakeBreak}
                >
                  {timerMode === "work" ? "Take Break" : "Resume Sprint"}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  icon={Square}
                  onClick={() => setShowEndModal(true)}
                >
                  End Session
                </Button>
              </div>
            )}
          </Card>

          {/* Wireless ESP32 IoT Module & Focus Audio */}
          <Card
            title="ESP32 IoT Physical Hardware"
            subtitle="Wireless ESP32 drives physical Traffic Light module & OLED face expressions in real-time."
            icon={Eye}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "1.25rem",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-color)",
                padding: "0.9rem 1rem",
                borderRadius: "6px",
                marginBottom: "0.75rem",
              }}
            >
              <div
                style={{
                  width: "50px",
                  height: "50px",
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.5rem",
                  fontWeight: 800,
                  backgroundColor:
                    currentLed === "RED"
                      ? "var(--status-bad-bg)"
                      : currentLed === "YELLOW"
                      ? "var(--status-buffer-bg)"
                      : "var(--status-good-bg)",
                  color:
                    currentLed === "RED"
                      ? "var(--status-bad-text)"
                      : currentLed === "YELLOW"
                      ? "var(--status-buffer-text)"
                      : "var(--status-good-text)",
                  border: `1px solid currentColor`,
                }}
              >
                {currentPosture === "good" ? "^_^" : currentPosture === "buffer" ? "-_-" : ">_<"}
              </div>

              <div>
                <div style={{ fontSize: "1rem", fontWeight: 700, textTransform: "uppercase" }}>
                  Hardware LED: {currentLed} &bull; {currentPosture}
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  OLED Animation: <strong>{hardwareState?.oled_animation || "good_posture"}</strong> &bull; Message: <strong>{hardwareState?.message || "FOCUSED"}</strong>
                </div>
              </div>
            </div>

            {/* Focus Audio Ambience */}
            <div>
              <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.35rem" }}>
                Ambient Focus Audio:
              </div>
              <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                {["Off", "White Noise", "Rainfall", "Lo-Fi Beats", "Cafe Library"].map((aud) => (
                  <Button
                    key={aud}
                    size="sm"
                    variant={audioMode === aud ? "primary" : "outline"}
                    onClick={() => {
                      setAudioMode(aud);
                      toast.info(`Ambient audio: ${aud}`);
                    }}
                  >
                    {aud}
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* ==================================================== */}
      {/* METHOD-SPECIFIC INTERACTIVE MODULE (WHEN SESSION ACTIVE) */}
      {/* ==================================================== */}
      {sessionActive && (
        <Card
          title={`${studyMethod} Interactive Canvas`}
          subtitle="Real-time methodology workflow designed for maximum active learning."
          icon={Sparkles}
          style={{ border: "2px solid var(--color-sage)" }}
        >
          {/* 1. ACTIVE RECALL WORKFLOW */}
          {studyMethod === "Active Recall" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                  Recall Prompt #{currentRecallIdx + 1} of {recallPrompts.length}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Recalled: {recallPrompts.filter((p) => p.recalled === "accurate").length} / {recallPrompts.length}
                </span>
              </div>

              {recallPrompts[currentRecallIdx] && (
                <div style={{ backgroundColor: "var(--bg-app)", padding: "1.25rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
                    Q: {recallPrompts[currentRecallIdx].prompt}
                  </div>

                  {!showRecallAnswer ? (
                    <Button variant="outline" size="sm" onClick={() => setShowRecallAnswer(true)}>
                      Reveal Benchmark Answer
                    </Button>
                  ) : (
                    <div>
                      <div
                        style={{
                          backgroundColor: "var(--bg-surface)",
                          padding: "0.85rem",
                          borderRadius: "4px",
                          borderLeft: "4px solid var(--color-sage)",
                          fontSize: "0.9rem",
                          marginBottom: "1rem",
                          lineHeight: 1.5,
                        }}
                      >
                        <strong>Target Key Points:</strong> {recallPrompts[currentRecallIdx].answer}
                      </div>

                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>How accurate was your recall?</span>
                        <Button size="sm" variant="primary" onClick={() => handleRateRecall("accurate")}>
                          ✓ Accurate
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleRateRecall("partial")}>
                          ~ Partial
                        </Button>
                        <Button size="sm" variant="ghost" style={{ color: "var(--color-terracotta)" }} onClick={() => handleRateRecall("missed")}>
                          ✗ Missed
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Add Custom Prompt Form */}
              <form onSubmit={handleAddCustomPrompt} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <input
                  type="text"
                  className="form-input"
                  style={{ flex: 1.5, minWidth: "200px" }}
                  placeholder="Add custom question prompt..."
                  value={customPromptInput}
                  onChange={(e) => setCustomPromptInput(e.target.value)}
                />
                <input
                  type="text"
                  className="form-input"
                  style={{ flex: 1, minWidth: "160px" }}
                  placeholder="Key answer points (optional)..."
                  value={customAnswerInput}
                  onChange={(e) => setCustomAnswerInput(e.target.value)}
                />
                <Button variant="outline" size="sm" type="submit">
                  + Add Question
                </Button>
              </form>
            </div>
          )}

          {/* 2. SPACED REPETITION (SM-2) WORKFLOW */}
          {studyMethod === "Spaced Repetition" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                SuperMemo-2 (SM-2) Engine: Rate your recall difficulty (0–5) to compute your next review interval mathematically.
              </p>

              {srCards.length === 0 ? (
                <div style={{ padding: "1.5rem", textAlign: "center", backgroundColor: "var(--bg-app)", borderRadius: "6px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  No flashcards created yet for this subject. Create cards in Academics or add below to start SM-2 scheduling.
                </div>
              ) : srCards[currentSrIdx] ? (
                <div style={{ backgroundColor: "var(--bg-app)", padding: "1.25rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    <span>Card #{currentSrIdx + 1} of {srCards.length}</span>
                    <span>Ease Factor: <strong>{srCards[currentSrIdx].ease_factor}</strong> &bull; Repetitions: <strong>{srCards[currentSrIdx].repetitions_count}</strong></span>
                  </div>

                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
                    {srCards[currentSrIdx].front_prompt}
                  </div>

                  {!showSrAnswer ? (
                    <Button variant="outline" size="sm" onClick={() => setShowSrAnswer(true)}>
                      Flip Card / Show Answer
                    </Button>
                  ) : (
                    <div>
                      <div
                        style={{
                          backgroundColor: "var(--bg-surface)",
                          padding: "0.85rem",
                          borderRadius: "4px",
                          borderLeft: "4px solid var(--color-sage)",
                          fontSize: "0.9rem",
                          marginBottom: "1rem",
                        }}
                      >
                        {srCards[currentSrIdx].back_answer}
                      </div>

                      <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem", color: "var(--text-muted)" }}>
                        Rate Recall Quality (SM-2 Grade):
                      </div>
                      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                        <Button size="sm" variant="outline" style={{ color: "var(--color-terracotta)" }} onClick={() => handleReviewSrCard(0)}>
                          0: Blackout
                        </Button>
                        <Button size="sm" variant="outline" style={{ color: "var(--color-terracotta)" }} onClick={() => handleReviewSrCard(1)}>
                          1: Incorrect
                        </Button>
                        <Button size="sm" variant="outline" style={{ color: "var(--color-sand)" }} onClick={() => handleReviewSrCard(2)}>
                          2: Remembered
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleReviewSrCard(3)}>
                          3: Hard Recall
                        </Button>
                        <Button size="sm" variant="primary" onClick={() => handleReviewSrCard(4)}>
                          4: Good Recall
                        </Button>
                        <Button size="sm" variant="primary" style={{ backgroundColor: "var(--color-sage)" }} onClick={() => handleReviewSrCard(5)}>
                          5: Perfect Recall
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: "1rem", textAlign: "center", color: "var(--color-sage)", fontWeight: 600 }}>
                  ✓ All spaced repetition cards reviewed for this session!
                </div>
              )}
            </div>
          )}

          {/* 3. FEYNMAN TECHNIQUE 4-STAGE CANVAS */}
          {studyMethod === "Feynman Technique" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Stepper Tabs */}
              <div style={{ display: "flex", gap: "0.4rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "0.5rem" }}>
                {[
                  { step: 1, label: "1. Explain Simply" },
                  { step: 2, label: "2. Identify Gaps & Jargon" },
                  { step: 3, label: "3. Revise with Notes" },
                  { step: 4, label: "4. Teach with Analogy" },
                ].map((s) => (
                  <button
                    key={s.step}
                    onClick={() => setFeynmanStage(s.step)}
                    style={{
                      padding: "0.4rem 0.8rem",
                      borderRadius: "4px",
                      border: "none",
                      fontSize: "0.85rem",
                      fontWeight: feynmanStage === s.step ? 700 : 500,
                      backgroundColor: feynmanStage === s.step ? "var(--color-sage)" : "transparent",
                      color: feynmanStage === s.step ? "#FFFFFF" : "var(--text-muted)",
                      cursor: "pointer",
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              {feynmanStage === 1 && (
                <div>
                  <label className="form-label">
                    Stage 1: Explain {topicName || "the concept"} in plain English without jargon (as if teaching a 10-year-old child):
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="Write your simplified explanation here..."
                    value={feynmanExplanation}
                    onChange={(e) => setFeynmanExplanation(e.target.value)}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                    <Button size="sm" variant="primary" onClick={() => setFeynmanStage(2)}>
                      Next: Identify Gaps &rarr;
                    </Button>
                  </div>
                </div>
              )}

              {feynmanStage === 2 && (
                <div>
                  <label className="form-label">
                    Stage 2: Pinpoint terms you struggled to explain, vague reasoning, or heavy academic jargon:
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="e.g. I couldn't explain why the balance factor is calculated as height(left) - height(right)..."
                    value={feynmanGaps}
                    onChange={(e) => setFeynmanGaps(e.target.value)}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                    <Button size="sm" variant="primary" onClick={() => setFeynmanStage(3)}>
                      Next: Revise & Research &rarr;
                    </Button>
                  </div>
                </div>
              )}

              {feynmanStage === 3 && (
                <div>
                  <label className="form-label">
                    Stage 3: Review reference textbook/lecture notes to bridge the identified gaps:
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="Summarize the textbook definition and correct logic..."
                    value={feynmanRevision}
                    onChange={(e) => setFeynmanRevision(e.target.value)}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                    <Button size="sm" variant="primary" onClick={() => setFeynmanStage(4)}>
                      Next: Synthesize Analogy &rarr;
                    </Button>
                  </div>
                </div>
              )}

              {feynmanStage === 4 && (
                <div>
                  <label className="form-label">
                    Stage 4: Synthesize a real-world analogy to solidify foundational intuition:
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="e.g. Think of a Binary Search Tree like a physical phonebook index where..."
                    value={feynmanAnalogy}
                    onChange={(e) => setFeynmanAnalogy(e.target.value)}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                    <Badge variant="good">Feynman Mastery Complete</Badge>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 4. POMODORO / 52-17 / CUSTOM FOCUS NOTES */}
          {(studyMethod === "Pomodoro" || studyMethod === "52/17" || studyMethod === "Custom") && (
            <div>
              <label className="form-label">Session Focus Notes & Deliverables Completed</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Log problem sets completed, formulas derived, or key breakthroughs..."
                value={sessionNotes}
                onChange={(e) => setSessionNotes(e.target.value)}
              />
            </div>
          )}
        </Card>
      )}

      {/* Post-Session Performance Report */}
      {sessionReport && (
        <Card
          title="Session Performance & Ergonomics Report"
          subtitle="Summary metrics recorded for Study Health Score calculations."
          icon={Award}
          style={{ border: "1px solid var(--status-good-border)", backgroundColor: "var(--status-good-bg)" }}
        >
          <div className="grid-cols-4" style={{ marginBottom: "1rem" }}>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Duration</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{sessionReport.duration_minutes} Mins</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Focus Quality</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-sage)" }}>
                {sessionReport.metric?.focus_score ?? 100}%
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Posture Score</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-wood)" }}>
                {sessionReport.metric?.posture_score ?? 100}%
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Productivity</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-terracotta)" }}>
                {sessionReport.metric?.productivity_score ?? 85}/100
              </div>
            </div>
          </div>

          {/* Detailed Event Counters in Report */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.6rem", marginBottom: "1rem" }}>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.7rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Posture Warnings</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                {sessionReport.liveMetrics?.postureWarnings ?? 0}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.7rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Bad Posture Events</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--color-terracotta)" }}>
                {sessionReport.visionSummary?.confirmed_bad_alerts ?? sessionReport.liveMetrics?.badPostureEvents ?? sessionReport.metric?.posture_alerts_count ?? 0}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
                {sessionReport.visionSummary?.bad_posture_seconds ? `${sessionReport.visionSummary.bad_posture_seconds}s in bad posture` : ""}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.7rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Desk Absences</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                {sessionReport.visionSummary?.absence_events_count ?? sessionReport.liveMetrics?.placeAbsenceEvents ?? 0}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
                {sessionReport.visionSummary?.absence_history?.length > 0 ? `${sessionReport.visionSummary.absence_history.length} logged departures` : "Continuous Presence"}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.7rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Phone-Use Detected</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--color-terracotta)" }}>
                {sessionReport.visionSummary?.phone_events_count ?? sessionReport.liveMetrics?.phoneUseEvents ?? 0}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
                {sessionReport.visionSummary?.phone_events_count > 0 ? "Elevated phone distraction" : "Zero phone distractions"}
              </div>
            </div>
          </div>

          {/* Recorded Desk Absence & Departure Log with Timestamps & Durations */}
          <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.85rem 1rem", borderRadius: "6px", border: "1px solid var(--border-color)", marginBottom: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-main)", textTransform: "uppercase" }}>
                Recorded Desk Absence & Departure Log:
              </div>
              <Badge variant={sessionReport.visionSummary?.absence_history?.length > 0 ? "bad" : "good"}>
                {sessionReport.visionSummary?.absence_history?.length > 0
                  ? `${sessionReport.visionSummary.absence_history.length} Departures (${sessionReport.visionSummary?.total_absence_seconds || 0}s Total Away)`
                  : "✓ Continuous Attendance"}
              </Badge>
            </div>

            {sessionReport.visionSummary?.absence_history && sessionReport.visionSummary.absence_history.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.74rem", textTransform: "uppercase" }}>
                      <th style={{ padding: "0.4rem 0.5rem" }}>#</th>
                      <th style={{ padding: "0.4rem 0.5rem" }}>Left Desk At</th>
                      <th style={{ padding: "0.4rem 0.5rem" }}>Returned At</th>
                      <th style={{ padding: "0.4rem 0.5rem" }}>Duration Away</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessionReport.visionSummary.absence_history.map((abs, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td style={{ padding: "0.4rem 0.5rem", fontWeight: 600 }}>Departure #{idx + 1}</td>
                        <td style={{ padding: "0.4rem 0.5rem" }}>{abs.left_at}</td>
                        <td style={{ padding: "0.4rem 0.5rem" }}>{abs.returned_at}</td>
                        <td style={{ padding: "0.4rem 0.5rem", fontWeight: 700, color: "var(--color-terracotta)" }}>
                          {abs.duration_formatted || `${abs.duration_seconds}s`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ fontSize: "0.82rem", color: "var(--color-sage)", margin: 0 }}>
                ✓ Zero departures during focus work. The student remained continuously seated at the study desk throughout the session!
              </p>
            )}
          </div>

          {/* Recorded Phone Distractions with Timestamps */}
          {sessionReport.visionSummary?.phone_history && sessionReport.visionSummary.phone_history.length > 0 && (
            <div style={{ backgroundColor: "var(--bg-surface)", padding: "0.85rem 1rem", borderRadius: "6px", border: "1px solid var(--border-color)", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-main)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                Recorded Phone Distractions ({sessionReport.visionSummary.phone_history.length} Events):
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {sessionReport.visionSummary.phone_history.map((ph, idx) => (
                  <Badge key={idx} variant="warning">
                    📱 Detection #{idx + 1}: {ph.detected_at || "Flagged"}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <p style={{ fontSize: "0.88rem", color: "var(--text-main)", lineHeight: 1.5, margin: 0 }}>
            {sessionReport.metric?.ai_feedback_summary || "Excellent study session recorded. Focus and posture telemetry have been synced to your Study Health Score."}
          </p>
        </Card>
      )}

      {/* Session History Deck */}
      <Card title="Recent Study Sessions History" subtitle="Chronological session logs and method effectiveness." icon={Clock}>
        {recentSessions.length === 0 ? (
          <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.88rem" }}>
            No study sessions recorded yet. Start your first session above!
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Method</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Subject & Topic</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Duration</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Date</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Status</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Focus / Posture</th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.map((s) => (
                  <tr key={s.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.6rem 0.5rem", fontWeight: 600 }}>{s.study_method}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>
                      <span style={{ fontWeight: 600 }}>{s.topic_name || "General Study"}</span>
                      {s.subject_name && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{s.subject_name}</div>
                      )}
                    </td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>{s.duration_minutes} mins</td>
                    <td style={{ padding: "0.6rem 0.5rem", color: "var(--text-muted)" }}>
                      {new Date(s.start_time).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>
                      <Badge variant={s.status === "completed" ? "good" : s.status === "active" ? "warning" : "neutral"}>
                        {s.status}
                      </Badge>
                    </td>
                    <td style={{ padding: "0.6rem 0.5rem", fontSize: "0.82rem" }}>
                      {s.metric ? (
                        <span>Focus: <strong>{s.metric.focus_score}%</strong> &bull; Posture: <strong>{s.metric.posture_score}%</strong></span>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Confirmation Modal Before Ending Session */}
      <Modal
        isOpen={showEndModal}
        onClose={() => setShowEndModal(false)}
        title="Complete Study Session"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ fontSize: "0.9rem", color: "var(--text-main)", lineHeight: 1.5, margin: 0 }}>
            Are you ready to finalize your <strong>{studyMethod}</strong> study session on <em>"{topicName || "General Study"}"</em>?
          </p>

          <div className="form-group">
            <label className="form-label">Key Breakthroughs / Session Notes (Optional)</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="e.g. Mastered BST deletion edge cases, solved 3 recursion tree problems..."
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
            <Button variant="outline" onClick={() => setShowEndModal(false)}>
              Keep Studying
            </Button>
            <Button variant="primary" icon={CheckCircle2} onClick={handleConfirmEndSession}>
              Complete & Generate Report
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
