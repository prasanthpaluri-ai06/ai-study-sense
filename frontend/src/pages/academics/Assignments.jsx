import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState, ProgressBar } from "../../components/common/Badge";
import { Modal, Tabs } from "../../components/common/Modal";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Calendar,
  Plus,
  CheckSquare,
  Square,
  Clock,
  AlertCircle,
  Sparkles,
  Edit2,
  Trash2,
  Filter,
  Flame,
  ChevronDown,
  ChevronUp,
  Sliders,
  CheckCircle2,
} from "lucide-react";
import {
  formatDateTime,
  toLocalDateTimeInputValue,
  toIsoFromLocalInput,
} from "../../utils/dateUtils";

export default function Assignments() {
  const [assignments, setAssignments] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [prioritizedTasks, setPrioritizedTasks] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [showAiPrioritizer, setShowAiPrioritizer] = useState(false);
  const [expandedAiTaskId, setExpandedAiTaskId] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState(null);

  // Form Fields
  const [subjectId, setSubjectId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [status, setStatus] = useState("Not Started");
  const [progressPercent, setProgressPercent] = useState(0);
  const [estimatedEffort, setEstimatedEffort] = useState("2.0");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const toast = useToast();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [asgns, subs, prioritized] = await Promise.all([
        apiRequest("/academic/assignments").catch(() => []),
        apiRequest("/academic/subjects").catch(() => []),
        apiRequest("/academic/assignments/prioritized").catch(() => []),
      ]);
      setAssignments(asgns || []);
      setSubjects(subs || []);
      setPrioritizedTasks(prioritized || []);
      if (subs.length > 0 && !subjectId) {
        setSubjectId(String(subs[0].id));
      }
    } catch (err) {
      toast.error(err.message || "Failed loading assignments");
    } finally {
      setLoading(false);
    }
  }

  // Open Add Modal
  const handleOpenAddModal = () => {
    if (subjects.length === 0) {
      toast.warning("Please create an academic subject first before adding assignments.");
      return;
    }
    setSubjectId(String(subjects[0].id));
    setTitle("");
    setDescription("");
    // Default due date: tomorrow at 23:59
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(23, 59, 0, 0);
    setDueDate(toLocalDateTimeInputValue(tomorrow));
    setPriority("Medium");
    setStatus("Not Started");
    setProgressPercent(0);
    setEstimatedEffort("2.0");
    setNotes("");
    setIsAddModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (a) => {
    setSelectedAssignment(a);
    setSubjectId(String(a.subject_id));
    setTitle(a.title || "");
    setDescription(a.description || "");
    setDueDate(a.due_date ? toLocalDateTimeInputValue(a.due_date) : "");
    setPriority(a.priority || "Medium");
    setStatus(a.status || "Not Started");
    setProgressPercent(a.progress_percent || 0);
    setEstimatedEffort(String(a.estimated_effort_hours || "2.0"));
    setNotes(a.notes || "");
    setIsEditModalOpen(true);
  };

  // Open Delete Modal
  const handleOpenDeleteModal = (a) => {
    setSelectedAssignment(a);
    setIsDeleteModalOpen(true);
  };

  // Create Assignment
  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    if (!subjectId || !title.trim() || !dueDate) return;
    setSaving(true);
    try {
      await apiRequest("/academic/assignments", {
        method: "POST",
        body: JSON.stringify({
          subject_id: parseInt(subjectId),
          title: title.trim(),
          description: description.trim() || null,
          due_date: toIsoFromLocalInput(dueDate),
          priority,
          status,
          progress_percent: parseInt(progressPercent) || 0,
          estimated_effort_hours: parseFloat(estimatedEffort) || 2.0,
          notes: notes.trim() || null,
        }),
      });
      setIsAddModalOpen(false);
      toast.success("Assignment created successfully");
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed creating assignment");
    } finally {
      setSaving(false);
    }
  };

  // Update Assignment
  const handleUpdateAssignment = async (e) => {
    e.preventDefault();
    if (!selectedAssignment || !title.trim() || !dueDate) return;
    setSaving(true);
    try {
      await apiRequest(`/academic/assignments/${selectedAssignment.id}`, {
        method: "PUT",
        body: JSON.stringify({
          subject_id: parseInt(subjectId),
          title: title.trim(),
          description: description.trim() || null,
          due_date: toIsoFromLocalInput(dueDate),
          priority,
          status,
          progress_percent: parseInt(progressPercent) || 0,
          estimated_effort_hours: parseFloat(estimatedEffort) || 2.0,
          notes: notes.trim() || null,
        }),
      });
      setIsEditModalOpen(false);
      toast.success("Assignment updated successfully");
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed updating assignment");
    } finally {
      setSaving(false);
    }
  };

  // Delete Assignment
  const handleDeleteAssignment = async () => {
    if (!selectedAssignment) return;
    setSaving(true);
    try {
      await apiRequest(`/academic/assignments/${selectedAssignment.id}`, {
        method: "DELETE",
      });
      setIsDeleteModalOpen(false);
      toast.info(`Assignment '${selectedAssignment.title}' removed`);
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed deleting assignment");
    } finally {
      setSaving(false);
    }
  };

  // Quick Toggle Status
  const handleToggleStatus = async (assign) => {
    const isCompleted = assign.status === "Completed";
    const nextStatus = isCompleted ? "In Progress" : "Completed";
    const nextProgress = isCompleted ? 50 : 100;
    try {
      await apiRequest(`/academic/assignments/${assign.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: nextStatus,
          progress_percent: nextProgress,
        }),
      });
      loadData();
      toast.info(`Marked as ${nextStatus}`);
    } catch (err) {
      toast.error("Failed updating assignment status");
    }
  };

  // Filter assignments
  const filteredAssignments = assignments.filter((a) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "pending") return a.status !== "Completed";
    if (activeFilter === "overdue") return a.is_overdue || a.status === "Overdue";
    if (activeFilter === "completed") return a.status === "Completed";
    return true;
  });

  const pendingCount = assignments.filter((a) => a.status !== "Completed").length;
  const overdueCount = assignments.filter((a) => a.is_overdue || a.status === "Overdue").length;
  const completedCount = assignments.filter((a) => a.status === "Completed").length;

  const filterTabs = [
    { id: "all", label: `All Tasks (${assignments.length})` },
    { id: "pending", label: `Pending (${pendingCount})` },
    { id: "overdue", label: `Overdue (${overdueCount})` },
    { id: "completed", label: `Completed (${completedCount})` },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header & Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Coursework & Deadlines
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Track project deliverables, problem sets, and transparent AI-assisted deadline prioritization.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Button
            variant={showAiPrioritizer ? "primary" : "outline"}
            icon={Sparkles}
            onClick={() => setShowAiPrioritizer(!showAiPrioritizer)}
          >
            {showAiPrioritizer ? "Hide AI Prioritizer" : "AI Smart Prioritizer"}
          </Button>
          <Button variant="primary" icon={Plus} onClick={handleOpenAddModal}>
            Add Assignment
          </Button>
        </div>
      </div>

      {/* AI Smart Prioritizer Deck (When active) */}
      {showAiPrioritizer && (
        <Card
          title="AI-Assisted Deadline Prioritizer"
          subtitle="Transparent multi-factor ranking based on Urgency (35%), Priority (25%), Academic Need (20%), Effort (10%), and Workload (10%)."
          icon={Sparkles}
          style={{ border: "2px solid var(--color-sage)", backgroundColor: "var(--bg-app)" }}
        >
          {prioritizedTasks.length === 0 ? (
            <div style={{ padding: "1rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              All pending coursework is completed! Add new assignments to generate recommendations.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {prioritizedTasks.map((task, idx) => {
                const isExpanded = expandedAiTaskId === task.assignment_id;
                const b = task.score_breakdown;

                return (
                  <div
                    key={task.assignment_id}
                    style={{
                      backgroundColor: "var(--bg-surface)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "6px",
                      padding: "1rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        <div
                          style={{
                            width: "32px",
                            height: "32px",
                            borderRadius: "50%",
                            backgroundColor: idx === 0 ? "var(--color-terracotta)" : "var(--color-sage)",
                            color: "#FFFFFF",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 700,
                            fontSize: "0.9rem",
                          }}
                        >
                          #{idx + 1}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text-main)" }}>
                            {task.title}
                          </div>
                          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                            <span style={{ borderLeft: `3px solid ${task.subject_color}`, paddingLeft: "6px", fontWeight: 600 }}>
                              {task.subject_name}
                            </span>
                            {" "}&bull; Due: {formatDateTime(task.due_date)} ({task.hours_remaining}h left) &bull; Effort: ~{task.estimated_effort_hours}h
                          </div>
                        </div>
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                        <Badge variant={task.priority_score >= 80 ? "danger" : task.priority_score >= 60 ? "warning" : "neutral"}>
                          Score: {task.priority_score}/100
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setExpandedAiTaskId(isExpanded ? null : task.assignment_id)}
                        >
                          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          <span style={{ fontSize: "0.8rem", marginLeft: "4px" }}>
                            {isExpanded ? "Hide Breakdown" : "Score Breakdown"}
                          </span>
                        </Button>
                      </div>
                    </div>

                    {/* AI Transparent Reasoning Banner */}
                    <div
                      style={{
                        marginTop: "0.6rem",
                        padding: "0.6rem 0.85rem",
                        backgroundColor: "var(--bg-app)",
                        borderLeft: "3px solid var(--color-sage)",
                        borderRadius: "4px",
                        fontSize: "0.83rem",
                        color: "var(--text-main)",
                        lineHeight: 1.4,
                      }}
                    >
                      <strong>Recommendation:</strong> {task.recommendation_reason}
                    </div>

                    {/* Expanded Score Factor Breakdown */}
                    {isExpanded && b && (
                      <div
                        style={{
                          marginTop: "0.75rem",
                          paddingTop: "0.75rem",
                          borderTop: "1px solid var(--border-subtle)",
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                          gap: "0.75rem",
                          fontSize: "0.8rem",
                        }}
                      >
                        <div style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem", borderRadius: "4px" }}>
                          <div style={{ color: "var(--text-muted)", fontWeight: 600 }}>Urgency (35%)</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--color-terracotta)" }}>
                            {b.urgency.score}/100
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{b.urgency.detail}</div>
                        </div>

                        <div style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem", borderRadius: "4px" }}>
                          <div style={{ color: "var(--text-muted)", fontWeight: 600 }}>Priority Tier (25%)</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--color-wood)" }}>
                            {b.priority.score}/100
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{b.priority.detail}</div>
                        </div>

                        <div style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem", borderRadius: "4px" }}>
                          <div style={{ color: "var(--text-muted)", fontWeight: 600 }}>Academic Need (20%)</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--color-sage)" }}>
                            {b.academic_importance.score}/100
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{b.academic_importance.detail}</div>
                        </div>

                        <div style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem", borderRadius: "4px" }}>
                          <div style={{ color: "var(--text-muted)", fontWeight: 600 }}>Effort vs Time (10%)</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700 }}>
                            {b.estimated_effort.score}/100
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{b.estimated_effort.detail}</div>
                        </div>

                        <div style={{ backgroundColor: "var(--bg-app)", padding: "0.6rem", borderRadius: "4px" }}>
                          <div style={{ color: "var(--text-muted)", fontWeight: 600 }}>Workload (10%)</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700 }}>
                            {b.workload_pressure.score}/100
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{b.workload_pressure.detail}</div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {/* Filter Tabs */}
      <Tabs tabs={filterTabs} activeTab={activeFilter} onChange={setActiveFilter} />

      {/* Assignments List */}
      {loading ? (
        <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
          Loading assignments...
        </div>
      ) : filteredAssignments.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No Assignments in this category"
          description="Maintain consistent study habits by planning your coursework deliverables ahead."
          action={
            <Button variant="primary" icon={Plus} onClick={handleOpenAddModal}>
              Add New Task
            </Button>
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {filteredAssignments.map((a) => {
            const isDone = a.status === "Completed";
            const isOver = a.is_overdue || a.status === "Overdue";

            return (
              <Card
                key={a.id}
                style={{
                  padding: "1rem 1.25rem",
                  backgroundColor: isDone ? "var(--bg-app)" : "var(--bg-surface)",
                  borderLeft: `5px solid ${isOver ? "var(--color-terracotta)" : isDone ? "var(--color-sage)" : a.subject_color || "var(--color-wood)"}`,
                  opacity: isDone ? 0.75 : 1,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem" }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: "0.9rem", flex: 1, minWidth: "260px" }}>
                    <button
                      onClick={() => handleToggleStatus(a)}
                      title={isDone ? "Mark as In Progress" : "Mark as Completed"}
                      style={{
                        background: "transparent",
                        border: "none",
                        cursor: "pointer",
                        color: isDone ? "var(--color-sage)" : "var(--text-muted)",
                        marginTop: "2px",
                        padding: "0",
                      }}
                    >
                      {isDone ? <CheckSquare size={22} /> : <Square size={22} />}
                    </button>

                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontSize: "1rem",
                          fontWeight: 600,
                          textDecoration: isDone ? "line-through" : "none",
                          color: isDone ? "var(--text-muted)" : "var(--text-main)",
                        }}
                      >
                        {a.title}
                      </div>

                      <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "3px", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                        <span style={{ fontWeight: 600, color: "var(--text-main)" }}>
                          {a.subject_name || "Academic Subject"}
                        </span>
                        <span>&bull;</span>
                        <span>Due: {formatDateTime(a.due_date)}</span>
                        <span>&bull;</span>
                        <span>Effort: {a.estimated_effort_hours || 2.0}h</span>
                        {isOver && (
                          <Badge variant="danger" style={{ fontSize: "0.72rem", padding: "1px 6px" }}>
                            Overdue
                          </Badge>
                        )}
                      </div>

                      {a.description && (
                        <p style={{ fontSize: "0.83rem", color: "var(--text-muted)", marginTop: "6px", lineHeight: 1.4 }}>
                          {a.description}
                        </p>
                      )}

                      {/* Progress Bar */}
                      <div style={{ marginTop: "8px", maxWidth: "320px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "3px" }}>
                          <span>Progress</span>
                          <span>{a.progress_percent || 0}%</span>
                        </div>
                        <ProgressBar
                          value={a.progress_percent || 0}
                          max={100}
                          color={isDone ? "var(--color-sage)" : isOver ? "var(--color-terracotta)" : "var(--color-sand)"}
                          height={5}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <Badge variant={a.priority === "Critical" ? "danger" : a.priority === "High" ? "warning" : "neutral"}>
                      {a.priority} Priority
                    </Badge>
                    <Badge variant={isDone ? "good" : isOver ? "danger" : "neutral"}>
                      {a.status}
                    </Badge>

                    <div style={{ display: "flex", gap: "0.2rem", marginLeft: "0.5rem" }}>
                      <button
                        onClick={() => handleOpenEditModal(a)}
                        title="Edit Task"
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          color: "var(--text-muted)",
                          padding: "4px",
                        }}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleOpenDeleteModal(a)}
                        title="Delete Task"
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          color: "var(--color-terracotta)",
                          padding: "4px",
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* ==================================================== */}
      {/* ADD ASSIGNMENT MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} title="Add Coursework Task">
        <form onSubmit={handleCreateAssignment}>
          <div className="form-group">
            <label className="form-label">Subject *</label>
            <select
              className="form-select"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              required
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name} {s.code ? `(${s.code})` : ""}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Task Title *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Dynamic Programming Problem Set"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description / Deliverables</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="Key submission requirements, rubric guidelines..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1.2 }}>
              <label className="form-label">Due Date & Time *</label>
              <input
                type="datetime-local"
                className="form-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Priority</label>
              <select
                className="form-select"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Estimated Effort (Hours)</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="50"
                className="form-input"
                value={estimatedEffort}
                onChange={(e) => setEstimatedEffort(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Status</label>
              <select
                className="form-select"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Completion Progress: {progressPercent}%</label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              style={{ width: "100%", accentColor: "var(--color-sage)" }}
              value={progressPercent}
              onChange={(e) => setProgressPercent(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Additional Notes / Links (Optional)</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="e.g. GitHub link, lecture slides page 42..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
            <Button variant="outline" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={saving}>
              Save Assignment
            </Button>
          </div>
        </form>
      </Modal>

      {/* ==================================================== */}
      {/* EDIT ASSIGNMENT MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit Coursework Task">
        <form onSubmit={handleUpdateAssignment}>
          <div className="form-group">
            <label className="form-label">Subject *</label>
            <select
              className="form-select"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              required
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name} {s.code ? `(${s.code})` : ""}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Task Title *</label>
            <input
              type="text"
              className="form-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description / Deliverables</label>
            <textarea
              className="form-textarea"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1.2 }}>
              <label className="form-label">Due Date & Time *</label>
              <input
                type="datetime-local"
                className="form-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Priority</label>
              <select
                className="form-select"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Estimated Effort (Hours)</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="50"
                className="form-input"
                value={estimatedEffort}
                onChange={(e) => setEstimatedEffort(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Status</label>
              <select
                className="form-select"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Completion Progress: {progressPercent}%</label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              style={{ width: "100%", accentColor: "var(--color-sage)" }}
              value={progressPercent}
              onChange={(e) => setProgressPercent(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Additional Notes / Links (Optional)</label>
            <textarea
              className="form-textarea"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
            <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={saving}>
              Update Assignment
            </Button>
          </div>
        </form>
      </Modal>

      {/* ==================================================== */}
      {/* DELETE CONFIRMATION MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Assignment Task">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ fontSize: "0.9rem", color: "var(--text-main)", lineHeight: 1.5 }}>
            Are you sure you want to delete the assignment <strong>{selectedAssignment?.title}</strong>?
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              style={{ backgroundColor: "var(--color-terracotta)", borderColor: "var(--color-terracotta)" }}
              onClick={handleDeleteAssignment}
              loading={saving}
            >
              Confirm Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
