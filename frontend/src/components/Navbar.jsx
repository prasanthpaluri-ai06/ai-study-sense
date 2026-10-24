import React from "react";
import {
  BookOpen,
  BrainCircuit,
  Compass,
  FileCheck,
  Flame,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Timer,
} from "lucide-react";
import HardwareStatusBadge from "./HardwareStatusBadge";

export default function Navbar({ activePage, setActivePage, currentUser, onLogout, hardwareState }) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "session", label: "Study Session", icon: Timer },
    { id: "academics", label: "Academics", icon: GraduationCap },
    { id: "roadmap", label: "Syllabus Roadmap", icon: Compass },
    { id: "coach", label: "AI Study Coach", icon: Sparkles },
  ];

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border)",
        background: "rgba(15, 23, 42, 0.9)",
        backdropFilter: "blur(10px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
        padding: "0.75rem 2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      {/* Brand & Motto */}
      <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div
            style={{
              background: "linear-gradient(135deg, #4f46e5, #06b6d4)",
              borderRadius: "10px",
              padding: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <BrainCircuit size={22} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: "1.15rem", fontWeight: 700, letterSpacing: "-0.5px" }}>
              AI StudySense
            </h1>
            <p style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>
              Hardware + AI Academic Companion
            </p>
          </div>
        </div>

        {/* Navigation items */}
        {currentUser && (
          <nav style={{ display: "flex", gap: "0.5rem" }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                    padding: "0.5rem 0.9rem",
                    borderRadius: "8px",
                    fontSize: "0.9rem",
                    fontWeight: 500,
                    color: isActive ? "#fff" : "var(--text-muted)",
                    background: isActive ? "var(--primary)" : "transparent",
                    transition: "all 0.15s ease",
                  }}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        )}
      </div>

      {/* Hardware Badge & User Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
        <HardwareStatusBadge hardwareState={hardwareState} />

        {currentUser ? (
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>{currentUser.full_name}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                @{currentUser.username}
              </div>
            </div>
            <button
              onClick={onLogout}
              className="btn-outline"
              style={{ padding: "0.45rem 0.8rem", fontSize: "0.85rem" }}
              title="Logout"
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
