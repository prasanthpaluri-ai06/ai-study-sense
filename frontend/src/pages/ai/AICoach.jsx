import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, ProgressBar, EmptyState } from "../../components/common/Badge";
import { Modal } from "../../components/common/Modal";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Calendar,
  Clock,
  Sparkles,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Plus,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Edit3,
  Trash2,
  Filter,
  Layers,
  Flag,
  PlayCircle,
  GraduationCap,
  CheckSquare,
  Square,
  AlertCircle,
  List,
  Grid,
  Columns,
  CalendarDays,
  Target,
  ArrowRight,
} from "lucide-react";
import { getTodayDateString, formatDate, formatDateTime } from "../../utils/dateUtils";

export default function AICoach({ setActivePage, setSelectedSessionData }) {
  const toast = useToast();

  // Overview Data
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  // Selected Subject Filter (null = Master Calendar, number = specific subject calendar)
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);

  // Calendar View & Navigation
  const [calendarView, setCalendarView] = useState("month"); // 'month' | 'week' | 'agenda'
  const [currentDate, setCurrentDate] = useState(new Date());

  // Schedule Feed
  const [scheduleData, setScheduleData] = useState({ tasks: [], blackout_dates: [], assignments: [] });
  const [loadingSchedule, setLoadingSchedule] = useState(false);

  // Modals
  const [showSemesterModal, setShowSemesterModal] = useState(false);
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [showBlackoutModal, setShowBlackoutModal] = useState(false);
  const [showRebalanceModal, setShowRebalanceModal] = useState(false);
  const [rebalancePreview, setRebalancePreview] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  // Semester Form State
  const [semesterForm, setSemesterForm] = useState({
    start_date: getTodayDateString(),
    end_date: getTodayDateString(new Date(Date.now() + 90 * 24 * 60 * 60 * 1000)),
    study_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    max_daily_tasks: 3,
    target_study_hours_daily: 3.0,
  });

  // Task Form State
  const [taskForm, setTaskForm] = useState({
    title: "",
    subject_id: "",
    scheduled_date: getTodayDateString(),
    task_type: "learning",
    priority: "Medium",
    estimated_minutes: 45,
    notes: "",
  });

  // Blackout Date Form State
  const [blackoutForm, setBlackoutForm] = useState({
    date: getTodayDateString(),
    reason: "",
    blackout_type: "holiday",
  });

  // Initial Load
  useEffect(() => {
    loadOverview();
  }, []);

  // Reload Schedule on Subject Filter or Date Change
  useEffect(() => {
    if (overview?.is_configured) {
      loadSchedule();
    }
  }, [selectedSubjectId, currentDate, overview?.is_configured]);

  const loadOverview = async () => {
    setLoading(true);
    try {
      const data = await apiRequest("/planner/overview");
      setOverview(data);
      if (data?.semester) {
        setSemesterForm({
          start_date: data.semester.start_date,
          end_date: data.semester.end_date,
          study_days: data.semester.study_days || ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
          max_daily_tasks: data.semester.max_daily_tasks || 3,
          target_study_hours_daily: data.semester.target_study_hours_daily || 3.0,
        });
      }
    } catch (err) {
      console.error("Error loading planner overview:", err);
      toast.error("Failed to load planner overview.");
    } finally {
      setLoading(false);
    }
  };

  const loadSchedule = async () => {
    setLoadingSchedule(true);
    try {
      const startOfYear = getTodayDateString(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
      const endOfYear = getTodayDateString(new Date(currentDate.getFullYear(), currentDate.getMonth() + 2, 0));

      let url = `/planner/schedule?start_date=${startOfYear}&end_date=${endOfYear}`;
      if (selectedSubjectId) {
        url += `&subject_id=${selectedSubjectId}`;
      }

      const res = await apiRequest(url);
      setScheduleData(res);
    } catch (err) {
      console.error("Error loading schedule:", err);
    } finally {
      setLoadingSchedule(false);
    }
  };

  // Toggle Task Completion
  const handleToggleTask = async (taskId) => {
    try {
      const updated = await apiRequest(`/planner/tasks/${taskId}/toggle`, { method: "PATCH" });
      toast.success(updated.is_completed ? "Task marked completed!" : "Task marked incomplete");
      // Refresh both overview and schedule
      loadOverview();
      loadSchedule();
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask(updated);
      }
    } catch (err) {
      console.error("Error toggling task:", err);
      toast.error("Failed to update task completion.");
    }
  };

  // Reschedule Task
  const handleRescheduleTask = async (taskId, newDate) => {
    try {
      const updated = await apiRequest(`/planner/tasks/${taskId}/reschedule`, {
        method: "PATCH",
        body: JSON.stringify({ scheduled_date: newDate }),
      });
      toast.success(`Rescheduled to ${newDate}`);
      setSelectedTask(null);
      loadSchedule();
      loadOverview();
    } catch (err) {
      console.error("Error rescheduling task:", err);
      toast.error("Failed to reschedule task.");
    }
  };

  // Save Semester Config
  const handleSaveSemester = async (e) => {
    e.preventDefault();
    try {
      await apiRequest("/planner/semester", {
        method: "POST",
        body: JSON.stringify(semesterForm),
      });
      toast.success("Semester configured and study plan initialized!");
      setShowSemesterModal(false);
      loadOverview();
      loadSchedule();
    } catch (err) {
      console.error("Error configuring semester:", err);
      toast.error(err.message || "Failed to save semester configuration.");
    }
  };

  // Create Custom Task
  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...taskForm,
        subject_id: taskForm.subject_id ? parseInt(taskForm.subject_id) : selectedSubjectId || null,
      };
      await apiRequest("/planner/tasks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      toast.success("Study task added to schedule!");
      setShowAddTaskModal(false);
      setTaskForm({
        title: "",
        subject_id: "",
        scheduled_date: getTodayDateString(),
        task_type: "learning",
        priority: "Medium",
        estimated_minutes: 45,
        notes: "",
      });
      loadSchedule();
      loadOverview();
    } catch (err) {
      console.error("Error adding task:", err);
      toast.error("Failed to create task.");
    }
  };

  // Delete Task
  const handleDeleteTask = async (taskId) => {
    try {
      await apiRequest(`/planner/tasks/${taskId}`, { method: "DELETE" });
      toast.success("Task removed from schedule.");
      setSelectedTask(null);
      loadSchedule();
      loadOverview();
    } catch (err) {
      console.error("Error deleting task:", err);
      toast.error("Failed to remove task.");
    }
  };

  // Add Blackout Date
  const handleAddBlackout = async (e) => {
    e.preventDefault();
    try {
      await apiRequest("/planner/blackout-dates", {
        method: "POST",
        body: JSON.stringify(blackoutForm),
      });
      toast.success("Unavailable / holiday date saved!");
      setShowBlackoutModal(false);
      loadSchedule();
      loadOverview();
    } catch (err) {
      console.error("Error adding blackout date:", err);
      toast.error("Failed to save blackout date.");
    }
  };

  // Remove Blackout Date
  const handleRemoveBlackout = async (dateId) => {
    try {
      await apiRequest(`/planner/blackout-dates/${dateId}`, { method: "DELETE" });
      toast.success("Unavailable date removed.");
      loadSchedule();
      loadOverview();
    } catch (err) {
      console.error("Error removing blackout date:", err);
      toast.error("Failed to remove date.");
    }
  };

  // Preview Rebalance
  const handleOpenRebalance = async () => {
    try {
      const preview = await apiRequest("/planner/rebalance/preview", { method: "POST" });
      setRebalancePreview(preview);
      setShowRebalanceModal(true);
    } catch (err) {
      console.error("Error previewing rebalance:", err);
      toast.error("Failed to preview rebalance.");
    }
  };

  // Apply Rebalance
  const handleApplyRebalance = async () => {
    try {
      const res = await apiRequest("/planner/rebalance/apply", { method: "POST" });
      toast.success(res.message || "Schedule rebalanced!");
      setShowRebalanceModal(false);
      loadOverview();
      loadSchedule();
    } catch (err) {
      console.error("Error applying rebalance:", err);
      toast.error("Failed to rebalance schedule.");
    }
  };

  // Launch Live Study Session with Task
  const handleStartStudySession = (task) => {
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

  // Calendar Helpers
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const monthName = currentDate.toLocaleString("default", { month: "long" });

  const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const setToday = () => setCurrentDate(new Date());

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sunday
  const todayStr = getTodayDateString();

  // Group tasks by date string
  const tasksByDate = {};
  scheduleData.tasks.forEach((t) => {
    tasksByDate[t.scheduled_date] = tasksByDate[t.scheduled_date] || [];
    tasksByDate[t.scheduled_date].push(t);
  });

  const blackoutsByDate = {};
  scheduleData.blackout_dates.forEach((b) => {
    blackoutsByDate[b.date] = b;
  });

  const assignmentsByDate = {};
  scheduleData.assignments.forEach((a) => {
    if (a.due_date) {
      assignmentsByDate[a.due_date] = assignmentsByDate[a.due_date] || [];
      assignmentsByDate[a.due_date].push(a);
    }
  });

  // Selected Subject Details
  const activeSubject = overview?.subject_cards?.find((s) => s.id === selectedSubjectId);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "50vh", flexDirection: "column", gap: "1rem" }}>
        <div className="spinner" />
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>Loading AI Academic Command Center...</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem", maxWidth: "1400px", margin: "0 auto" }}>
      {/* 1. TOP HEADER & SEMESTER TIMELINE BANNER */}
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "10px",
          padding: "1.25rem 1.5rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <span
                style={{
                  display: "inline-flex",
                  padding: "6px",
                  borderRadius: "6px",
                  backgroundColor: "var(--color-sage-soft)",
                  color: "var(--color-sage)",
                }}
              >
                <Sparkles size={18} />
              </span>
              <h1 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)", margin: 0 }}>
                AI Academic Planner & Command Center
              </h1>
            </div>
            <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginTop: "4px", marginBottom: 0 }}>
              Dynamic semester scheduling, subject-wise calendars, topic distribution, and intelligent deadline rebalancing.
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
            <Button
              variant="outline"
              size="sm"
              icon={RotateCcw}
              onClick={handleOpenRebalance}
              disabled={!overview?.is_configured}
            >
              Rebalance Schedule
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={Plus}
              onClick={() => setShowAddTaskModal(true)}
              disabled={!overview?.is_configured}
            >
              Add Task
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={CalendarDays}
              onClick={() => setShowBlackoutModal(true)}
              disabled={!overview?.is_configured}
            >
              Add Off-Day / Holiday
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={Edit3}
              onClick={() => setShowSemesterModal(true)}
            >
              {overview?.is_configured ? "Edit Semester Dates" : "Setup Semester"}
            </Button>
          </div>
        </div>

        {/* Semester Progress Bar & Date Range */}
        {overview?.is_configured ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1.25rem",
              paddingTop: "0.75rem",
              borderTop: "1px solid var(--border-subtle)",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: "4px" }}>
                <span style={{ color: "var(--text-muted)" }}>Semester Window</span>
                <span style={{ fontWeight: 600 }}>{overview.semester.start_date} → {overview.semester.end_date}</span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                {overview.days_elapsed} of {overview.days_total} days elapsed ({overview.days_remaining} remaining)
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: "4px" }}>
                <span style={{ color: "var(--text-muted)" }}>Semester Timeline</span>
                <span style={{ fontWeight: 600 }}>{overview.semester_progress_percent}%</span>
              </div>
              <ProgressBar value={overview.semester_progress_percent} max={100} color="var(--color-terracotta)" height={6} />
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: "4px" }}>
                <span style={{ color: "var(--text-muted)" }}>Syllabus Topics Mastered</span>
                <span style={{ fontWeight: 600 }}>{overview.completed_topics_count} / {overview.total_topics_count} ({overview.syllabus_progress_percent}%)</span>
              </div>
              <ProgressBar value={overview.syllabus_progress_percent} max={100} color="var(--color-sage)" height={6} />
            </div>
          </div>
        ) : (
          <div
            style={{
              padding: "1rem",
              backgroundColor: "var(--color-sage-soft)",
              border: "1px dashed var(--color-sage)",
              borderRadius: "8px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.75rem",
            }}
          >
            <div>
              <h4 style={{ margin: 0, fontSize: "0.95rem", color: "var(--color-sage)", fontWeight: 600 }}>
                Semester Setup Required
              </h4>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                Configure your semester start and end dates to activate personalized, topic-wise schedule generation across all subjects.
              </p>
            </div>
            <Button size="sm" variant="primary" onClick={() => setShowSemesterModal(true)}>
              Start Semester Setup
            </Button>
          </div>
        )}
      </div>

      {/* 2. AI INSIGHTS & WORKLOAD WARNINGS */}
      {(overview?.workload_warnings?.length > 0 || overview?.ai_insights?.length > 0) && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {overview.workload_warnings.map((w, idx) => (
            <div
              key={`warn-${idx}`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.75rem 1rem",
                backgroundColor: "rgba(220, 100, 60, 0.08)",
                borderLeft: "4px solid var(--color-terracotta)",
                borderRadius: "6px",
                fontSize: "0.88rem",
                color: "var(--text-main)",
              }}
            >
              <AlertTriangle size={17} style={{ color: "var(--color-terracotta)", flexShrink: 0 }} />
              <span>{w}</span>
            </div>
          ))}

          {overview.ai_insights.map((ins, idx) => (
            <div
              key={`ins-${idx}`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.75rem 1rem",
                backgroundColor: "var(--color-sage-soft)",
                borderLeft: "4px solid var(--color-sage)",
                borderRadius: "6px",
                fontSize: "0.88rem",
                color: "var(--text-main)",
              }}
            >
              <Sparkles size={17} style={{ color: "var(--color-sage)", flexShrink: 0 }} />
              <div>
                <strong>{ins.title}: </strong>
                <span>{ins.description}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 3. SEPARATE CALENDAR FOR EVERY SUBJECT - SUBJECT CARDS ROW */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-main)", margin: 0 }}>
            Subject Calendars & Workspaces
          </h3>
          <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            Select a subject to isolate its modules, topics, revisions, and deadlines
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: "0.85rem",
          }}
        >
          {/* Master Calendar Option */}
          <div
            onClick={() => setSelectedSubjectId(null)}
            style={{
              padding: "1rem",
              borderRadius: "8px",
              backgroundColor: "var(--bg-surface)",
              border: selectedSubjectId === null ? "2px solid var(--color-sage)" : "1px solid var(--border-color)",
              cursor: "pointer",
              transition: "all 0.2s ease",
              boxShadow: selectedSubjectId === null ? "0 4px 12px rgba(90, 110, 82, 0.12)" : "none",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-main)" }}>
                Master Schedule
              </span>
              <Badge variant={selectedSubjectId === null ? "good" : "neutral"}>All Courses</Badge>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: 0 }}>
              Consolidated view of all {overview?.subject_cards?.length || 0} registered subjects
            </p>
          </div>

          {/* Registered Subject Cards */}
          {overview?.subject_cards?.map((subj) => {
            const isSelected = selectedSubjectId === subj.id;
            return (
              <div
                key={subj.id}
                onClick={() => setSelectedSubjectId(subj.id)}
                style={{
                  padding: "1rem",
                  borderRadius: "8px",
                  backgroundColor: "var(--bg-surface)",
                  border: isSelected ? `2px solid ${subj.color || "var(--color-sage)"}` : "1px solid var(--border-color)",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: isSelected ? `0 4px 12px ${subj.color}22` : "none",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: "3px",
                    backgroundColor: subj.color || "var(--color-sage)",
                  }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)" }}>
                      {subj.name}
                    </h4>
                    {subj.code && (
                      <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{subj.code}</span>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      backgroundColor: `${subj.color}18`,
                      color: subj.color,
                      fontWeight: 600,
                    }}
                  >
                    {subj.credits} Cr
                  </span>
                </div>

                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "3px" }}>
                    <span>Progress</span>
                    <span>{subj.completed_topics}/{subj.total_topics} topics ({subj.progress_percent}%)</span>
                  </div>
                  <ProgressBar value={subj.progress_percent} max={100} color={subj.color || "var(--color-sage)"} height={5} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. CALENDAR CONTROLS & MAIN WORKSPACE */}
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "10px",
          overflow: "hidden",
          boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
        }}
      >
        {/* Calendar Header Bar */}
        <div
          style={{
            padding: "1rem 1.25rem",
            borderBottom: "1px solid var(--border-color)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1rem",
            backgroundColor: "var(--bg-surface-soft)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0, color: "var(--text-main)" }}>
              {activeSubject ? `${activeSubject.name} Calendar` : "All Courses Calendar"}
            </h2>
            {activeSubject && (
              <Button size="sm" variant="ghost" onClick={() => setSelectedSubjectId(null)}>
                Show All
              </Button>
            )}
          </div>

          {/* Month / Week / Agenda Switcher & Month Navigation */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", backgroundColor: "var(--bg-app)", padding: "3px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
              <Button
                size="sm"
                variant={calendarView === "month" ? "primary" : "ghost"}
                icon={Grid}
                onClick={() => setCalendarView("month")}
                style={{ padding: "4px 10px", fontSize: "0.82rem" }}
              >
                Month
              </Button>
              <Button
                size="sm"
                variant={calendarView === "agenda" ? "primary" : "ghost"}
                icon={List}
                onClick={() => setCalendarView("agenda")}
                style={{ padding: "4px 10px", fontSize: "0.82rem" }}
              >
                Agenda
              </Button>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Button size="sm" variant="outline" icon={ChevronLeft} onClick={prevMonth} />
              <Button size="sm" variant="outline" onClick={setToday}>
                Today
              </Button>
              <Button size="sm" variant="outline" icon={ChevronRight} onClick={nextMonth} />
              <span style={{ fontSize: "0.95rem", fontWeight: 600, minWidth: "120px", textAlign: "center" }}>
                {monthName} {year}
              </span>
            </div>
          </div>
        </div>

        {/* 5. CALENDAR VIEWS */}
        {loadingSchedule ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            Updating calendar feed...
          </div>
        ) : calendarView === "month" ? (
          /* MONTH VIEW GRID */
          <div style={{ padding: "0.75rem" }}>
            {/* Weekday Labels */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(7, 1fr)",
                gap: "6px",
                marginBottom: "6px",
                textAlign: "center",
                fontWeight: 600,
                fontSize: "0.82rem",
                color: "var(--text-muted)",
              }}
            >
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                <div key={day} style={{ padding: "6px" }}>{day}</div>
              ))}
            </div>

            {/* Days Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(7, 1fr)",
                gap: "6px",
              }}
            >
              {/* Empty padding cells for first week offset */}
              {Array.from({ length: firstDayIndex }).map((_, idx) => (
                <div
                  key={`pad-${idx}`}
                  style={{
                    minHeight: "110px",
                    backgroundColor: "var(--bg-app)",
                    opacity: 0.4,
                    borderRadius: "6px",
                  }}
                />
              ))}

              {/* Day cells in month */}
              {Array.from({ length: daysInMonth }).map((_, dayIdx) => {
                const dayNum = dayIdx + 1;
                const dStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
                const isToday = dStr === todayStr;
                const dayTasks = tasksByDate[dStr] || [];
                const blackout = blackoutsByDate[dStr];
                const dayAssignments = assignmentsByDate[dStr] || [];

                return (
                  <div
                    key={dStr}
                    onClick={() => {
                      setTaskForm((prev) => ({ ...prev, scheduled_date: dStr }));
                    }}
                    style={{
                      minHeight: "115px",
                      backgroundColor: blackout
                        ? "rgba(140, 109, 88, 0.06)"
                        : isToday
                        ? "rgba(90, 110, 82, 0.05)"
                        : "var(--bg-app)",
                      border: isToday
                        ? "2px solid var(--color-sage)"
                        : blackout
                        ? "1px dashed var(--color-terracotta)"
                        : "1px solid var(--border-subtle)",
                      borderRadius: "6px",
                      padding: "6px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                      position: "relative",
                      transition: "border 0.2s ease",
                    }}
                  >
                    {/* Date Number & Blackout Label */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span
                        style={{
                          fontSize: "0.82rem",
                          fontWeight: isToday ? 700 : 500,
                          color: isToday ? "var(--color-sage)" : "var(--text-main)",
                          width: "22px",
                          height: "22px",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          borderRadius: "50%",
                          backgroundColor: isToday ? "var(--color-sage-soft)" : "transparent",
                        }}
                      >
                        {dayNum}
                      </span>

                      {blackout && (
                        <span
                          title={blackout.reason}
                          style={{
                            fontSize: "0.68rem",
                            padding: "1px 4px",
                            backgroundColor: "rgba(220, 100, 60, 0.15)",
                            color: "var(--color-terracotta)",
                            borderRadius: "3px",
                            fontWeight: 600,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            maxWidth: "70px",
                          }}
                        >
                          {blackout.reason}
                        </span>
                      )}
                    </div>

                    {/* Assignments Due on this date */}
                    {dayAssignments.map((a) => (
                      <div
                        key={`assign-${a.id}`}
                        style={{
                          fontSize: "0.72rem",
                          backgroundColor: "rgba(220, 100, 60, 0.12)",
                          borderLeft: "3px solid var(--color-terracotta)",
                          color: "var(--text-main)",
                          padding: "2px 5px",
                          borderRadius: "3px",
                          fontWeight: 600,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={`Due: ${a.title} (${a.priority} Priority)`}
                      >
                        ⏰ {a.title}
                      </div>
                    ))}

                    {/* Study Tasks scheduled on this date */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "3px", overflowY: "auto", maxHeight: "80px" }}>
                      {dayTasks.map((t) => {
                        const isDone = t.is_completed;
                        return (
                          <div
                            key={t.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTask(t);
                            }}
                            style={{
                              fontSize: "0.72rem",
                              backgroundColor: isDone ? "var(--bg-surface-soft)" : `${t.subject_color || "#5A6E52"}14`,
                              borderLeft: `3px solid ${isDone ? "var(--text-muted)" : t.subject_color || "var(--color-sage)"}`,
                              padding: "2px 5px",
                              borderRadius: "3px",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              gap: "4px",
                              opacity: isDone ? 0.6 : 1,
                              textDecoration: isDone ? "line-through" : "none",
                            }}
                            title={`${t.subject_name || "Topic"}: ${t.title} (${t.task_type})`}
                          >
                            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {t.title}
                            </span>
                            {isDone && <CheckCircle2 size={10} style={{ color: "var(--color-sage)", flexShrink: 0 }} />}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* AGENDA / LIST VIEW */
          <div style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {scheduleData.tasks.length === 0 ? (
              <EmptyState
                icon={Calendar}
                title="No tasks scheduled"
                description="Use 'Add Task' or configure your semester to populate your study agenda."
              />
            ) : (
              Object.keys(tasksByDate)
                .sort()
                .map((dStr) => {
                  const tasksForDay = tasksByDate[dStr];
                  const blackout = blackoutsByDate[dStr];
                  const assignmentsForDay = assignmentsByDate[dStr] || [];
                  const isToday = dStr === todayStr;

                  return (
                    <div
                      key={`agenda-${dStr}`}
                      style={{
                        backgroundColor: isToday ? "rgba(90, 110, 82, 0.04)" : "var(--bg-app)",
                        border: isToday ? "1px solid var(--color-sage)" : "1px solid var(--border-subtle)",
                        borderRadius: "8px",
                        padding: "1rem",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "0.75rem",
                          paddingBottom: "0.5rem",
                          borderBottom: "1px solid var(--border-subtle)",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                          <span style={{ fontWeight: 700, fontSize: "0.95rem", color: isToday ? "var(--color-sage)" : "var(--text-main)" }}>
                            {dStr} {isToday && "(Today)"}
                          </span>
                          {blackout && (
                            <Badge variant="warning">{blackout.reason}</Badge>
                          )}
                        </div>
                        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          {tasksForDay.length} task(s)
                        </span>
                      </div>

                      {/* Day Tasks List */}
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {tasksForDay.map((t) => (
                          <div
                            key={t.id}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              padding: "0.6rem 0.8rem",
                              backgroundColor: "var(--bg-surface)",
                              border: "1px solid var(--border-subtle)",
                              borderRadius: "6px",
                              gap: "0.75rem",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flex: 1, minWidth: 0 }}>
                              <button
                                onClick={() => handleToggleTask(t.id)}
                                style={{
                                  background: "none",
                                  border: "none",
                                  cursor: "pointer",
                                  padding: 0,
                                  color: t.is_completed ? "var(--color-sage)" : "var(--text-muted)",
                                }}
                              >
                                {t.is_completed ? <CheckSquare size={18} /> : <Square size={18} />}
                              </button>

                              <div style={{ minWidth: 0 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                                  <span
                                    style={{
                                      fontSize: "0.75rem",
                                      padding: "1px 6px",
                                      borderRadius: "3px",
                                      backgroundColor: `${t.subject_color || "#5A6E52"}18`,
                                      color: t.subject_color || "var(--color-sage)",
                                      fontWeight: 600,
                                    }}
                                  >
                                    {t.subject_name || "Coursework"}
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
                                </div>
                                <div
                                  style={{
                                    fontSize: "0.88rem",
                                    fontWeight: 500,
                                    color: "var(--text-main)",
                                    marginTop: "2px",
                                    textDecoration: t.is_completed ? "line-through" : "none",
                                    opacity: t.is_completed ? 0.6 : 1,
                                  }}
                                >
                                  {t.title}
                                </div>
                              </div>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                              <Button
                                size="sm"
                                variant="ghost"
                                icon={PlayCircle}
                                onClick={() => handleStartStudySession(t)}
                                title="Start live session"
                              >
                                Study
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                icon={Edit3}
                                onClick={() => setSelectedTask(t)}
                                title="Reschedule or edit"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })
            )}
          </div>
        )}
      </div>

      {/* 6. BOTTOM PANELS: TODAY'S FOCUS LOAD & UPCOMING ASSIGNMENTS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: "1.25rem",
        }}
      >
        {/* Today's Planned Tasks Card */}
        <Card
          title="Today's Planned Focus"
          subtitle={`${overview?.today_tasks?.length || 0} tasks planned for today`}
          icon={Target}
        >
          {overview?.today_tasks?.length === 0 ? (
            <div style={{ textAlign: "center", padding: "1.5rem", color: "var(--text-muted)", fontSize: "0.88rem" }}>
              Nothing scheduled for today. Enjoy your day or pick a topic to get ahead!
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {overview.today_tasks.map((t) => (
                <div
                  key={`today-${t.id}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.6rem 0.75rem",
                    backgroundColor: "var(--bg-app)",
                    borderRadius: "6px",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <button
                      onClick={() => handleToggleTask(t.id)}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 0,
                        color: t.is_completed ? "var(--color-sage)" : "var(--text-muted)",
                      }}
                    >
                      {t.is_completed ? <CheckSquare size={17} /> : <Square size={17} />}
                    </button>
                    <div>
                      <span style={{ fontSize: "0.75rem", color: t.subject_color || "var(--color-sage)", fontWeight: 600 }}>
                        {t.subject_name || "General"}
                      </span>
                      <div
                        style={{
                          fontSize: "0.85rem",
                          fontWeight: 500,
                          textDecoration: t.is_completed ? "line-through" : "none",
                          opacity: t.is_completed ? 0.6 : 1,
                        }}
                      >
                        {t.title}
                      </div>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="ghost"
                    icon={PlayCircle}
                    onClick={() => handleStartStudySession(t)}
                  >
                    Start
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Pending & Upcoming Assignments Card */}
        <Card
          title="Pending Coursework & Deadlines"
          subtitle="Assignments slotted into your study calendar"
          icon={Flag}
        >
          {overview?.upcoming_assignments?.length === 0 && overview?.overdue_assignments?.length === 0 ? (
            <div style={{ textAlign: "center", padding: "1.5rem", color: "var(--text-muted)", fontSize: "0.88rem" }}>
              No pending assignments. You are fully up to date!
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {overview?.overdue_assignments?.map((a) => (
                <div
                  key={`overdue-${a.id}`}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.6rem 0.75rem",
                    backgroundColor: "rgba(220, 100, 60, 0.08)",
                    borderLeft: "3px solid var(--color-terracotta)",
                    borderRadius: "4px",
                  }}
                >
                  <div>
                    <span style={{ fontSize: "0.72rem", color: "var(--color-terracotta)", fontWeight: 700 }}>
                      OVERDUE
                    </span>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>{a.title}</div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {a.subject_name} • Due: {a.due_date?.slice(0, 10)}
                    </span>
                  </div>
                  <Badge variant="danger">{a.priority}</Badge>
                </div>
              ))}

              {overview?.upcoming_assignments?.map((a) => (
                <div
                  key={`up-${a.id}`}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.6rem 0.75rem",
                    backgroundColor: "var(--bg-app)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "4px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 500 }}>{a.title}</div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {a.subject_name} • Due: {a.due_date?.slice(0, 10)}
                    </span>
                  </div>
                  <Badge variant={a.priority === "Critical" || a.priority === "High" ? "warning" : "neutral"}>
                    {a.priority}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* ========================================================================= */}
      {/* MODAL 1: SEMESTER SETUP & EDIT */}
      {/* ========================================================================= */}
      <Modal
        isOpen={showSemesterModal}
        onClose={() => setShowSemesterModal(false)}
        title="Semester Configuration & Plan Setup"
        maxWidth="500px"
      >
        <form onSubmit={handleSaveSemester} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Semester Start Date
            </label>
            <input
              type="date"
              className="input-field"
              value={semesterForm.start_date}
              onChange={(e) => setSemesterForm({ ...semesterForm, start_date: e.target.value })}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Semester End Date
            </label>
            <input
              type="date"
              className="input-field"
              value={semesterForm.end_date}
              onChange={(e) => setSemesterForm({ ...semesterForm, end_date: e.target.value })}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
              Active Study Weekdays
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "6px" }}>
              {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((d) => {
                const checked = semesterForm.study_days.includes(d);
                return (
                  <label
                    key={d}
                    style={{
                      fontSize: "0.8rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...semesterForm.study_days, d]
                          : semesterForm.study_days.filter((x) => x !== d);
                        setSemesterForm({ ...semesterForm, study_days: next });
                      }}
                    />
                    {d.slice(0, 3)}
                  </label>
                );
              })}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.82rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Max Topics / Day
              </label>
              <input
                type="number"
                min="1"
                max="10"
                className="input-field"
                value={semesterForm.max_daily_tasks}
                onChange={(e) => setSemesterForm({ ...semesterForm, max_daily_tasks: parseInt(e.target.value) || 3 })}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.82rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Target Study Hours / Day
              </label>
              <input
                type="number"
                min="0.5"
                max="16"
                step="0.5"
                className="input-field"
                value={semesterForm.target_study_hours_daily}
                onChange={(e) => setSemesterForm({ ...semesterForm, target_study_hours_daily: parseFloat(e.target.value) || 3.0 })}
              />
            </div>
          </div>

          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0" }}>
            💡 Generating the plan distributes unfinished topics from all registered course syllabi fairly without overwriting completed progress.
          </p>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
            <Button type="button" variant="outline" onClick={() => setShowSemesterModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Generate & Save Plan
            </Button>
          </div>
        </form>
      </Modal>

      {/* ========================================================================= */}
      {/* MODAL 2: ADD STUDY TASK / REVISION */}
      {/* ========================================================================= */}
      <Modal
        isOpen={showAddTaskModal}
        onClose={() => setShowAddTaskModal(false)}
        title="Add Custom Study / Revision Task"
        maxWidth="480px"
      >
        <form onSubmit={handleCreateTask} style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Task Title
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Master Dynamic Programming or Revise Unit 2"
              value={taskForm.title}
              onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
              required
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Subject (Optional)
              </label>
              <select
                className="input-field"
                value={taskForm.subject_id}
                onChange={(e) => setTaskForm({ ...taskForm, subject_id: e.target.value })}
              >
                <option value="">General / Personal</option>
                {overview?.subject_cards?.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Scheduled Date
              </label>
              <input
                type="date"
                className="input-field"
                value={taskForm.scheduled_date}
                onChange={(e) => setTaskForm({ ...taskForm, scheduled_date: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Task Type
              </label>
              <select
                className="input-field"
                value={taskForm.task_type}
                onChange={(e) => setTaskForm({ ...taskForm, task_type: e.target.value })}
              >
                <option value="learning">Learning New Topic</option>
                <option value="practice">Practice & Problem Solving</option>
                <option value="revision">Active Recall Revision</option>
                <option value="assignment">Assignment Prep</option>
                <option value="custom">Custom Task</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Priority
              </label>
              <select
                className="input-field"
                value={taskForm.priority}
                onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
            <Button type="button" variant="outline" onClick={() => setShowAddTaskModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Add to Schedule
            </Button>
          </div>
        </form>
      </Modal>

      {/* ========================================================================= */}
      {/* MODAL 3: ADD BLACKOUT / HOLIDAY DATE */}
      {/* ========================================================================= */}
      <Modal
        isOpen={showBlackoutModal}
        onClose={() => setShowBlackoutModal(false)}
        title="Add Holiday / Unavailable Date"
        maxWidth="440px"
      >
        <form onSubmit={handleAddBlackout} style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Date
            </label>
            <input
              type="date"
              className="input-field"
              value={blackoutForm.date}
              onChange={(e) => setBlackoutForm({ ...blackoutForm, date: e.target.value })}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Reason / Event Name
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Midterm Exams, Festival Break, Personal Leave"
              value={blackoutForm.reason}
              onChange={(e) => setBlackoutForm({ ...blackoutForm, reason: e.target.value })}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
              Type
            </label>
            <select
              className="input-field"
              value={blackoutForm.blackout_type}
              onChange={(e) => setBlackoutForm({ ...blackoutForm, blackout_type: e.target.value })}
            >
              <option value="holiday">Holiday / Break</option>
              <option value="exam">Examination Window</option>
              <option value="personal">Personal Commitment</option>
            </select>
          </div>

          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0" }}>
            Study topics will not be scheduled on unavailable dates during plan generation or rebalancing.
          </p>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
            <Button type="button" variant="outline" onClick={() => setShowBlackoutModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Mark Date Unavailable
            </Button>
          </div>
        </form>
      </Modal>

      {/* ========================================================================= */}
      {/* MODAL 4: TASK DETAIL & RESCHEDULE */}
      {/* ========================================================================= */}
      {selectedTask && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedTask(null)}
          title="Study Task Details"
          maxWidth="440px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "2px 6px",
                  borderRadius: "3px",
                  backgroundColor: `${selectedTask.subject_color || "#5A6E52"}18`,
                  color: selectedTask.subject_color || "var(--color-sage)",
                  fontWeight: 600,
                }}
              >
                {selectedTask.subject_name || "General Coursework"}
              </span>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600, margin: "6px 0 2px 0", color: "var(--text-main)" }}>
                {selectedTask.title}
              </h3>
              {selectedTask.module_name && (
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: 0 }}>
                  {selectedTask.module_name}
                </p>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.85rem" }}>
              <div>
                <span style={{ color: "var(--text-muted)", display: "block" }}>Type</span>
                <strong style={{ textTransform: "capitalize" }}>{selectedTask.task_type}</strong>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)", display: "block" }}>Priority</span>
                <strong>{selectedTask.priority}</strong>
              </div>
            </div>

            {/* Quick Reschedule */}
            <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem" }}>
              <label style={{ fontSize: "0.82rem", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Reschedule Date
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="date"
                  className="input-field"
                  defaultValue={selectedTask.scheduled_date}
                  onChange={(e) => handleRescheduleTask(selectedTask.id, e.target.value)}
                />
              </div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderTop: "1px solid var(--border-subtle)",
                paddingTop: "0.75rem",
                gap: "0.5rem",
                flexWrap: "wrap",
              }}
            >
              <Button
                variant={selectedTask.is_completed ? "outline" : "primary"}
                size="sm"
                icon={selectedTask.is_completed ? CheckSquare : Square}
                onClick={() => handleToggleTask(selectedTask.id)}
              >
                {selectedTask.is_completed ? "Completed" : "Mark Complete"}
              </Button>

              <div style={{ display: "flex", gap: "0.4rem" }}>
                <Button
                  variant="outline"
                  size="sm"
                  icon={PlayCircle}
                  onClick={() => {
                    handleStartStudySession(selectedTask);
                    setSelectedTask(null);
                  }}
                >
                  Start Live Session
                </Button>

                <Button
                  variant="danger"
                  size="sm"
                  icon={Trash2}
                  onClick={() => handleDeleteTask(selectedTask.id)}
                  title="Remove from schedule"
                />
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* ========================================================================= */}
      {/* MODAL 5: REBALANCE PREVIEW & CONFIRM */}
      {/* ========================================================================= */}
      {showRebalanceModal && rebalancePreview && (
        <Modal
          isOpen={true}
          onClose={() => setShowRebalanceModal(false)}
          title="Preview Intelligent Rebalance"
          maxWidth="560px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <p style={{ fontSize: "0.88rem", color: "var(--text-main)", margin: 0 }}>
              {rebalancePreview.summary}
            </p>

            {rebalancePreview.warnings?.length > 0 && (
              <div style={{ padding: "0.75rem", backgroundColor: "rgba(220, 100, 60, 0.08)", borderRadius: "6px" }}>
                {rebalancePreview.warnings.map((w, i) => (
                  <p key={i} style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-terracotta)" }}>
                    ⚠️ {w}
                  </p>
                ))}
              </div>
            )}

            {/* List of Shifted Tasks */}
            {rebalancePreview.shifted_tasks?.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "250px", overflowY: "auto" }}>
                <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)" }}>
                  Proposed Date Adjustments ({rebalancePreview.shifted_tasks.length}):
                </span>
                {rebalancePreview.shifted_tasks.map((shift, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "0.5rem 0.75rem",
                      backgroundColor: "var(--bg-app)",
                      borderRadius: "4px",
                      fontSize: "0.82rem",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <div>
                      <strong>{shift.title}</strong>
                      <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{shift.subject_name}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontWeight: 600 }}>
                      <span style={{ color: "var(--color-terracotta)", textDecoration: "line-through" }}>{shift.old_date}</span>
                      <ArrowRight size={12} />
                      <span style={{ color: "var(--color-sage)" }}>{shift.new_date}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "0.85rem", color: "var(--color-sage)", margin: 0 }}>
                ✔️ All tasks are on schedule! No adjustments required.
              </p>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem" }}>
              <Button variant="outline" onClick={() => setShowRebalanceModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleApplyRebalance}
                disabled={rebalancePreview.shifted_tasks?.length === 0}
              >
                Apply Date Adjustments
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
