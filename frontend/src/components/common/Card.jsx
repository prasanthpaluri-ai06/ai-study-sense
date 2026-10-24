import React from "react";

export default function Card({
  title,
  subtitle,
  icon: Icon,
  action,
  children,
  className = "",
  style = {},
  headerStyle = {},
}) {
  return (
    <div className={`card-box ${className}`} style={style}>
      {(title || subtitle || action || Icon) && (
        <div className="card-box-header" style={headerStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            {Icon && (
              <div
                style={{
                  background: "var(--color-sage-soft)",
                  color: "var(--color-sage)",
                  padding: "6px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Icon size={18} />
              </div>
            )}
            <div>
              {title && <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{title}</h3>}
              {subtitle && <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "2px" }}>{subtitle}</p>}
            </div>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
