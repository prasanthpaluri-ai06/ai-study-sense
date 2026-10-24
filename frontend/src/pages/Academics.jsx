import React, { useEffect, useState } from "react";
import {
  Calendar,
  CheckCircle,
  Clock,
  GraduationCap,
  Plus,
  TrendingUp,
} from "lucide-react";
import { apiRequest } from "../api/client";

export default function Academics() {
  const [subjects, setSubjects] = useState([]);
  const [marks, setMarks] = useState([]);
  const [assignments, setAssignments] = useState([]);

  // Form states
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newSubjectCode, setNewSubjectCode] = useState("");
  const [newMarkSubjectId, setNewMarkSubjectId] = useState("");
  const [newMarkName, setNewMarkName] = useState("CAT 1");
  const [newMarkScored, setNewMarkScored] = useState("");
  const [newMarkTotal, setNewMarkTotal] = useState("50");

  const [newAssignTitle, setNewAssignTitle] = useState("");
  const [newAssignSubjectId, setNewAssignSubjectId] = useState("");
  const [newAssignDueDate, setNewAssignDueDate] = useState("");
  const [newAssignPriority, setNewAssignPriority] = useState("Medium");

  useEffect(() => {
    loadAcademicData();
  }, []);

  async function loadAcademicData() {
    try {
      const [subs, mks, asgns] = await Promise.all([
        apiRequest("/academic/subjects"),
        apiRequest("/academic/marks"),
        apiRequest("/academic/assignments"),
      ]);
      setSubjects(subs);
      setMarks(mks);
      setAssignments(asgns);
      if (subs.length > 0) {
        if (!newMarkSubjectId) setNewMarkSubjectId(subs[0].id);
        if (!newAssignSubjectId) setNewAssignSubjectId(subs[0].id);
      }
    } catch (err) {
      console.error("Error fetching academic records:", err);
    }
  }

  const handleAddSubject = async (e) => {
    e.preventDefault();
    if (!newSubjectName) return;
    try {
      await apiRequest("/academic/subjects", {
        method: "POST",
        body: JSON.stringify({ name: newSubjectName, code: newSubjectCode }),
      });
      setNewSubjectName("");
      setNewSubjectCode("");
      loadAcademicData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAddMark = async (e) => {
    e.preventDefault();
    if (!newMarkSubjectId || !newMarkScored) return;
    try {
      await apiRequest("/academic/marks", {
        method: "POST",
        body: JSON.stringify({
          subject_id: parseInt(newMarkSubjectId),
          assessment_name: newMarkName,
          scored_marks: parseFloat(newMarkScored),
          total_marks: parseFloat(newMarkTotal),
        }),
      });
      setNewMarkScored("");
      loadAcademicData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAddAssignment = async (e) => {
    e.preventDefault();
    if (!newAssignSubjectId || !newAssignTitle || !newAssignDueDate) return;
    try {
      await apiRequest("/academic/assignments", {
        method: "POST",
        body: JSON.stringify({
          subject_id: parseInt(newAssignSubjectId),
          title: newAssignTitle,
          due_date: new Date(newAssignDueDate).toISOString(),
          priority: newAssignPriority,
        }),
      });
      setNewAssignTitle("");
      setNewAssignDueDate("");
      loadAcademicData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 700 }}>Academic Management</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Track coursework, assessment performance, and assignments across all subjects.
        </p>
      </div>

      {/* Subjects Grid & Add Subject */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <GraduationCap size={18} color="#4f46e5" />
            <h3 className="card-title">Enrolled Subjects</h3>
          </div>
        </div>

        {/* Add Subject inline form */}
        <form onSubmit={handleAddSubject} style={{ display: "flex", gap: "0.75rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
          <div style={{ flex: 2, minWidth: "180px" }}>
            <input
              type="text"
              placeholder="Subject Name (e.g. Algorithms)"
              value={newSubjectName}
              onChange={(e) => setNewSubjectName(e.target.value)}
              required
            />
          </div>
          <div style={{ flex: 1, minWidth: "100px" }}>
            <input
              type="text"
              placeholder="Code (e.g. CS201)"
              value={newSubjectCode}
              onChange={(e) => setNewSubjectCode(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">
            <Plus size={16} />
            <span>Add Subject</span>
          </button>
        </form>

        {/* Subjects list */}
        <div className="grid-3">
          {subjects.map((sub) => (
            <div
              key={sub.id}
              style={{
                background: "#0f172a",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "1rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: 600, fontSize: "1rem" }}>{sub.name}</span>
                {sub.code && (
                  <span style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.1)", padding: "2px 6px", borderRadius: "4px" }}>
                    {sub.code}
                  </span>
                )}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                <span>Performance:</span>
                <strong style={{ color: "#10b981" }}>{sub.average_score ? `${sub.average_score}%` : "No marks"}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two Column Section: Marks Entry & Assignments Tracker */}
      <div className="grid-2">
        {/* Marks Entry & History */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <TrendingUp size={18} color="#10b981" />
              <h3 className="card-title">Assessment Marks Tracker</h3>
            </div>
          </div>

          <form onSubmit={handleAddMark} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1rem" }}>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <select value={newMarkSubjectId} onChange={(e) => setNewMarkSubjectId(e.target.value)} required>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <select value={newMarkName} onChange={(e) => setNewMarkName(e.target.value)}>
                <option value="CAT 1">CAT 1</option>
                <option value="CAT 2">CAT 2</option>
                <option value="Quiz">Quiz</option>
                <option value="Lab Assessment">Lab Assessment</option>
                <option value="Midterm Exam">Midterm Exam</option>
                <option value="End Semester">End Semester</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="number"
                step="0.5"
                placeholder="Scored Marks"
                value={newMarkScored}
                onChange={(e) => setNewMarkScored(e.target.value)}
                required
              />
              <input
                type="number"
                placeholder="Total Marks"
                value={newMarkTotal}
                onChange={(e) => setNewMarkTotal(e.target.value)}
                required
              />
              <button type="submit" className="btn-primary" style={{ whiteSpace: "nowrap" }}>
                Save Mark
              </button>
            </div>
          </form>

          {/* Marks table */}
          <div style={{ maxHeight: "250px", overflowY: "auto" }}>
            {marks.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No marks recorded yet.</div>
            ) : (
              marks.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "0.6rem 0",
                    borderBottom: "1px solid var(--border)",
                    fontSize: "0.85rem",
                  }}
                >
                  <span>{m.assessment_name}</span>
                  <strong>{m.scored_marks} / {m.total_marks} ({m.percentage}%)</strong>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Assignment Tracker */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Calendar size={18} color="#06b6d4" />
              <h3 className="card-title">Assignments & Deadlines</h3>
            </div>
          </div>

          <form onSubmit={handleAddAssignment} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1rem" }}>
            <input
              type="text"
              placeholder="Assignment Title"
              value={newAssignTitle}
              onChange={(e) => setNewAssignTitle(e.target.value)}
              required
            />
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <select value={newAssignSubjectId} onChange={(e) => setNewAssignSubjectId(e.target.value)} required>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <select value={newAssignPriority} onChange={(e) => setNewAssignPriority(e.target.value)}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="date"
                value={newAssignDueDate}
                onChange={(e) => setNewAssignDueDate(e.target.value)}
                required
              />
              <button type="submit" className="btn-primary" style={{ whiteSpace: "nowrap" }}>
                Add Task
              </button>
            </div>
          </form>

          {/* Assignments list */}
          <div style={{ maxHeight: "250px", overflowY: "auto" }}>
            {assignments.map((a) => (
              <div
                key={a.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.6rem 0",
                  borderBottom: "1px solid var(--border)",
                  fontSize: "0.85rem",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                    Due: {new Date(a.due_date).toLocaleDateString()} &bull; {a.subject_name}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "0.75rem",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: a.priority === "Critical" ? "#ef4444" : "#10b981",
                    color: "white",
                  }}
                >
                  {a.priority}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
