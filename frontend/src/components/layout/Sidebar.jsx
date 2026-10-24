import React from "react";
import {
  LayoutDashboard,
  Timer,
  BookOpen,
  GraduationCap,
  Award,
  Calendar,
  Compass,
  Sparkles,
  FileQuestion,
  BookMarked,
  Search,
  BarChart2,
  HeartPulse,
  User,
  BrainCircuit,
  LogOut,
  ChevronRight,
} from "lucide-react";

export default function Sidebar({ activePage, setActivePage, currentUser, onLogout }) {
  const navigationGroups = [
    {
      label: "Overview",
      items: [{ id: "dashboard", label: "Dashboard", icon: LayoutDashboard }],
    },
    {
      label: "Study Execution",
      items: [
        { id: "study-methods", label: "Study Methods", icon: BookOpen },
        { id: "study-session", label: "Live Study Session", icon: Timer },
      ],
    },
    {
      label: "Academic Growth",
      items: [
        { id: "subjects", label: "Course Subjects", icon: GraduationCap },
        { id: "marks", label: "Marks Tracker", icon: Award },
        { id: "assignments", label: "Assignments & Due", icon: Calendar },
      ],
    },
    {
      label: "Syllabus Intelligence",
      items: [
        { id: "roadmap", label: "Checklist Roadmap", icon: Compass },
      ],
    },
    {
      label: "AI Academic Tools",
      items: [
        { id: "ai-coach", label: "AI Coach & Planner", icon: Sparkles },
        { id: "quiz-generator", label: "Topic Quiz Generator", icon: FileQuestion },
        { id: "revision-generator", label: "Revision Packages", icon: BookMarked },
        { id: "resource-finder", label: "Resource Finder", icon: Search },
      ],
    },
    {
      label: "Analytics & Health",
      items: [
        { id: "session-analytics", label: "Session Reports", icon: BarChart2 },
        { id: "study-health", label: "Study Health Score", icon: HeartPulse },
      ],
    },
    {
      label: "Account",
      items: [
        { id: "profile", label: "Profile & Face Auth", icon: User },
      ],
    },
  ];

  return (
    <aside
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        bottom: 0,
        width: "var(--sidebar-width)",
        backgroundColor: "var(--bg-surface)",
        borderRight: "1px solid var(--border-color)",
        display: "flex",
        flexDirection: "column",
        zIndex: 40,
        overflowY: "auto",
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: "1.25rem 1.25rem 1rem 1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "6px",
            backgroundColor: "var(--color-sage)",
            color: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <BrainCircuit size={20} />
        </div>
        <div>
          <h1 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-main)", letterSpacing: "-0.02em" }}>
            AI StudySense
          </h1>
          <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "1px" }}>
            Academic Companion & IoT
          </p>
        </div>
      </div>

      {/* Navigation list */}
      <nav style={{ flex: 1, padding: "1rem 0.75rem" }}>
        {navigationGroups.map((group, gIdx) => (
          <div key={gIdx} style={{ marginBottom: "1.25rem" }}>
            <div
              style={{
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "var(--text-subtle)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                padding: "0 0.6rem 0.4rem 0.6rem",
              }}
            >
              {group.label}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActivePage(item.id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.55rem 0.65rem",
                      borderRadius: "6px",
                      fontSize: "0.88rem",
                      fontWeight: isActive ? 600 : 500,
                      backgroundColor: isActive ? "var(--color-sage-soft)" : "transparent",
                      color: isActive ? "var(--color-sage)" : "var(--text-muted)",
                      border: "none",
                      width: "100%",
                      textAlign: "left",
                      transition: "background-color 0.12s ease, color 0.12s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = "var(--bg-surface-warm)";
                        e.currentTarget.style.color = "var(--text-main)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = "transparent";
                        e.currentTarget.style.color = "var(--text-muted)";
                      }
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <Icon size={16} />
                      <span>{item.label}</span>
                    </div>
                    {isActive && <ChevronRight size={14} />}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User profile footer */}
      {currentUser && (
        <div
          style={{
            padding: "0.9rem 1rem",
            borderTop: "1px solid var(--border-color)",
            backgroundColor: "var(--bg-surface-warm)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{ display: "flex", alignItems: "center", gap: "0.6rem", cursor: "pointer", overflow: "hidden" }}
            onClick={() => setActivePage("profile")}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "var(--color-sand)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.85rem",
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : "U"}
            </div>
            <div style={{ overflow: "hidden" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)", whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden" }}>
                {currentUser.full_name}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden" }}>
                @{currentUser.username}
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Sign Out"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "4px",
              borderRadius: "4px",
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      )}
    </aside>
  );
}
