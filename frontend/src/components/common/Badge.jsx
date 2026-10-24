import React from "react";

export function Badge({ children, variant = "neutral", style = {} }) {
  let badgeClass = "status-neutral";
  if (variant === "good" || variant === "success") badgeClass = "status-good";
  else if (variant === "buffer" || variant === "warning") badgeClass = "status-buffer";
  else if (variant === "bad" || variant === "danger") badgeClass = "status-bad";

  return (
    <span className={`status-badge ${badgeClass}`} style={style}>
      {children}
    </span>
  );
}

export function ProgressBar({ value = 0, max = 100, color = "var(--color-sage)", height = 8 }) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div
      style={{
        width: "100%",
        backgroundColor: "var(--bg-surface-soft)",
        borderRadius: height / 2,
        height: `${height}px`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${percentage}%`,
          backgroundColor: color,
          height: "100%",
          borderRadius: height / 2,
          transition: "width 0.3s ease",
        }}
      />
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "3rem 1.5rem",
        backgroundColor: "var(--bg-app)",
        border: "1px dashed var(--border-color)",
        borderRadius: "8px",
      }}
    >
      {Icon && (
        <div style={{ display: "inline-flex", padding: "12px", background: "var(--bg-surface-soft)", borderRadius: "50%", color: "var(--text-muted)", marginBottom: "1rem" }}>
          <Icon size={28} />
        </div>
      )}
      <h4 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "0.4rem" }}>
        {title}
      </h4>
      {description && (
        <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", maxWidth: "400px", margin: "0 auto 1.25rem auto" }}>
          {description}
        </p>
      )}
      {action}
    </div>
  );
}
