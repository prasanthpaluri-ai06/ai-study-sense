import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState, ProgressBar } from "../../components/common/Badge";
import { Modal } from "../../components/common/Modal";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Award,
  Plus,
  TrendingUp,
  Filter,
  Edit2,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Calculator,
  Calendar,
} from "lucide-react";
import { formatDate, getTodayDateString } from "../../utils/dateUtils";

const ASSESSMENT_TYPES = [
  "CAT/internal",
  "Quiz",
  "Assignment",
  "Lab",
  "Midterm",
  "End semester",
  "Other",
];

export default function Marks() {
  const [subjects, setSubjects] = useState([]);
  const [marks, setMarks] = useState([]);
  const [performances, setPerformances] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState("all");
  const [selectedTypeFilter, setSelectedTypeFilter] = useState("all");

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedMark, setSelectedMark] = useState(null);

  // Form Fields
  const [subjectId, setSubjectId] = useState("");
  const [assessmentName, setAssessmentName] = useState("CAT 1");
  const [assessmentType, setAssessmentType] = useState("CAT/internal");
  const [scoredMarks, setScoredMarks] = useState("");
  const [totalMarks, setTotalMarks] = useState("50");
  const [weightage, setWeightage] = useState("20");
  const [notes, setNotes] = useState("");
  const [recordedDate, setRecordedDate] = useState("");
  const [saving, setSaving] = useState(false);

  const toast = useToast();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [subs, mks, perfs] = await Promise.all([
        apiRequest("/academic/subjects").catch(() => []),
        apiRequest("/academic/marks").catch(() => []),
        apiRequest("/academic/marks/performance").catch(() => []),
      ]);
      setSubjects(subs || []);
      setMarks(mks || []);
      setPerformances(perfs || []);
      if (subs.length > 0 && !subjectId) {
        setSubjectId(String(subs[0].id));
      }
    } catch (err) {
      toast.error(err.message || "Failed loading assessment marks");
    } finally {
      setLoading(false);
    }
  }

  // Open Add Modal
  const handleOpenAddModal = () => {
    if (subjects.length === 0) {
      toast.warning("Please register a subject first before adding assessment marks.");
      return;
    }
    setSubjectId(String(subjects[0].id));
    setAssessmentName("CAT 1");
    setAssessmentType("CAT/internal");
    setScoredMarks("");
    setTotalMarks("50");
    setWeightage("20");
    setNotes("");
    setRecordedDate(getTodayDateString());
    setIsAddModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (mark) => {
    setSelectedMark(mark);
    setSubjectId(String(mark.subject_id));
    setAssessmentName(mark.assessment_name || "");
    setAssessmentType(mark.assessment_type || "CAT/internal");
    setScoredMarks(String(mark.scored_marks));
    setTotalMarks(String(mark.total_marks));
    setWeightage(mark.weightage_percent ? String(mark.weightage_percent) : "");
    setNotes(mark.notes || "");
    setRecordedDate(mark.recorded_date ? mark.recorded_date.split("T")[0] : "");
    setIsEditModalOpen(true);
  };

  // Open Delete Modal
  const handleOpenDeleteModal = (mark) => {
    setSelectedMark(mark);
    setIsDeleteModalOpen(true);
  };

  // Create Mark Handler
  const handleAddMark = async (e) => {
    e.preventDefault();
    if (!subjectId || scoredMarks === "" || totalMarks === "") return;
    setSaving(true);
    try {
      await apiRequest("/academic/marks", {
        method: "POST",
        body: JSON.stringify({
          subject_id: parseInt(subjectId),
          assessment_name: assessmentName.trim(),
          assessment_type: assessmentType,
          scored_marks: parseFloat(scoredMarks),
          total_marks: parseFloat(totalMarks),
          weightage_percent: weightage ? parseFloat(weightage) : null,
          notes: notes.trim() || null,
          recorded_date: recordedDate ? new Date(recordedDate).toISOString() : new Date().toISOString(),
        }),
      });
      setIsAddModalOpen(false);
      toast.success("Assessment mark logged successfully");
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed saving assessment mark");
    } finally {
      setSaving(false);
    }
  };

  // Update Mark Handler
  const handleUpdateMark = async (e) => {
    e.preventDefault();
    if (!selectedMark || scoredMarks === "" || totalMarks === "") return;
    setSaving(true);
    try {
      await apiRequest(`/academic/marks/${selectedMark.id}`, {
        method: "PUT",
        body: JSON.stringify({
          assessment_name: assessmentName.trim(),
          assessment_type: assessmentType,
          scored_marks: parseFloat(scoredMarks),
          total_marks: parseFloat(totalMarks),
          weightage_percent: weightage ? parseFloat(weightage) : null,
          notes: notes.trim() || null,
          recorded_date: recordedDate ? new Date(recordedDate).toISOString() : undefined,
        }),
      });
      setIsEditModalOpen(false);
      toast.success("Assessment score updated successfully");
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed updating mark");
    } finally {
      setSaving(false);
    }
  };

  // Delete Mark Handler
  const handleDeleteMark = async () => {
    if (!selectedMark) return;
    setSaving(true);
    try {
      await apiRequest(`/academic/marks/${selectedMark.id}`, {
        method: "DELETE",
      });
      setIsDeleteModalOpen(false);
      toast.info("Assessment score removed");
      loadData();
    } catch (err) {
      toast.error(err.message || "Failed deleting mark");
    } finally {
      setSaving(false);
    }
  };

  // Filter marks
  const filteredMarks = marks.filter((m) => {
    const matchesSubject = selectedSubjectFilter === "all" || m.subject_id === parseInt(selectedSubjectFilter);
    const matchesType = selectedTypeFilter === "all" || m.assessment_type === selectedTypeFilter;
    return matchesSubject && matchesType;
  });

  // Calculate Overall Average & Weighted Score
  const allPercentages = marks.map((m) => m.percentage).filter((p) => p !== undefined);
  const overallAvg = allPercentages.length > 0
    ? (allPercentages.reduce((a, b) => a + b, 0) / allPercentages.length).toFixed(1)
    : "—";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Page Title & Main Action */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
            Assessment Marks & Weighting
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
            Record internal CATs, quizzes, labs, midterms, and end-semesters with configurable weightages.
          </p>
        </div>
        <Button variant="primary" icon={Plus} onClick={handleOpenAddModal}>
          Record Assessment Mark
        </Button>
      </div>

      {/* 3 KPI Summary Cards */}
      <div className="grid-cols-3">
        <Card style={{ borderLeft: "4px solid var(--color-sage)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Overall Average</span>
            <Calculator size={16} color="var(--color-sage)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)" }}>
            {overallAvg !== "—" ? `${overallAvg}%` : "No Marks"}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
            Across {marks.length} recorded assessments
          </div>
        </Card>

        <Card style={{ borderLeft: "4px solid var(--color-terracotta)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Active Courses</span>
            <Layers size={16} color="var(--color-terracotta)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-main)" }}>
            {performances.length} Subjects
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
            {performances.filter((p) => p.performance_status === "Exceeding Target").length} on track for target grade
          </div>
        </Card>

        <Card style={{ borderLeft: "4px solid var(--color-sand)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, textTransform: "uppercase" }}>Performance Trends</span>
            <TrendingUp size={16} color="var(--color-sand)" />
          </div>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)", marginTop: "0.4rem" }}>
            {performances.filter((p) => p.performance_trend === "Improving").length} Improving &bull; {performances.filter((p) => p.performance_trend === "Declining").length} Needs Attention
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            Calculated from sequential test results
          </div>
        </Card>
      </div>

      {/* Subject-Wise Performance Breakdown Grid */}
      {performances.length > 0 && (
        <Card title="Subject Performance & Weighting Breakdown" icon={Layers}>
          <div className="grid-cols-2" style={{ gap: "1rem" }}>
            {performances.map((perf) => {
              const effScore = perf.weighted_average ?? perf.simple_average;
              const hasScore = effScore !== null;
              const target = perf.target_score || 85;
              const isGood = hasScore && effScore >= target;
              const isWarning = hasScore && effScore < target && effScore >= 60;
              const isDanger = hasScore && effScore < 60;

              return (
                <div
                  key={perf.subject_id}
                  style={{
                    backgroundColor: "var(--bg-app)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "6px",
                    padding: "1rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem" }}>
                    <div>
                      <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-main)" }}>
                        {perf.subject_name}
                      </span>
                      {perf.subject_code && (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "6px" }}>
                          ({perf.subject_code})
                        </span>
                      )}
                    </div>
                    <Badge variant={!hasScore ? "neutral" : isGood ? "good" : isWarning ? "warning" : "danger"}>
                      {perf.performance_status}
                    </Badge>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                    <span>Target: <strong>{target}%</strong></span>
                    <span>
                      {hasScore ? (
                        <strong>{effScore}% {perf.weighted_average !== null ? "(Weighted)" : "(Simple Avg)"}</strong>
                      ) : (
                        "No marks recorded"
                      )}
                    </span>
                  </div>

                  <ProgressBar
                    value={effScore || 0}
                    max={100}
                    color={isGood ? "var(--color-sage)" : isWarning ? "var(--color-sand)" : "var(--color-terracotta)"}
                    height={6}
                  />

                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.6rem", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    <span>Weightage configured: <strong>{perf.total_weightage_used}%</strong> / 100%</span>
                    <span>Trend: <strong>{perf.performance_trend}</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Filter and Marks Table Card */}
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            {/* Subject Filter */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Filter size={15} color="var(--text-muted)" />
              <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Subject:
              </span>
              <select
                className="form-select"
                style={{ width: "auto", minWidth: "160px", padding: "0.35rem 0.6rem" }}
                value={selectedSubjectFilter}
                onChange={(e) => setSelectedSubjectFilter(e.target.value)}
              >
                <option value="all">All Subjects</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            {/* Assessment Type Filter */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Type:
              </span>
              <select
                className="form-select"
                style={{ width: "auto", minWidth: "140px", padding: "0.35rem 0.6rem" }}
                value={selectedTypeFilter}
                onChange={(e) => setSelectedTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                {ASSESSMENT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Showing <strong>{filteredMarks.length}</strong> Marks
          </div>
        </div>

        {filteredMarks.length === 0 ? (
          <EmptyState
            icon={Award}
            title="No Assessment Marks Found"
            description="Log your test scores, internal assessments, and exams to monitor academic mastery."
            action={
              <Button variant="primary" icon={Plus} onClick={handleOpenAddModal}>
                Log First Score
              </Button>
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.8rem", textTransform: "uppercase" }}>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Subject</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Assessment</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Type</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Score</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Percentage</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Weightage</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Contribution</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Date</th>
                  <th style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredMarks.map((m) => {
                  const pct = m.percentage;
                  let badge = "good";
                  if (pct < 60) badge = "danger";
                  else if (pct < 75) badge = "warning";

                  return (
                    <tr key={m.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600 }}>
                        <span style={{ borderLeft: `3px solid ${m.subject_color || "var(--color-sage)"}`, paddingLeft: "6px" }}>
                          {m.subject_name || "Course"}
                        </span>
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: 500 }}>
                        {m.assessment_name}
                        {m.notes && (
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                            {m.notes}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                        <span style={{ backgroundColor: "var(--bg-surface-soft)", padding: "2px 6px", borderRadius: "4px" }}>
                          {m.assessment_type}
                        </span>
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem" }}>
                        {m.scored_marks} / {m.total_marks}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem" }}>
                        <Badge variant={badge}>{pct}%</Badge>
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-muted)" }}>
                        {m.weightage_percent ? `${m.weightage_percent}%` : "—"}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600, color: "var(--color-sage)" }}>
                        {m.weighted_contribution !== null && m.weighted_contribution !== undefined
                          ? `+${m.weighted_contribution}%`
                          : "—"}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-muted)", fontSize: "0.82rem" }}>
                        {formatDate(m.recorded_date)}
                      </td>
                      <td style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "0.3rem" }}>
                          <button
                            onClick={() => handleOpenEditModal(m)}
                            title="Edit Mark"
                            style={{
                              background: "transparent",
                              border: "none",
                              cursor: "pointer",
                              color: "var(--text-muted)",
                              padding: "4px",
                            }}
                          >
                            <Edit2 size={15} />
                          </button>
                          <button
                            onClick={() => handleOpenDeleteModal(m)}
                            title="Delete Mark"
                            style={{
                              background: "transparent",
                              border: "none",
                              cursor: "pointer",
                              color: "var(--color-terracotta)",
                              padding: "4px",
                            }}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ==================================================== */}
      {/* RECORD MARK MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} title="Record Assessment Mark">
        <form onSubmit={handleAddMark}>
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

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1.2 }}>
              <label className="form-label">Assessment Title *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Continuous Assessment Test 1"
                value={assessmentName}
                onChange={(e) => setAssessmentName(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Assessment Type</label>
              <select
                className="form-select"
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value)}
              >
                {ASSESSMENT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Scored Marks *</label>
              <input
                type="number"
                step="0.25"
                className="form-input"
                placeholder="42"
                value={scoredMarks}
                onChange={(e) => setScoredMarks(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Total Max Marks *</label>
              <input
                type="number"
                step="1"
                className="form-input"
                value={totalMarks}
                onChange={(e) => setTotalMarks(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Weightage % (Configurable)</label>
              <input
                type="number"
                step="1"
                min="0"
                max="100"
                className="form-input"
                placeholder="e.g. 20"
                value={weightage}
                onChange={(e) => setWeightage(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Recorded Date</label>
            <input
              type="date"
              className="form-input"
              value={recordedDate}
              onChange={(e) => setRecordedDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Notes / Topics Evaluated (Optional)</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="e.g. Dynamic programming, Binary Search trees..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
            <Button variant="outline" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={saving}>
              Save Assessment Mark
            </Button>
          </div>
        </form>
      </Modal>

      {/* ==================================================== */}
      {/* EDIT MARK MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit Assessment Score">
        <form onSubmit={handleUpdateMark}>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1.2 }}>
              <label className="form-label">Assessment Title *</label>
              <input
                type="text"
                className="form-input"
                value={assessmentName}
                onChange={(e) => setAssessmentName(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Assessment Type</label>
              <select
                className="form-select"
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value)}
              >
                {ASSESSMENT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Scored Marks *</label>
              <input
                type="number"
                step="0.25"
                className="form-input"
                value={scoredMarks}
                onChange={(e) => setScoredMarks(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Total Max Marks *</label>
              <input
                type="number"
                step="1"
                className="form-input"
                value={totalMarks}
                onChange={(e) => setTotalMarks(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Weightage %</label>
              <input
                type="number"
                step="1"
                min="0"
                max="100"
                className="form-input"
                value={weightage}
                onChange={(e) => setWeightage(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Recorded Date</label>
            <input
              type="date"
              className="form-input"
              value={recordedDate}
              onChange={(e) => setRecordedDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Notes (Optional)</label>
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
              Update Score
            </Button>
          </div>
        </form>
      </Modal>

      {/* ==================================================== */}
      {/* DELETE CONFIRMATION MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Assessment Mark">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ fontSize: "0.9rem", color: "var(--text-main)", lineHeight: 1.5 }}>
            Are you sure you want to delete the score record for <strong>{selectedMark?.assessment_name}</strong> ({selectedMark?.scored_marks}/{selectedMark?.total_marks})?
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              style={{ backgroundColor: "var(--color-terracotta)", borderColor: "var(--color-terracotta)" }}
              onClick={handleDeleteMark}
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
