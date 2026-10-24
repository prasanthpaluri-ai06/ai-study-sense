import React, { useEffect, useState, useRef } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState, ProgressBar } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Compass,
  UploadCloud,
  FileText,
  Type,
  Sparkles,
  CheckCircle2,
  Clock,
  AlertCircle,
  Circle,
  Trash2,
  ArrowRight,
  PlayCircle,
  Layers,
  ChevronDown,
  ChevronRight,
  Target
} from "lucide-react";

export default function SyllabusRoadmap({ setActivePage, setSelectedSessionData }) {
  const [roadmaps, setRoadmaps] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [syllabusTitle, setSyllabusTitle] = useState("");
  const [syllabusText, setSyllabusText] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMode, setUploadMode] = useState("file"); // 'file' or 'text'
  const [uploading, setUploading] = useState(false);
  const [activeRoadmapId, setActiveRoadmapId] = useState(null);
  const [expandedModules, setExpandedModules] = useState({});
  const fileInputRef = useRef(null);
  const toast = useToast();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [subs, rdms] = await Promise.all([
        apiRequest("/academic/subjects"),
        apiRequest("/syllabus/roadmaps"),
      ]);
      setSubjects(subs || []);
      setRoadmaps(rdms || []);
      if (subs && subs.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(subs[0].id);
      }
      if (rdms && rdms.length > 0 && !activeRoadmapId) {
        setActiveRoadmapId(rdms[0].id);
        // Expand all modules by default for first roadmap
        const initialExpanded = {};
        rdms[0].modules.forEach(m => {
          initialExpanded[m.id] = true;
        });
        setExpandedModules(initialExpanded);
      }
    } catch (err) {
      console.error("Error loading syllabus data:", err);
    }
  }

  const handleFileUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSubjectId) {
      toast.error("Please select a subject first.");
      return;
    }

    setUploading(true);
    try {
      if (uploadMode === "file") {
        if (!selectedFile) {
          toast.error("Please select a PDF, DOCX, or TXT file.");
          setUploading(false);
          return;
        }

        const formData = new FormData();
        formData.append("subject_id", selectedSubjectId);
        if (syllabusTitle.trim()) {
          formData.append("title", syllabusTitle.trim());
        }
        formData.append("file", selectedFile);

        const token = localStorage.getItem("token");
        const res = await fetch("http://localhost:8000/api/v1/syllabus/upload/file", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Failed to process syllabus document.");
        }

        const newRoadmap = await res.json();
        toast.success(`Extracted ${newRoadmap.total_topics} topics across ${newRoadmap.modules.length} modules!`);
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      } else {
        if (!syllabusText.trim()) {
          toast.error("Please paste your syllabus text.");
          setUploading(false);
          return;
        }

        await apiRequest("/syllabus/upload/text", {
          method: "POST",
          body: JSON.stringify({
            subject_id: parseInt(selectedSubjectId),
            title: syllabusTitle.trim() || undefined,
            content_text: syllabusText.trim(),
          }),
        });
        toast.success("Syllabus parsed into structured topic checklist!");
        setSyllabusText("");
      }

      setSyllabusTitle("");
      await loadData();
    } catch (err) {
      toast.error(err.message || "Failed uploading syllabus");
    } finally {
      setUploading(false);
    }
  };

  const handleUpdateTopicStatus = async (topicId, newStatus) => {
    try {
      await apiRequest(`/syllabus/topics/${topicId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      // Optimistically update local state
      setRoadmaps(prevRoadmaps =>
        prevRoadmaps.map(rm => ({
          ...rm,
          modules: rm.modules.map(mod => ({
            ...mod,
            topics: mod.topics.map(t =>
              t.id === topicId ? { ...t, status: newStatus, is_completed: newStatus === "Completed" } : t
            ),
          })),
        }))
      );
      // Refresh to recalculate progress counters accurately
      const updated = await apiRequest("/syllabus/roadmaps");
      setRoadmaps(updated || []);
    } catch (err) {
      toast.error(err.message || "Failed to update topic status.");
    }
  };

  const handleDeleteSyllabus = async (syllabusId, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this syllabus roadmap?")) return;
    try {
      await apiRequest(`/syllabus/${syllabusId}`, { method: "DELETE" });
      toast.info("Syllabus roadmap deleted.");
      const updated = roadmaps.filter(r => r.id !== syllabusId);
      setRoadmaps(updated);
      if (activeRoadmapId === syllabusId) {
        setActiveRoadmapId(updated.length > 0 ? updated[0].id : null);
      }
    } catch (err) {
      toast.error("Failed to delete syllabus roadmap.");
    }
  };

  const toggleModuleAccordion = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }));
  };

  const startTopicStudy = (subjectId, subjectName, topicTitle, recommendedMethod) => {
    if (setSelectedSessionData) {
      setSelectedSessionData({
        subject_id: subjectId,
        subject_name: subjectName,
        topic: topicTitle,
        method: recommendedMethod || "Active Recall",
      });
    }
    if (setActivePage) {
      setActivePage("study-session");
    }
  };

  const activeRoadmap = roadmaps.find(r => r.id === activeRoadmapId) || roadmaps[0];

  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case "Completed":
        return "good";
      case "In Progress":
        return "terracotta";
      case "Needs Revision":
        return "warning";
      default:
        return "neutral";
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
          Checklist Syllabus Roadmap
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
          AI extracts modules, core topics, and conceptual dependencies from uploaded documents into an actionable checklist.
        </p>
      </div>

      {/* Upload & Extraction Section */}
      <Card
        title="Extract Course Syllabus"
        subtitle="Upload your official syllabus (PDF, DOCX, TXT) or paste raw curriculum text. The AI maps topics in conceptual learning order."
        icon={UploadCloud}
      >
        <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.25rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "0.75rem" }}>
          <button
            type="button"
            onClick={() => setUploadMode("file")}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: uploadMode === "file" ? "var(--color-sage)" : "var(--border-color)",
              backgroundColor: uploadMode === "file" ? "var(--bg-app)" : "transparent",
              fontWeight: uploadMode === "file" ? 600 : 500,
              color: uploadMode === "file" ? "var(--color-sage)" : "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.88rem"
            }}
          >
            <FileText size={16} /> Document File (.PDF, .DOCX, .TXT)
          </button>
          <button
            type="button"
            onClick={() => setUploadMode("text")}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: uploadMode === "text" ? "var(--color-sage)" : "var(--border-color)",
              backgroundColor: uploadMode === "text" ? "var(--bg-app)" : "transparent",
              fontWeight: uploadMode === "text" ? 600 : 500,
              color: uploadMode === "text" ? "var(--color-sage)" : "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.88rem"
            }}
          >
            <Type size={16} /> Paste Raw Text
          </button>
        </div>

        <form onSubmit={handleFileUploadSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: "220px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Associate Subject *
              </label>
              <select
                className="form-select"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                required
              >
                {subjects.length === 0 && <option value="">No subjects created yet</option>}
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.code || "No Code"})</option>
                ))}
              </select>
            </div>

            <div style={{ flex: 2, minWidth: "260px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Syllabus / Course Title (Optional)
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Data Structures & Algorithms (CS201)"
                value={syllabusTitle}
                onChange={(e) => setSyllabusTitle(e.target.value)}
              />
            </div>
          </div>

          {uploadMode === "file" ? (
            <div
              style={{
                border: "2px dashed var(--border-color)",
                borderRadius: "6px",
                padding: "1.75rem",
                textAlign: "center",
                backgroundColor: "var(--bg-app)",
                cursor: "pointer",
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: "none" }}
                accept=".pdf,.docx,.doc,.txt,.md"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSelectedFile(e.target.files[0]);
                  }
                }}
              />
              <UploadCloud size={36} color="var(--color-sage)" style={{ margin: "0 auto 0.5rem" }} />
              <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-main)" }}>
                {selectedFile ? selectedFile.name : "Click to select or drag & drop syllabus document"}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                Supports PDF, DOCX, or TXT up to 15 MB
              </div>
              {selectedFile && (
                <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "var(--color-sage)", fontWeight: 600 }}>
                  Ready to process ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>
          ) : (
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem", color: "var(--text-muted)" }}>
                Syllabus Content (Modules & Topic Bullet Points)
              </label>
              <textarea
                className="form-textarea"
                rows={5}
                placeholder={`MODULE 1: Linear Data Structures
- Arrays and Dynamic Sizing
- Singly and Doubly Linked Lists
- Stacks & Queues

MODULE 2: Hierarchical Structures
- Tree Terminology & Binary Trees
- Tree Traversals: Inorder, Preorder, Postorder
- Binary Search Trees (BST) & AVL Balancing`}
                value={syllabusText}
                onChange={(e) => setSyllabusText(e.target.value)}
                required={uploadMode === "text"}
              />
            </div>
          )}

          <Button
            variant="primary"
            type="submit"
            icon={Sparkles}
            loading={uploading}
            style={{ alignSelf: "flex-start" }}
          >
            {uploading ? "Extracting Conceptual Modules..." : "Generate AI Checklist Roadmap"}
          </Button>
        </form>
      </Card>

      {/* Syllabus Selector & Roadmap View */}
      {roadmaps.length === 0 ? (
        <EmptyState
          icon={Compass}
          title="No Syllabus Roadmaps Uploaded Yet"
          description="Upload or paste your course syllabus above to automatically generate structured module checklists."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Syllabus Switcher Tabs */}
          <div style={{ display: "flex", gap: "0.5rem", overflowX: "auto", paddingBottom: "0.25rem" }}>
            {roadmaps.map((r) => {
              const isActive = r.id === (activeRoadmap?.id);
              return (
                <button
                  key={r.id}
                  onClick={() => {
                    setActiveRoadmapId(r.id);
                    const modExpanded = {};
                    r.modules.forEach(m => { modExpanded[m.id] = true; });
                    setExpandedModules(modExpanded);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "0.6rem 1rem",
                    borderRadius: "6px",
                    border: `1px solid ${isActive ? "var(--color-sage)" : "var(--border-color)"}`,
                    backgroundColor: isActive ? "var(--color-sage)" : "var(--bg-surface)",
                    color: isActive ? "#FFFFFF" : "var(--text-main)",
                    fontWeight: 600,
                    fontSize: "0.88rem",
                    cursor: "pointer",
                    whiteSpace: "nowrap"
                  }}
                >
                  <Layers size={15} />
                  <span>{r.title}</span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      backgroundColor: isActive ? "rgba(255,255,255,0.25)" : "var(--bg-app)",
                      padding: "2px 6px",
                      borderRadius: "10px",
                    }}
                  >
                    {r.completion_percentage}%
                  </span>
                  <Trash2
                    size={14}
                    style={{ marginLeft: "4px", opacity: 0.7 }}
                    onClick={(e) => handleDeleteSyllabus(r.id, e)}
                  />
                </button>
              );
            })}
          </div>

          {activeRoadmap && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              {/* Overall Progress Banner */}
              <Card style={{ borderLeft: "5px solid var(--color-sage)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                  <div>
                    <h2 style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-main)" }}>
                      {activeRoadmap.title}
                    </h2>
                    <div style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                      Course: <strong>{activeRoadmap.subject_name || "Academic Subject"}</strong> &bull; {activeRoadmap.modules.length} Modules &bull; {activeRoadmap.total_topics} Topics
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--color-sage)" }}>
                        {activeRoadmap.completion_percentage}%
                      </div>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Overall Mastery</div>
                    </div>
                    <div style={{ width: "140px" }}>
                      <ProgressBar
                        value={activeRoadmap.completed_topics}
                        max={activeRoadmap.total_topics || 1}
                        color="var(--color-sage)"
                      />
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem", marginTop: "1rem" }}>
                  <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "var(--bg-app)", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Total Topics</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>{activeRoadmap.total_topics}</div>
                  </div>
                  <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "var(--status-good-bg)", borderRadius: "6px", border: "1px solid var(--status-good-border)" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--status-good-text)" }}>Completed</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--status-good-text)" }}>{activeRoadmap.completed_topics}</div>
                  </div>
                  <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "var(--status-terracotta-bg)", borderRadius: "6px", border: "1px solid var(--status-terracotta-border)" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--status-terracotta-text)" }}>In Progress</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--status-terracotta-text)" }}>
                      {activeRoadmap.modules.reduce((acc, m) => acc + m.topics.filter(t => t.status === "In Progress").length, 0)}
                    </div>
                  </div>
                  <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "var(--status-warning-bg)", borderRadius: "6px", border: "1px solid var(--status-warning-border)" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--status-warning-text)" }}>Needs Revision</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--status-warning-text)" }}>
                      {activeRoadmap.modules.reduce((acc, m) => acc + m.topics.filter(t => t.status === "Needs Revision").length, 0)}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Modules List */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {activeRoadmap.modules.map((mod, modIdx) => {
                  const isExpanded = expandedModules[mod.id] !== false;
                  const modTotal = mod.topics.length;
                  const modCompleted = mod.topics.filter(t => t.is_completed || t.status === "Completed").length;
                  const modPct = modTotal > 0 ? Math.round((modCompleted / modTotal) * 100) : 0;

                  return (
                    <div
                      key={mod.id}
                      style={{
                        backgroundColor: "var(--bg-surface)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "6px",
                        overflow: "hidden",
                      }}
                    >
                      {/* Module Header */}
                      <div
                        onClick={() => toggleModuleAccordion(mod.id)}
                        style={{
                          padding: "1rem 1.25rem",
                          backgroundColor: "var(--bg-app)",
                          borderBottom: isExpanded ? "1px solid var(--border-color)" : "none",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          cursor: "pointer",
                          userSelect: "none",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                          {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                          <div>
                            <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--color-wood)" }}>
                              {mod.name}
                            </span>
                            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: "0.75rem" }}>
                              {modCompleted} of {modTotal} topics ({modPct}%)
                            </span>
                          </div>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                          <div style={{ width: "100px" }}>
                            <ProgressBar value={modCompleted} max={modTotal || 1} color="var(--color-sage)" />
                          </div>
                        </div>
                      </div>

                      {/* Module Content & Topic Checklists */}
                      {isExpanded && (
                        <div style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                          {/* Conceptual Dependency Ribbon */}
                          {mod.conceptual_chain && mod.conceptual_chain.length > 1 && (
                            <div
                              style={{
                                backgroundColor: "var(--bg-app)",
                                border: "1px dashed var(--border-color)",
                                borderRadius: "6px",
                                padding: "0.65rem 0.85rem",
                                fontSize: "0.82rem",
                                color: "var(--text-muted)",
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem",
                                flexWrap: "wrap",
                              }}
                            >
                              <strong style={{ color: "var(--color-wood)" }}>Conceptual Flow:</strong>
                              {mod.conceptual_chain.map((chainItem, cIdx) => (
                                <React.Fragment key={cIdx}>
                                  <span style={{ color: "var(--text-main)", fontWeight: 500 }}>{chainItem}</span>
                                  {cIdx < mod.conceptual_chain.length - 1 && (
                                    <ArrowRight size={13} color="var(--color-sage)" />
                                  )}
                                </React.Fragment>
                              ))}
                            </div>
                          )}

                          {/* Topic Checklist Items */}
                          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                            {mod.topics.map((topic) => {
                              const isComplete = topic.status === "Completed";
                              return (
                                <div
                                  key={topic.id}
                                  style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: "0.4rem",
                                    padding: "0.85rem 1rem",
                                    borderRadius: "6px",
                                    backgroundColor: isComplete ? "var(--status-good-bg)" : "var(--bg-app)",
                                    border: `1px solid ${isComplete ? "var(--status-good-border)" : "var(--border-color)"}`,
                                    transition: "background-color 0.15s ease",
                                  }}
                                >
                                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flex: 1, minWidth: "220px" }}>
                                      <button
                                        type="button"
                                        onClick={() => handleUpdateTopicStatus(topic.id, isComplete ? "Not Started" : "Completed")}
                                        style={{
                                          background: "none",
                                          border: "none",
                                          padding: 0,
                                          cursor: "pointer",
                                          display: "flex",
                                          alignItems: "center",
                                        }}
                                        title={isComplete ? "Mark as Not Started" : "Mark as Completed"}
                                      >
                                        {isComplete ? (
                                          <CheckCircle2 size={20} color="var(--color-sage)" />
                                        ) : (
                                          <Circle size={20} color="var(--text-subtle)" />
                                        )}
                                      </button>

                                      <div>
                                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                                          <span
                                            style={{
                                              fontSize: "0.95rem",
                                              fontWeight: isComplete ? 500 : 600,
                                              textDecoration: isComplete ? "line-through" : "none",
                                              color: isComplete ? "var(--text-muted)" : "var(--text-main)",
                                            }}
                                          >
                                            {topic.title}
                                          </span>
                                          {topic.is_core && (
                                            <Badge variant="terracotta">Core Exam Topic</Badge>
                                          )}
                                        </div>

                                        {/* Subtopics */}
                                        {topic.subtopics && topic.subtopics.length > 0 && (
                                          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                                            {topic.subtopics.join(" &bull; ")}
                                          </div>
                                        )}
                                      </div>
                                    </div>

                                    {/* Actions & Status Dropdown */}
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                                      <Badge variant="neutral" title="Recommended Learning Method">
                                        {topic.recommended_study_method}
                                      </Badge>

                                      <select
                                        className="form-select"
                                        value={topic.status}
                                        onChange={(e) => handleUpdateTopicStatus(topic.id, e.target.value)}
                                        style={{
                                          padding: "0.25rem 0.5rem",
                                          fontSize: "0.82rem",
                                          height: "30px",
                                          fontWeight: 600,
                                        }}
                                      >
                                        <option value="Not Started">Not Started</option>
                                        <option value="In Progress">In Progress</option>
                                        <option value="Completed">Completed</option>
                                        <option value="Needs Revision">Needs Revision</option>
                                      </select>

                                      <button
                                        type="button"
                                        onClick={() => startTopicStudy(
                                          activeRoadmap.subject_id,
                                          activeRoadmap.subject_name,
                                          topic.title,
                                          topic.recommended_study_method
                                        )}
                                        style={{
                                          display: "flex",
                                          alignItems: "center",
                                          gap: "0.3rem",
                                          padding: "0.3rem 0.6rem",
                                          backgroundColor: "var(--color-sage)",
                                          color: "#FFFFFF",
                                          border: "none",
                                          borderRadius: "4px",
                                          fontSize: "0.8rem",
                                          fontWeight: 600,
                                          cursor: "pointer",
                                        }}
                                        title="Start a timed study session on this topic"
                                      >
                                        <PlayCircle size={14} /> Study
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
