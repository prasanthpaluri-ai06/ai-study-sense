import React, { useEffect, useState, useRef, useMemo } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState, ProgressBar } from "../../components/common/Badge";
import { Modal } from "../../components/common/Modal";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  GraduationCap,
  Plus,
  Edit2,
  Trash2,
  Eye,
  BookOpen,
  Target,
  Award,
  Calendar,
  Layers,
  CheckCircle2,
  AlertCircle,
  Filter,
  UploadCloud,
  FileText,
  Sparkles,
  ChevronDown,
  ChevronRight,
  CheckSquare,
  Square,
  RefreshCw,
  Clock,
  ArrowLeft,
  X,
  ListChecks,
  Search,
  Check,
} from "lucide-react";

export default function Subjects() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [semesterFilter, setSemesterFilter] = useState("all");

  // Modal States
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isSyllabusModalOpen, setIsSyllabusModalOpen] = useState(false);

  // Selected & Form Data
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [subjectDetail, setSubjectDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Essential Subject Registration Form Fields
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [semester, setSemester] = useState("Semester 1");
  const [credits, setCredits] = useState("3.0");
  const [targetScore, setTargetScore] = useState("85");
  const [color, setColor] = useState("#5A6E52");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  // Add Subject Workflow: Step 1 = Details & File, Step 2 = Extraction Preview
  const [addStep, setAddStep] = useState(1);
  const [syllabusMode, setSyllabusMode] = useState("file"); // "file" | "text"
  const [syllabusFile, setSyllabusFile] = useState(null);
  const [syllabusText, setSyllabusText] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [expandedPreviewModules, setExpandedPreviewModules] = useState({});
  const [previewSearchQuery, setPreviewSearchQuery] = useState("");
  const fileInputRef = useRef(null);

  // Interactive Syllabus Checklist Modal State
  const [syllabusSubject, setSyllabusSubject] = useState(null);
  const [syllabusRoadmap, setSyllabusRoadmap] = useState(null);
  const [syllabusLoading, setSyllabusLoading] = useState(false);
  const [expandedChecklistModules, setExpandedChecklistModules] = useState({});
  const [checklistStatusFilter, setChecklistStatusFilter] = useState("all");
  const [checklistSearchQuery, setChecklistSearchQuery] = useState("");
  const [isReplacingSyllabus, setIsReplacingSyllabus] = useState(false);
  const [replaceFile, setReplaceFile] = useState(null);
  const [replaceLoading, setReplaceLoading] = useState(false);
  const replaceFileInputRef = useRef(null);

  const toast = useToast();

  useEffect(() => {
    loadSubjects();
  }, [semesterFilter]);

  async function loadSubjects() {
    setLoading(true);
    try {
      const url =
        semesterFilter !== "all"
          ? `/academic/subjects?semester=${encodeURIComponent(semesterFilter)}`
          : "/academic/subjects";
      const data = await apiRequest(url);
      setSubjects(data || []);
    } catch (err) {
      toast.error(err.message || "Failed loading subjects");
    } finally {
      setLoading(false);
    }
  }

  // Open Simplified Add Modal
  const handleOpenAddModal = () => {
    setName("");
    setCode("");
    setSemester("Semester 1");
    setCredits("3.0");
    setColor("#5A6E52");
    setDescription("");
    setAddStep(1);
    setSyllabusMode("file");
    setSyllabusFile(null);
    setSyllabusText("");
    setExtracting(false);
    setExtractionError(null);
    setPreviewData(null);
    setExpandedPreviewModules({});
    setPreviewSearchQuery("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    setIsAddModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (sub, e) => {
    e?.stopPropagation();
    setSelectedSubject(sub);
    setName(sub.name || "");
    setCode(sub.code || "");
    setSemester(sub.semester || "Semester 1");
    setCredits(String(sub.credits || "3.0"));
    setTargetScore(String(sub.target_score || "85"));
    setColor(sub.color || "#5A6E52");
    setDescription(sub.description || "");
    setIsEditModalOpen(true);
  };

  // Open View Detail Modal
  const handleOpenDetailModal = async (sub) => {
    setSelectedSubject(sub);
    setIsDetailModalOpen(true);
    setDetailLoading(true);
    try {
      const detail = await apiRequest(`/academic/subjects/${sub.id}`);
      setSubjectDetail(detail);
    } catch (err) {
      toast.error("Failed loading subject details");
    } finally {
      setDetailLoading(false);
    }
  };

  // Open Delete Modal
  const handleOpenDeleteModal = (sub, e) => {
    e?.stopPropagation();
    setSelectedSubject(sub);
    setIsDeleteModalOpen(true);
  };

  // Step 1 -> Extract & Preview Syllabus
  const handleExtractSyllabusPreview = async (e) => {
    e?.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter a subject name first.");
      return;
    }

    if (syllabusMode === "file") {
      if (!syllabusFile) {
        toast.error("Please select a syllabus document (PDF, DOCX, TXT, or image).");
        return;
      }
      if (syllabusFile.size > 15 * 1024 * 1024) {
        toast.error("File exceeds 15 MB limit.");
        return;
      }
    } else {
      if (!syllabusText.trim()) {
        toast.error("Please paste your syllabus text.");
        return;
      }
    }

    setExtracting(true);
    setExtractionError(null);

    try {
      const formData = new FormData();
      if (syllabusMode === "file") {
        formData.append("file", syllabusFile);
      } else {
        formData.append("content_text", syllabusText.trim());
      }

      const preview = await apiRequest("/syllabus/extract-preview", {
        method: "POST",
        body: formData,
      });

      setPreviewData(preview);
      // Expand all modules by default in preview
      const initialExp = {};
      (preview.modules || []).forEach((m) => {
        initialExp[m.module_number] = true;
      });
      setExpandedPreviewModules(initialExp);
      setAddStep(2);
      toast.success(
        `Extracted ${preview.topics_count} topics across ${preview.modules_count} modules!`
      );
    } catch (err) {
      const errMsg = err.message || "Failed to extract syllabus. Please verify file format.";
      setExtractionError(errMsg);
      toast.error(errMsg);
    } finally {
      setExtracting(false);
    }
  };

  // Step 2 -> Confirm & Register Subject with Reviewed Syllabus
  const handleConfirmCreateSubject = async () => {
    if (!previewData || !previewData.modules || previewData.modules.length === 0) {
      toast.error("No extracted modules available to save.");
      return;
    }

    setSaving(true);
    try {
      const created = await apiRequest("/academic/subjects/with-syllabus", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          code: code.trim() || null,
          semester: semester.trim(),
          credits: parseFloat(credits) || 3.0,
          color,
          description: description.trim() || null,
          syllabus_title: `${name.trim()} Syllabus`,
          file_name: syllabusMode === "file" ? syllabusFile?.name : "Pasted Text",
          modules: previewData.modules,
        }),
      });

      setIsAddModalOpen(false);
      toast.success(`Subject '${created.name}' registered with syllabus checklist!`);
      await loadSubjects();

      // Open checklist directly for the new subject
      handleOpenSyllabusChecklist(created);
    } catch (err) {
      toast.error(err.message || "Failed creating subject with syllabus");
    } finally {
      setSaving(false);
    }
  };

  // Update Subject Handler (Edit Metadata)
  const handleUpdateSubject = async (e) => {
    e.preventDefault();
    if (!selectedSubject || !name.trim()) return;
    setSaving(true);
    try {
      await apiRequest(`/academic/subjects/${selectedSubject.id}`, {
        method: "PUT",
        body: JSON.stringify({
          name: name.trim(),
          code: code.trim() || null,
          semester: semester.trim(),
          credits: parseFloat(credits) || 3.0,
          target_score: parseFloat(targetScore) || 85.0,
          color,
          description: description.trim() || null,
        }),
      });
      setIsEditModalOpen(false);
      toast.success("Subject updated successfully");
      loadSubjects();
    } catch (err) {
      toast.error(err.message || "Failed updating subject");
    } finally {
      setSaving(false);
    }
  };

  // Delete Subject Handler
  const handleDeleteSubject = async () => {
    if (!selectedSubject) return;
    setSaving(true);
    try {
      await apiRequest(`/academic/subjects/${selectedSubject.id}`, {
        method: "DELETE",
      });
      setIsDeleteModalOpen(false);
      toast.info(`Subject '${selectedSubject.name}' deleted`);
      loadSubjects();
    } catch (err) {
      toast.error(err.message || "Failed deleting subject");
    } finally {
      setSaving(false);
    }
  };

  // Open Interactive Syllabus Checklist Modal
  const handleOpenSyllabusChecklist = async (sub, e) => {
    e?.stopPropagation();
    setSyllabusSubject(sub);
    setIsSyllabusModalOpen(true);
    setSyllabusLoading(true);
    setIsReplacingSyllabus(false);
    setReplaceFile(null);
    setChecklistStatusFilter("all");
    setChecklistSearchQuery("");

    try {
      const roadmaps = await apiRequest(`/syllabus/roadmaps?subject_id=${sub.id}`);
      if (roadmaps && roadmaps.length > 0) {
        setSyllabusRoadmap(roadmaps[0]);
        // Expand all modules by default
        const initialExp = {};
        roadmaps[0].modules.forEach((m) => {
          initialExp[m.id] = true;
        });
        setExpandedChecklistModules(initialExp);
      } else {
        setSyllabusRoadmap(null);
      }
    } catch (err) {
      toast.error(err.message || "Failed loading syllabus checklist");
      setSyllabusRoadmap(null);
    } finally {
      setSyllabusLoading(false);
    }
  };

  // Toggle Topic Completed Checkbox (Completed <-> Not Started)
  const handleToggleTopicComplete = async (topicId, currentStatus) => {
    const newStatus = currentStatus === "Completed" ? "Not Started" : "Completed";
    await handleUpdateTopicStatus(topicId, newStatus);
  };

  // Update Topic Status Dropdown (4 states: Not Started, In Progress, Completed, Needs Revision)
  const handleUpdateTopicStatus = async (topicId, newStatus) => {
    try {
      await apiRequest(`/syllabus/topics/${topicId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });

      // Optimistically update local checklist state
      setSyllabusRoadmap((prev) => {
        if (!prev) return prev;
        let totalComp = 0;
        let totalCount = 0;
        let inProg = 0;
        let needsRev = 0;
        let notStarted = 0;

        const newModules = prev.modules.map((mod) => {
          let modComp = 0;
          const newTopics = mod.topics.map((t) => {
            totalCount++;
            const curStatus = t.id === topicId ? newStatus : t.status;
            const isComp = curStatus === "Completed";
            if (isComp) {
              totalComp++;
              modComp++;
            } else if (curStatus === "In Progress") {
              inProg++;
            } else if (curStatus === "Needs Revision") {
              needsRev++;
            } else {
              notStarted++;
            }
            return t.id === topicId
              ? { ...t, status: newStatus, is_completed: isComp }
              : t;
          });

          const modPct =
            mod.topics.length > 0 ? Math.round((modComp / mod.topics.length) * 100) : 0;
          return {
            ...mod,
            completed_count: modComp,
            progress_percent: modPct,
            topics: newTopics,
          };
        });

        const overallPct = totalCount > 0 ? Math.round((totalComp / totalCount) * 100) : 0;

        return {
          ...prev,
          completed_topics: totalComp,
          total_topics: totalCount,
          in_progress_topics: inProg,
          needs_revision_topics: needsRev,
          not_started_topics: notStarted,
          overall_progress_percent: overallPct,
          modules: newModules,
        };
      });

      // Update subject in parent listing
      setSubjects((prev) =>
        prev.map((s) => {
          if (s.id === syllabusSubject?.id) {
            return {
              ...s,
              has_syllabus: true,
              syllabus_completed_topics:
                newStatus === "Completed"
                  ? (s.syllabus_completed_topics || 0) + 1
                  : Math.max(0, (s.syllabus_completed_topics || 1) - 1),
            };
          }
          return s;
        })
      );
    } catch (err) {
      toast.error(err.message || "Failed updating topic status");
    }
  };

  // Replace Syllabus Document for Current Subject
  const handleReplaceSyllabus = async (e) => {
    e.preventDefault();
    if (!replaceFile || !syllabusSubject) {
      toast.error("Please select a replacement syllabus document.");
      return;
    }

    setReplaceLoading(true);
    try {
      const formData = new FormData();
      formData.append("subject_id", syllabusSubject.id);
      formData.append("file", replaceFile);

      const updatedRoadmap = await apiRequest("/syllabus/upload/file", {
        method: "POST",
        body: formData,
      });

      toast.success(
        `Syllabus updated! Preserved progress on matching topics (${updatedRoadmap.completed_topics} completed).`
      );
      setSyllabusRoadmap(updatedRoadmap);
      setIsReplacingSyllabus(false);
      setReplaceFile(null);
      if (replaceFileInputRef.current) replaceFileInputRef.current.value = "";
      loadSubjects();
    } catch (err) {
      toast.error(err.message || "Failed replacing syllabus document");
    } finally {
      setReplaceLoading(false);
    }
  };

  // Toggle Module Accordion Expansion in Checklist
  const toggleChecklistModule = (moduleId) => {
    setExpandedChecklistModules((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }));
  };

  // Toggle Module Accordion Expansion in Preview
  const togglePreviewModule = (moduleNum) => {
    setExpandedPreviewModules((prev) => ({
      ...prev,
      [moduleNum]: !prev[moduleNum],
    }));
  };

  // Expand / Collapse all in preview
  const handleToggleAllPreviewModules = (expandAll) => {
    const newState = {};
    if (expandAll) {
      (previewData?.modules || []).forEach((m) => {
        newState[m.module_number] = true;
      });
    }
    setExpandedPreviewModules(newState);
  };

  // Expand / Collapse all in checklist
  const handleToggleAllChecklistModules = (expandAll) => {
    const newState = {};
    if (expandAll) {
      (syllabusRoadmap?.modules || []).forEach((m) => {
        newState[m.id] = true;
      });
    }
    setExpandedChecklistModules(newState);
  };

  // Collect unique semesters for filter
  const availableSemesters = Array.from(new Set(subjects.map((s) => s.semester).filter(Boolean)));

  // Filtered preview modules based on search query
  const filteredPreviewModules = useMemo(() => {
    if (!previewData?.modules) return [];
    if (!previewSearchQuery.trim()) return previewData.modules;
    const q = previewSearchQuery.toLowerCase();
    return previewData.modules
      .map((mod) => {
        const modMatches = mod.name.toLowerCase().includes(q);
        const matchedTopics = mod.topics.filter(
          (t) =>
            t.title.toLowerCase().includes(q) ||
            (t.subtopics && t.subtopics.some((st) => st.toLowerCase().includes(q)))
        );
        if (modMatches || matchedTopics.length > 0) {
          return {
            ...mod,
            topics: modMatches ? mod.topics : matchedTopics,
          };
        }
        return null;
      })
      .filter(Boolean);
  }, [previewData, previewSearchQuery]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header Bar */}
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
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "var(--text-main)" }}>
            Academic Subjects & Syllabi
          </h2>
          <p style={{ margin: "4px 0 0 0", color: "var(--text-muted)", fontSize: "0.88rem" }}>
            Manage registered courses, track syllabus checklist progress, and master course modules.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          {availableSemesters.length > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Filter size={16} color="var(--text-muted)" />
              <select
                className="form-select"
                style={{ width: "auto", fontSize: "0.85rem", padding: "6px 12px" }}
                value={semesterFilter}
                onChange={(e) => setSemesterFilter(e.target.value)}
              >
                <option value="all">All Semesters</option>
                {availableSemesters.map((sem) => (
                  <option key={sem} value={sem}>
                    {sem}
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button
            variant="primary"
            onClick={handleOpenAddModal}
            style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
          >
            <Plus size={16} /> Register Subject
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
          Loading registered course subjects...
        </div>
      ) : subjects.length === 0 ? (
        <Card>
          <EmptyState
            icon={GraduationCap}
            title="No Academic Subjects Registered"
            description="Register your course subjects along with their syllabus document to unlock module-wise checklists and AI-driven mastery tracking."
            action={
              <Button
                variant="primary"
                onClick={handleOpenAddModal}
                style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
              >
                <Plus size={16} /> Register Your First Subject
              </Button>
            }
          />
        </Card>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "1.25rem",
          }}
        >
          {subjects.map((sub) => {
            const hasMarks = sub.average_score !== null;
            const avg = sub.weighted_score ?? sub.average_score;
            const target = sub.target_score || 85;
            const isOnTrack = hasMarks && avg >= target - 5;
            const isCritical = hasMarks && avg < 50;

            return (
              <Card
                key={sub.id}
                style={{
                  cursor: "pointer",
                  transition: "transform 0.15s ease, box-shadow 0.15s ease",
                  borderLeft: `5px solid ${sub.color || "#5A6E52"}`,
                }}
                onClick={() => handleOpenDetailModal(sub)}
              >
                {/* Subject Header */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "0.6rem",
                  }}
                >
                  <div>
                    <h3
                      style={{
                        margin: 0,
                        fontSize: "1.1rem",
                        fontWeight: 700,
                        color: "var(--text-main)",
                        lineHeight: 1.3,
                      }}
                    >
                      {sub.name}
                    </h3>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        marginTop: "4px",
                        flexWrap: "wrap",
                      }}
                    >
                      {sub.code && (
                        <span
                          style={{
                            fontSize: "0.75rem",
                            border: "1px solid var(--border-color)",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            color: "var(--text-muted)",
                            fontWeight: 600,
                          }}
                        >
                          {sub.code}
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: "0.75rem",
                          backgroundColor: "var(--bg-surface-soft)",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          color: "var(--text-muted)",
                        }}
                      >
                        {sub.semester || "Semester 1"}
                      </span>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        &bull; {sub.credits || 3.0} Credits
                      </span>
                    </div>
                  </div>

                  <Badge
                    variant={
                      !hasMarks ? "neutral" : isOnTrack ? "good" : isCritical ? "danger" : "warning"
                    }
                  >
                    {hasMarks ? `${avg}% ${sub.weighted_score !== null ? "Wtd" : "Avg"}` : "No Marks"}
                  </Badge>
                </div>

                {/* Description if present */}
                {sub.description && (
                  <p
                    style={{
                      fontSize: "0.82rem",
                      color: "var(--text-muted)",
                      marginBottom: "0.6rem",
                      lineHeight: 1.4,
                    }}
                  >
                    {sub.description.length > 90
                      ? `${sub.description.substring(0, 90)}...`
                      : sub.description}
                  </p>
                )}

                {/* Interactive Syllabus Section & Button on Card */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    backgroundColor: "var(--bg-app)",
                    padding: "0.55rem 0.75rem",
                    borderRadius: "6px",
                    marginTop: "0.5rem",
                    marginBottom: "0.5rem",
                    border: "1px solid var(--border-subtle)",
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem" }}>
                    <BookOpen
                      size={16}
                      color={sub.has_syllabus ? "var(--color-sage)" : "var(--text-muted)"}
                    />
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--text-main)" }}>
                        {sub.has_syllabus ? "Syllabus Checklist" : "No Syllabus Attached"}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        {sub.has_syllabus
                          ? `${sub.syllabus_completed_topics || 0} / ${
                              sub.syllabus_total_topics || 0
                            } Topics (${sub.syllabus_progress_percent || 0}%)`
                          : "Upload syllabus to track"}
                      </div>
                    </div>
                  </div>

                  <Button
                    variant={sub.has_syllabus ? "outline" : "primary"}
                    size="sm"
                    onClick={(e) => handleOpenSyllabusChecklist(sub, e)}
                    style={{
                      fontSize: "0.75rem",
                      padding: "4px 9px",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.3rem",
                    }}
                  >
                    <ListChecks size={13} />
                    {sub.has_syllabus ? "Syllabus" : "+ Add"}
                  </Button>
                </div>

                {/* Target vs Progress */}
                <div style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "0.8rem",
                      color: "var(--text-muted)",
                      marginBottom: "4px",
                    }}
                  >
                    <span>
                      Target: <strong>{target}%</strong>
                    </span>
                    <span>{hasMarks ? `Current: ${avg}%` : "Not evaluated"}</span>
                  </div>
                  <ProgressBar
                    value={avg || 0}
                    max={100}
                    color={
                      isOnTrack
                        ? "var(--color-sage)"
                        : isCritical
                        ? "var(--color-terracotta)"
                        : "var(--color-sand)"
                    }
                    height={6}
                  />
                </div>

                {/* Card Footer with Counts and Action Buttons */}
                <div
                  style={{
                    borderTop: "1px solid var(--border-subtle)",
                    paddingTop: "0.6rem",
                    marginTop: "0.6rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                  }}
                >
                  <div style={{ display: "flex", gap: "0.75rem" }}>
                    <span>{sub.marks_count || 0} Marks</span>
                    <span>&bull;</span>
                    <span>{sub.assignments_count || 0} Tasks</span>
                  </div>

                  <div style={{ display: "flex", gap: "0.3rem" }}>
                    <button
                      onClick={(e) => handleOpenEditModal(sub, e)}
                      title="Edit Subject"
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
                      onClick={(e) => handleOpenDeleteModal(sub, e)}
                      title="Delete Subject"
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
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* ==================================================== */}
      {/* SIMPLIFIED ADD SUBJECT & SYLLABUS REGISTRATION MODAL */}
      {/* ==================================================== */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title={addStep === 1 ? "Register Course Subject with Syllabus" : "Review Extracted Syllabus"}
        maxWidth={addStep === 1 ? "680px" : "820px"}
      >
        {addStep === 1 ? (
          <form onSubmit={handleExtractSyllabusPreview}>
            {/* Step 1: Essential Subject Information */}
            <div
              style={{
                backgroundColor: "var(--bg-app)",
                padding: "1rem",
                borderRadius: "8px",
                marginBottom: "1rem",
                border: "1px solid var(--border-color)",
              }}
            >
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "var(--color-sage)",
                  marginBottom: "0.75rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                1. Essential Course Information
              </div>

              <div className="form-group" style={{ marginBottom: "0.85rem" }}>
                <label className="form-label">Subject / Course Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Software Engineering"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <div className="form-group" style={{ flex: 1, minWidth: "140px", marginBottom: "0.85rem" }}>
                  <label className="form-label">Course Code</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. CS301"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                </div>
                <div className="form-group" style={{ flex: 1, minWidth: "140px", marginBottom: "0.85rem" }}>
                  <label className="form-label">Semester Association</label>
                  <select
                    className="form-select"
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                  >
                    {[
                      "Semester 1",
                      "Semester 2",
                      "Semester 3",
                      "Semester 4",
                      "Semester 5",
                      "Semester 6",
                      "Semester 7",
                      "Semester 8",
                    ].map((sem) => (
                      <option key={sem} value={sem}>
                        {sem}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group" style={{ width: "110px", marginBottom: "0.85rem" }}>
                  <label className="form-label">Credits</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="10"
                    className="form-input"
                    value={credits}
                    onChange={(e) => setCredits(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Theme Color</label>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  {[
                    { label: "Sage Olive", val: "#5A6E52" },
                    { label: "Terracotta", val: "#BA644A" },
                    { label: "Muted Wood", val: "#756254" },
                    { label: "Warm Stone", val: "#8A7968" },
                    { label: "Slate Blue", val: "#4A6B82" },
                  ].map((c) => (
                    <button
                      type="button"
                      key={c.val}
                      onClick={() => setColor(c.val)}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        backgroundColor: c.val,
                        border:
                          color === c.val ? "3px solid var(--text-main)" : "2px solid transparent",
                        cursor: "pointer",
                      }}
                      title={c.label}
                    />
                  ))}
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                    Selected: {color}
                  </span>
                </div>
              </div>
            </div>

            {/* Step 2: Mandatory Syllabus Upload Section */}
            <div
              style={{
                backgroundColor: "var(--bg-app)",
                padding: "1rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.75rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    color: "var(--color-sage)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  2. Syllabus Document Upload (Required) *
                </div>

                {/* Mode Selector */}
                <div
                  style={{
                    display: "flex",
                    backgroundColor: "var(--bg-surface-soft)",
                    borderRadius: "6px",
                    padding: "2px",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setSyllabusMode("file")}
                    style={{
                      background: syllabusMode === "file" ? "var(--bg-surface)" : "transparent",
                      border: "none",
                      borderRadius: "4px",
                      padding: "4px 10px",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      fontWeight: syllabusMode === "file" ? 700 : 500,
                      color: syllabusMode === "file" ? "var(--text-main)" : "var(--text-muted)",
                      boxShadow: syllabusMode === "file" ? "0 1px 2px rgba(0,0,0,0.06)" : "none",
                    }}
                  >
                    Upload Document
                  </button>
                  <button
                    type="button"
                    onClick={() => setSyllabusMode("text")}
                    style={{
                      background: syllabusMode === "text" ? "var(--bg-surface)" : "transparent",
                      border: "none",
                      borderRadius: "4px",
                      padding: "4px 10px",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      fontWeight: syllabusMode === "text" ? 700 : 500,
                      color: syllabusMode === "text" ? "var(--text-main)" : "var(--text-muted)",
                      boxShadow: syllabusMode === "text" ? "0 1px 2px rgba(0,0,0,0.06)" : "none",
                    }}
                  >
                    Paste Text
                  </button>
                </div>
              </div>

              {syllabusMode === "file" ? (
                <div>
                  <div
                    style={{
                      border: "2px dashed var(--border-color)",
                      borderRadius: "8px",
                      padding: "1.75rem 1.25rem",
                      textAlign: "center",
                      backgroundColor: "var(--bg-surface-soft)",
                      cursor: "pointer",
                      transition: "border-color 0.2s ease, background 0.2s ease",
                    }}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <UploadCloud size={36} color="var(--color-sage)" style={{ margin: "0 auto 0.5rem auto" }} />
                    <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-main)" }}>
                      {syllabusFile ? syllabusFile.name : "Click to select syllabus document"}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
                      PDF, DOCX, TXT, Markdown, PNG, JPG (Up to 15 MB)
                    </div>
                    {syllabusFile && (
                      <div style={{ marginTop: "0.75rem" }}>
                        <Badge variant="good">
                          Selected: {(syllabusFile.size / 1024).toFixed(0)} KB &bull; Ready to extract
                        </Badge>
                      </div>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.webp"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setSyllabusFile(e.target.files[0]);
                        setExtractionError(null);
                      }
                    }}
                  />
                </div>
              ) : (
                <div>
                  <textarea
                    className="form-textarea"
                    rows={6}
                    placeholder={`Paste syllabus structure here, e.g.:\n\nModule 1: Overview of Software Engineering\n- Software Engineering Process Models\n- Agile Software Development\n- Requirement Engineering\n\nModule 2: Software Design & Architecture\n- Architectural Styles\n- Component-Level Design`}
                    value={syllabusText}
                    onChange={(e) => {
                      setSyllabusText(e.target.value);
                      setExtractionError(null);
                    }}
                  />
                </div>
              )}

              {/* Extraction error banner if any */}
              {extractionError && (
                <div
                  style={{
                    marginTop: "0.85rem",
                    padding: "0.75rem 1rem",
                    backgroundColor: "var(--status-bad-bg)",
                    border: "1px solid var(--status-bad-border)",
                    borderRadius: "6px",
                    color: "var(--status-bad-text)",
                    fontSize: "0.84rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.6rem",
                  }}
                >
                  <AlertCircle size={18} style={{ flexShrink: 0 }} />
                  <span>{extractionError}</span>
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.25rem" }}>
              <Button variant="outline" type="button" onClick={() => setIsAddModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                type="submit"
                loading={extracting}
                style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
              >
                <Sparkles size={16} /> Extract & Preview Syllabus
              </Button>
            </div>
          </form>
        ) : (
          /* Step 2: Extraction Preview & Confirmation */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
            {/* Header Validation Banner */}
            <div
              style={{
                backgroundColor: "rgba(90, 110, 82, 0.08)",
                border: "1px solid rgba(90, 110, 82, 0.25)",
                borderRadius: "8px",
                padding: "1rem 1.25rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "0.75rem",
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--text-main)" }}>
                  Extracted Curriculum for: {name}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "3px" }}>
                  <strong>{previewData?.modules_count || 0} Modules</strong> &bull;{" "}
                  <strong>{previewData?.topics_count || 0} Topics</strong> &bull;{" "}
                  <strong>{previewData?.subtopics_count || 0} Subtopics</strong> Identified
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  backgroundColor: "rgba(90, 110, 82, 0.15)",
                  color: "var(--color-sage)",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  fontWeight: 700,
                  fontSize: "0.82rem",
                }}
              >
                <CheckCircle2 size={16} /> Extraction Validated
              </div>
            </div>

            {/* Controls Bar: Search & Expand/Collapse */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "0.75rem",
                flexWrap: "wrap",
              }}
            >
              {/* Search input */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  backgroundColor: "var(--bg-app)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "6px",
                  padding: "4px 10px",
                  flex: 1,
                  maxWidth: "340px",
                }}
              >
                <Search size={15} color="var(--text-muted)" />
                <input
                  type="text"
                  placeholder="Search extracted modules & topics..."
                  value={previewSearchQuery}
                  onChange={(e) => setPreviewSearchQuery(e.target.value)}
                  style={{
                    border: "none",
                    background: "transparent",
                    outline: "none",
                    fontSize: "0.82rem",
                    width: "100%",
                    color: "var(--text-main)",
                  }}
                />
                {previewSearchQuery && (
                  <button
                    onClick={() => setPreviewSearchQuery("")}
                    style={{ background: "transparent", border: "none", cursor: "pointer", padding: 0 }}
                  >
                    <X size={14} color="var(--text-muted)" />
                  </button>
                )}
              </div>

              {/* Expand / Collapse All Controls */}
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleAllPreviewModules(true)}
                  style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                >
                  Expand All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleAllPreviewModules(false)}
                  style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                >
                  Collapse All
                </Button>
              </div>
            </div>

            {/* Modules Accordion List — Fixed with flexShrink: 0 and smooth scrolling */}
            <div
              style={{
                maxHeight: "52vh",
                minHeight: "340px",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                paddingRight: "6px",
              }}
            >
              {filteredPreviewModules.length === 0 ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                  No modules match your search query.
                </div>
              ) : (
                filteredPreviewModules.map((m) => {
                  const isExp = expandedPreviewModules[m.module_number];
                  return (
                    <div
                      key={m.module_number}
                      style={{
                        border: "1px solid var(--border-color)",
                        borderRadius: "8px",
                        backgroundColor: "var(--bg-app)",
                        overflow: "hidden",
                        flexShrink: 0, // CRITICAL: prevents flexbox squishing!
                        width: "100%",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
                      }}
                    >
                      {/* Module Header */}
                      <div
                        style={{
                          padding: "0.75rem 1rem",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          cursor: "pointer",
                          backgroundColor: "var(--bg-surface-soft)",
                          userSelect: "none",
                        }}
                        onClick={() => togglePreviewModule(m.module_number)}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                          {isExp ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                          <span
                            style={{
                              backgroundColor: "var(--bg-app)",
                              border: "1px solid var(--border-color)",
                              borderRadius: "4px",
                              padding: "2px 7px",
                              fontSize: "0.75rem",
                              fontWeight: 700,
                              color: "var(--color-sage)",
                            }}
                          >
                            #{m.module_number}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: "0.92rem", color: "var(--text-main)" }}>
                            {m.name}
                          </span>
                        </div>
                        <Badge variant="neutral">{m.topics.length} topics</Badge>
                      </div>

                      {/* Topics Inside Module */}
                      {isExp && (
                        <div
                          style={{
                            padding: "0.75rem 1rem",
                            display: "flex",
                            flexDirection: "column",
                            gap: "0.5rem",
                            backgroundColor: "var(--bg-app)",
                          }}
                        >
                          {m.topics.map((t, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: "0.6rem 0.75rem",
                                backgroundColor: "var(--bg-surface-soft)",
                                borderRadius: "6px",
                                border: "1px solid var(--border-subtle)",
                                fontSize: "0.84rem",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  flexWrap: "wrap",
                                  gap: "0.4rem",
                                }}
                              >
                                <span style={{ fontWeight: 600, color: "var(--text-main)" }}>
                                  {t.title}
                                </span>
                                <div style={{ display: "flex", gap: "0.3rem" }}>
                                  {t.is_core && <Badge variant="warning">Core Concept</Badge>}
                                  <Badge variant="neutral">{t.difficulty_level}</Badge>
                                  <Badge variant="neutral">{t.recommended_study_method}</Badge>
                                </div>
                              </div>

                              {/* Subtopics chips */}
                              {t.subtopics && t.subtopics.length > 0 && (
                                <div
                                  style={{
                                    display: "flex",
                                    flexWrap: "wrap",
                                    gap: "0.35rem",
                                    marginTop: "0.45rem",
                                  }}
                                >
                                  {t.subtopics.map((st, sidx) => (
                                    <span
                                      key={sidx}
                                      style={{
                                        fontSize: "0.74rem",
                                        backgroundColor: "var(--bg-app)",
                                        padding: "2px 8px",
                                        borderRadius: "4px",
                                        color: "var(--text-muted)",
                                        border: "1px solid var(--border-color)",
                                      }}
                                    >
                                      &bull; {st}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Bottom Actions */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                paddingTop: "0.75rem",
                borderTop: "1px solid var(--border-color)",
              }}
            >
              <Button
                variant="outline"
                onClick={() => setAddStep(1)}
                style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
              >
                <ArrowLeft size={16} /> Back to Edit Details
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmCreateSubject}
                loading={saving}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "8px 18px",
                  fontSize: "0.92rem",
                  fontWeight: 600,
                }}
              >
                <CheckCircle2 size={17} /> Confirm & Register Subject
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* ==================================================== */}
      {/* INTERACTIVE SYLLABUS CHECKLIST MODAL */}
      {/* ==================================================== */}
      <Modal
        isOpen={isSyllabusModalOpen}
        onClose={() => setIsSyllabusModalOpen(false)}
        title={
          syllabusSubject
            ? `${syllabusSubject.name} — Syllabus Checklist`
            : "Syllabus Checklist"
        }
        maxWidth="850px"
      >
        {syllabusLoading ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            Loading course syllabus checklist...
          </div>
        ) : !syllabusRoadmap ? (
          <div style={{ textAlign: "center", padding: "2rem" }}>
            <EmptyState
              icon={BookOpen}
              title="No Syllabus Available for this Subject"
              description="Upload a syllabus document (PDF, DOCX, TXT) to generate the module checklist and track your progress."
              action={
                <Button
                  variant="primary"
                  onClick={() => setIsReplacingSyllabus(true)}
                  style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
                >
                  <UploadCloud size={16} /> Upload Syllabus Document
                </Button>
              }
            />
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
            {/* Top Progress & Quick Actions Header */}
            <div
              style={{
                backgroundColor: "var(--bg-app)",
                padding: "1rem 1.25rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  marginBottom: "0.75rem",
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--text-main)" }}>
                    {syllabusRoadmap.title}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                    Source: {syllabusRoadmap.file_name || "Document"} &bull;{" "}
                    {syllabusRoadmap.total_topics} Total Topics across {syllabusRoadmap.modules.length} Modules
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsReplacingSyllabus(!isReplacingSyllabus)}
                    style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.78rem" }}
                  >
                    <RefreshCw size={13} />
                    {isReplacingSyllabus ? "Cancel Replace" : "Replace Syllabus"}
                  </Button>
                </div>
              </div>

              {/* In-Place Replace Syllabus Box */}
              {isReplacingSyllabus && (
                <div
                  style={{
                    backgroundColor: "var(--bg-surface-soft)",
                    border: "1px dashed var(--color-sage)",
                    borderRadius: "6px",
                    padding: "0.85rem",
                    marginBottom: "0.85rem",
                  }}
                >
                  <div style={{ fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.4rem" }}>
                    Upload Updated Syllabus Document
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.6rem" }}>
                    <strong>Progress Preservation:</strong> Any topics matching your existing syllabus will retain
                    their marked completion status and notes.
                  </div>
                  <form
                    onSubmit={handleReplaceSyllabus}
                    style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}
                  >
                    <input
                      ref={replaceFileInputRef}
                      type="file"
                      accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.webp"
                      className="form-input"
                      style={{ flex: 1, padding: "5px", fontSize: "0.8rem" }}
                      onChange={(e) => {
                        if (e.target.files?.[0]) setReplaceFile(e.target.files[0]);
                      }}
                      required
                    />
                    <Button variant="primary" size="sm" type="submit" loading={replaceLoading}>
                      Confirm & Replace
                    </Button>
                  </form>
                </div>
              )}

              {/* Overall Progress Bar */}
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.82rem",
                    fontWeight: 600,
                    marginBottom: "4px",
                  }}
                >
                  <span>Overall Curriculum Progress</span>
                  <span style={{ color: "var(--color-sage)" }}>
                    {syllabusRoadmap.completed_topics} / {syllabusRoadmap.total_topics} Topics (
                    {syllabusRoadmap.overall_progress_percent}%)
                  </span>
                </div>
                <ProgressBar
                  value={syllabusRoadmap.overall_progress_percent}
                  max={100}
                  color="var(--color-sage)"
                  height={8}
                />
              </div>

              {/* Status Breakdown Pills */}
              <div
                style={{
                  display: "flex",
                  gap: "0.6rem",
                  marginTop: "0.85rem",
                  flexWrap: "wrap",
                  fontSize: "0.78rem",
                }}
              >
                <span
                  style={{
                    backgroundColor: "rgba(90, 110, 82, 0.15)",
                    color: "var(--color-sage)",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontWeight: 600,
                  }}
                >
                  {syllabusRoadmap.completed_topics} Completed
                </span>
                <span
                  style={{
                    backgroundColor: "rgba(217, 131, 36, 0.15)",
                    color: "#D98324",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontWeight: 600,
                  }}
                >
                  {syllabusRoadmap.in_progress_topics} In Progress
                </span>
                <span
                  style={{
                    backgroundColor: "rgba(186, 100, 74, 0.15)",
                    color: "var(--color-terracotta)",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontWeight: 600,
                  }}
                >
                  {syllabusRoadmap.needs_revision_topics} Needs Revision
                </span>
                <span
                  style={{
                    backgroundColor: "var(--bg-surface-soft)",
                    color: "var(--text-muted)",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontWeight: 600,
                  }}
                >
                  {syllabusRoadmap.not_started_topics} Not Started
                </span>
              </div>
            </div>

            {/* Checklist Filter Tabs and Expand All Controls */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "0.6rem",
              }}
            >
              <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginRight: "0.25rem" }}>
                  Filter:
                </span>
                {[
                  { key: "all", label: "All Topics" },
                  { key: "Completed", label: "Completed" },
                  { key: "In Progress", label: "In Progress" },
                  { key: "Needs Revision", label: "Needs Revision" },
                  { key: "Not Started", label: "Not Started" },
                ].map((f) => (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => setChecklistStatusFilter(f.key)}
                    style={{
                      background: checklistStatusFilter === f.key ? "var(--bg-surface-soft)" : "transparent",
                      border:
                        checklistStatusFilter === f.key
                          ? "1px solid var(--border-color)"
                          : "1px solid transparent",
                      borderRadius: "4px",
                      padding: "3px 8px",
                      fontSize: "0.75rem",
                      cursor: "pointer",
                      fontWeight: checklistStatusFilter === f.key ? 700 : 400,
                      color: "var(--text-main)",
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              <div style={{ display: "flex", gap: "0.5rem" }}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleAllChecklistModules(true)}
                  style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                >
                  Expand All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleAllChecklistModules(false)}
                  style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                >
                  Collapse All
                </Button>
              </div>
            </div>

            {/* Module-wise & Topic-wise Checklist Accordion */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.85rem",
                maxHeight: "50vh",
                overflowY: "auto",
                paddingRight: "6px",
              }}
            >
              {syllabusRoadmap.modules.map((mod) => {
                const isExp = expandedChecklistModules[mod.id];
                const filteredTopics =
                  checklistStatusFilter === "all"
                    ? mod.topics
                    : mod.topics.filter((t) => t.status === checklistStatusFilter);

                if (filteredTopics.length === 0 && checklistStatusFilter !== "all") {
                  return null;
                }

                return (
                  <div
                    key={mod.id}
                    style={{
                      border: "1px solid var(--border-color)",
                      borderRadius: "8px",
                      backgroundColor: "var(--bg-app)",
                      overflow: "hidden",
                      flexShrink: 0, // CRITICAL: prevents squishing!
                      width: "100%",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
                    }}
                  >
                    {/* Module Accordion Header */}
                    <div
                      style={{
                        padding: "0.75rem 1rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        backgroundColor: "var(--bg-surface-soft)",
                        cursor: "pointer",
                        userSelect: "none",
                      }}
                      onClick={() => toggleChecklistModule(mod.id)}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                        {isExp ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                        <div>
                          <div style={{ fontWeight: 700, fontSize: "0.92rem", color: "var(--text-main)" }}>
                            {mod.name}
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {mod.completed_count} / {mod.total_count} Topics Completed ({mod.progress_percent}%)
                          </div>
                        </div>
                      </div>

                      <div style={{ width: "120px" }}>
                        <ProgressBar
                          value={mod.progress_percent}
                          max={100}
                          color="var(--color-sage)"
                          height={5}
                        />
                      </div>
                    </div>

                    {/* Topic Items in Module */}
                    {isExp && (
                      <div
                        style={{
                          padding: "0.75rem 1rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.6rem",
                        }}
                      >
                        {filteredTopics.map((top) => {
                          const isDone = top.status === "Completed" || top.is_completed;

                          return (
                            <div
                              key={top.id}
                              style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: "0.4rem",
                                padding: "0.65rem 0.85rem",
                                borderRadius: "6px",
                                backgroundColor: isDone ? "rgba(90, 110, 82, 0.05)" : "var(--bg-app)",
                                border: isDone
                                  ? "1px solid rgba(90, 110, 82, 0.25)"
                                  : "1px solid var(--border-subtle)",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  flexWrap: "wrap",
                                  gap: "0.5rem",
                                }}
                              >
                                {/* Checkbox + Title */}
                                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flex: 1 }}>
                                  <button
                                    type="button"
                                    onClick={() => handleToggleTopicComplete(top.id, top.status)}
                                    style={{
                                      background: "transparent",
                                      border: "none",
                                      cursor: "pointer",
                                      color: isDone ? "var(--color-sage)" : "var(--text-muted)",
                                      padding: 0,
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                    title={isDone ? "Mark as Not Started" : "Mark as Completed"}
                                  >
                                    {isDone ? <CheckSquare size={19} /> : <Square size={19} />}
                                  </button>
                                  <span
                                    style={{
                                      fontWeight: 600,
                                      fontSize: "0.88rem",
                                      color: isDone ? "var(--text-muted)" : "var(--text-main)",
                                      textDecoration: isDone ? "line-through" : "none",
                                    }}
                                  >
                                    {top.title}
                                  </span>
                                </div>

                                {/* Status Selector & Badges */}
                                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                                  {top.is_core && <Badge variant="warning">Core Concept</Badge>}
                                  <Badge variant="neutral">{top.difficulty_level}</Badge>
                                  <Badge variant="neutral">{top.recommended_study_method}</Badge>

                                  {/* 4-State Status Selector */}
                                  <select
                                    value={top.status}
                                    onChange={(e) => handleUpdateTopicStatus(top.id, e.target.value)}
                                    className="form-select"
                                    style={{
                                      width: "auto",
                                      fontSize: "0.78rem",
                                      padding: "3px 6px",
                                      borderRadius: "4px",
                                    }}
                                  >
                                    <option value="Not Started">Not Started</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Needs Revision">Needs Revision</option>
                                  </select>
                                </div>
                              </div>

                              {/* Subtopics Chips */}
                              {top.subtopics && top.subtopics.length > 0 && (
                                <div
                                  style={{
                                    display: "flex",
                                    flexWrap: "wrap",
                                    gap: "0.35rem",
                                    marginLeft: "1.75rem",
                                  }}
                                >
                                  {top.subtopics.map((subtop, sidx) => (
                                    <span
                                      key={sidx}
                                      style={{
                                        fontSize: "0.73rem",
                                        backgroundColor: "var(--bg-surface-soft)",
                                        padding: "1px 7px",
                                        borderRadius: "3px",
                                        color: "var(--text-muted)",
                                        border: "1px solid var(--border-subtle)",
                                      }}
                                    >
                                      &bull; {subtop}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* Conceptual Prerequisites if present */}
                              {top.conceptual_dependencies && top.conceptual_dependencies.length > 0 && (
                                <div
                                  style={{
                                    fontSize: "0.72rem",
                                    color: "var(--text-muted)",
                                    marginLeft: "1.75rem",
                                    fontStyle: "italic",
                                  }}
                                >
                                  Prerequisites: {top.conceptual_dependencies.slice(-2).join(" &rarr; ")}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
              <Button variant="outline" onClick={() => setIsSyllabusModalOpen(false)}>
                Close Checklist
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* ==================================================== */}
      {/* EDIT SUBJECT METADATA MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit Academic Subject">
        <form onSubmit={handleUpdateSubject}>
          <div className="form-group">
            <label className="form-label">Subject / Course Name *</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Course Code</label>
              <input
                type="text"
                className="form-input"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Semester Association</label>
              <select
                className="form-select"
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
              >
                {[
                  "Semester 1",
                  "Semester 2",
                  "Semester 3",
                  "Semester 4",
                  "Semester 5",
                  "Semester 6",
                  "Semester 7",
                  "Semester 8",
                ].map((sem) => (
                  <option key={sem} value={sem}>
                    {sem}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Academic Credits</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="10"
                className="form-input"
                value={credits}
                onChange={(e) => setCredits(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Target Mastery Score (%)</label>
              <input
                type="number"
                min="50"
                max="100"
                className="form-input"
                value={targetScore}
                onChange={(e) => setTargetScore(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Theme Color</label>
            <select className="form-select" value={color} onChange={(e) => setColor(e.target.value)}>
              <option value="#5A6E52">Sage Olive (#5A6E52)</option>
              <option value="#BA644A">Dusty Terracotta (#BA644A)</option>
              <option value="#756254">Muted Wood (#756254)</option>
              <option value="#8A7968">Warm Stone (#8A7968)</option>
              <option value="#4A6B82">Slate Blue (#4A6B82)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Description / Course Notes</label>
            <textarea
              className="form-textarea"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
            <Button variant="outline" type="button" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={saving}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* ==================================================== */}
      {/* VIEW SUBJECT DETAILS MODAL */}
      {/* ==================================================== */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={subjectDetail ? `${subjectDetail.name} — Course Details` : "Subject Overview"}
        maxWidth="720px"
      >
        {detailLoading ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
            Loading course breakdown...
          </div>
        ) : subjectDetail ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {/* Top Stat Summary Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "0.75rem",
                backgroundColor: "var(--bg-app)",
                padding: "0.9rem",
                borderRadius: "6px",
                border: "1px solid var(--border-color)",
              }}
            >
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Semester
                </div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{subjectDetail.semester}</div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Credits
                </div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{subjectDetail.credits} Credits</div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Target
                </div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{subjectDetail.target_score}%</div>
              </div>
              <div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Mastery Score
                </div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--color-sage)" }}>
                  {subjectDetail.weighted_score ?? subjectDetail.average_score ?? "N/A"}
                  {subjectDetail.weighted_score !== null && <span style={{ fontSize: "0.75rem", fontWeight: 400 }}>%</span>}
                </div>
              </div>
            </div>

            {/* Prominent Syllabus Quick Action Banner in Details Modal */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                backgroundColor: "rgba(90, 110, 82, 0.08)",
                border: "1px solid rgba(90, 110, 82, 0.25)",
                borderRadius: "8px",
                padding: "0.85rem 1rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <BookOpen size={22} color="var(--color-sage)" />
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-main)" }}>
                    Course Syllabus & Topic Checklist
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {subjectDetail.has_syllabus
                      ? `${subjectDetail.syllabus_completed_topics || 0} of ${
                          subjectDetail.syllabus_total_topics || 0
                        } topics completed (${subjectDetail.syllabus_progress_percent || 0}%)`
                      : "No syllabus attached yet to this subject"}
                  </div>
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setIsDetailModalOpen(false);
                  handleOpenSyllabusChecklist(subjectDetail);
                }}
                style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
              >
                <ListChecks size={15} />
                {subjectDetail.has_syllabus ? "Open Syllabus Checklist" : "Upload Syllabus"}
              </Button>
            </div>

            {/* Assessment Marks Sub-table */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: 0 }}>
                  Assessment Scores ({subjectDetail.marks?.length || 0})
                </h4>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Total Weightage Used: <strong>{subjectDetail.total_weightage_recorded || 0}%</strong>
                </span>
              </div>

              {!subjectDetail.marks || subjectDetail.marks.length === 0 ? (
                <div
                  style={{
                    padding: "1rem",
                    textAlign: "center",
                    backgroundColor: "var(--bg-app)",
                    borderRadius: "6px",
                    color: "var(--text-muted)",
                    fontSize: "0.85rem",
                  }}
                >
                  No assessment marks logged yet for this subject.
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", textAlign: "left" }}>
                      <th style={{ padding: "0.5rem" }}>Assessment</th>
                      <th style={{ padding: "0.5rem" }}>Type</th>
                      <th style={{ padding: "0.5rem" }}>Score</th>
                      <th style={{ padding: "0.5rem" }}>Percentage</th>
                      <th style={{ padding: "0.5rem" }}>Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subjectDetail.marks.map((m) => (
                      <tr key={m.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td style={{ padding: "0.5rem", fontWeight: 600 }}>{m.assessment_name}</td>
                        <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{m.assessment_type}</td>
                        <td style={{ padding: "0.5rem" }}>
                          {m.scored_marks} / {m.total_marks}
                        </td>
                        <td style={{ padding: "0.5rem", fontWeight: 600 }}>{m.percentage}%</td>
                        <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>
                          {m.weightage_percent ? `${m.weightage_percent}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Assignments Sub-list */}
            <div>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.5rem", margin: 0 }}>
                Coursework Tasks ({subjectDetail.assignments?.length || 0})
              </h4>
              {!subjectDetail.assignments || subjectDetail.assignments.length === 0 ? (
                <div
                  style={{
                    padding: "1rem",
                    textAlign: "center",
                    backgroundColor: "var(--bg-app)",
                    borderRadius: "6px",
                    color: "var(--text-muted)",
                    fontSize: "0.85rem",
                    marginTop: "0.5rem",
                  }}
                >
                  No active assignments for this subject.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "0.5rem" }}>
                  {subjectDetail.assignments.map((a) => (
                    <div
                      key={a.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "0.5rem 0.75rem",
                        backgroundColor: "var(--bg-app)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "4px",
                        fontSize: "0.85rem",
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{a.title}</span>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                          Due: {new Date(a.due_date).toLocaleDateString()}
                        </span>
                        <Badge variant={a.status === "Completed" ? "good" : a.is_overdue ? "danger" : "neutral"}>
                          {a.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
              <Button variant="outline" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* ==================================================== */}
      {/* DELETE CONFIRMATION MODAL */}
      {/* ==================================================== */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Academic Subject">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ fontSize: "0.9rem", color: "var(--text-main)", lineHeight: 1.5, margin: 0 }}>
            Are you sure you want to delete <strong>{selectedSubject?.name}</strong>?
          </p>
          <div
            style={{
              padding: "0.75rem",
              backgroundColor: "var(--status-bad-bg)",
              border: "1px solid var(--status-bad-border)",
              borderRadius: "6px",
              color: "var(--status-bad-text)",
              fontSize: "0.82rem",
            }}
          >
            <strong>Warning:</strong> Deleting this subject will also remove its associated syllabus, topics, assessment
            marks, and coursework tasks.
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              style={{ backgroundColor: "var(--color-terracotta)", borderColor: "var(--color-terracotta)" }}
              onClick={handleDeleteSubject}
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
