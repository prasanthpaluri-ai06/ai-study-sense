import React, { useEffect, useState } from "react";
import {
  CheckSquare,
  ChevronDown,
  ChevronRight,
  Compass,
  FileText,
  Sparkles,
  Square,
  UploadCloud,
} from "lucide-react";
import { apiRequest } from "../api/client";

export default function Roadmap({ setActivePage }) {
  const [roadmaps, setRoadmaps] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [syllabusTitle, setSyllabusTitle] = useState("");
  const [syllabusText, setSyllabusText] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [subs, rdms] = await Promise.all([
        apiRequest("/academic/subjects"),
        apiRequest("/syllabus/roadmaps"),
      ]);
      setSubjects(subs);
      setRoadmaps(rdms);
      if (subs.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(subs[0].id);
      }
    } catch (err) {
      console.error("Error loading roadmaps:", err);
    }
  }

  const handleUploadSyllabus = async (e) => {
    e.preventDefault();
    if (!selectedSubjectId || !syllabusText) return;
    setUploading(true);
    try {
      await apiRequest("/syllabus/upload", {
        method: "POST",
        body: JSON.stringify({
          subject_id: parseInt(selectedSubjectId),
          title: syllabusTitle || "Syllabus Roadmap",
          content_text: syllabusText,
        }),
      });
      setSyllabusTitle("");
      setSyllabusText("");
      loadData();
    } catch (err) {
      alert(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleToggleTopic = async (topicId) => {
    try {
      await apiRequest(`/syllabus/topics/${topicId}/toggle-status`, {
        method: "POST",
      });
      loadData();
    } catch (err) {
      console.error("Error toggling topic status:", err);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 700 }}>Checklist Syllabus Roadmap</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Conceptual order of topics for each module. Check off topics as you master them.
        </p>
      </div>

      {/* Syllabus Uploader Card */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <UploadCloud size={18} color="#4f46e5" />
            <h3 className="card-title">Upload / Paste Syllabus Text</h3>
          </div>
        </div>

        <form onSubmit={handleUploadSyllabus} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <select
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              style={{ flex: 1, minWidth: "200px" }}
              required
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Syllabus Title (e.g. Data Structures & Algorithms)"
              value={syllabusTitle}
              onChange={(e) => setSyllabusTitle(e.target.value)}
              style={{ flex: 2, minWidth: "250px" }}
            />
          </div>

          <textarea
            rows={4}
            placeholder={`Paste your syllabus here. Example:
MODULE 1: Algorithm Analysis
- Time Complexity
- Space Complexity
- Recurrence Relations

MODULE 2: Trees
- Binary Search Trees
- AVL Rotations`}
            value={syllabusText}
            onChange={(e) => setSyllabusText(e.target.value)}
            required
          />

          <button type="submit" className="btn-primary" style={{ alignSelf: "flex-start" }} disabled={uploading}>
            <Sparkles size={16} />
            <span>{uploading ? "Extracting Modules & Topics..." : "Extract Checklist Roadmap with AI"}</span>
          </button>
        </form>
      </div>

      {/* Structured Roadmap Checklists */}
      {roadmaps.map((syl) => (
        <div key={syl.id} className="card">
          <div className="card-header">
            <div>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700 }}>{syl.title}</h3>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{syl.subject_name}</div>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {syl.modules.map((mod) => (
              <div
                key={mod.id}
                style={{
                  background: "#0f172a",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1.25rem",
                }}
              >
                <h4 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#a5b4fc", marginBottom: "0.75rem" }}>
                  {mod.name}
                </h4>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {mod.topics.map((top) => (
                    <div
                      key={top.id}
                      onClick={() => handleToggleTopic(top.id)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "0.6rem 0.8rem",
                        borderRadius: "6px",
                        background: top.is_completed ? "rgba(16, 185, 129, 0.1)" : "rgba(30, 41, 59, 0.6)",
                        border: `1px solid ${top.is_completed ? "#10b981" : "var(--border)"}`,
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        {top.is_completed ? (
                          <CheckSquare size={18} color="#10b981" />
                        ) : (
                          <Square size={18} color="var(--text-muted)" />
                        )}
                        <span
                          style={{
                            fontSize: "0.95rem",
                            textDecoration: top.is_completed ? "line-through" : "none",
                            color: top.is_completed ? "var(--text-muted)" : "var(--text-main)",
                          }}
                        >
                          {top.title}
                        </span>
                      </div>

                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            padding: "2px 8px",
                            borderRadius: "12px",
                            background: "rgba(79, 70, 229, 0.2)",
                            color: "#a5b4fc",
                          }}
                        >
                          {top.recommended_study_method}
                        </span>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            padding: "2px 8px",
                            borderRadius: "12px",
                            background: top.is_completed ? "rgba(16, 185, 129, 0.2)" : "rgba(148, 163, 184, 0.2)",
                            color: top.is_completed ? "#10b981" : "#94a3b8",
                          }}
                        >
                          {top.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
