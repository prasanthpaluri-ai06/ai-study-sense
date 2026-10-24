import React, { useEffect } from "react";
import { X } from "lucide-react";

export function Modal({ isOpen, onClose, title, children, maxWidth = "540px" }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(45, 40, 36, 0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "8px",
          width: "100%",
          maxWidth,
          boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "1rem 1.25rem",
            borderBottom: "1px solid var(--border-color)",
          }}
        >
          <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{title}</h3>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "4px",
            }}
          >
            <X size={18} />
          </button>
        </div>
        <div style={{ padding: "1.25rem" }}>{children}</div>
      </div>
    </div>
  );
}

export function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "0.4rem",
        borderBottom: "1px solid var(--border-color)",
        marginBottom: "1.5rem",
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.6rem 1rem",
              fontSize: "0.9rem",
              fontWeight: 500,
              background: "transparent",
              color: isActive ? "var(--color-sage)" : "var(--text-muted)",
              borderBottom: `2px solid ${isActive ? "var(--color-sage)" : "transparent"}`,
              marginBottom: "-1px",
              transition: "all 0.15s ease",
            }}
          >
            {Icon && <Icon size={16} />}
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
