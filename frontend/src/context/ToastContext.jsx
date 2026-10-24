import React, { createContext, useContext, useState } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = "info", duration = 4000) => {
    if (!message) return;
    const id = Date.now() + Math.random();
    setToasts((prev) => {
      if (prev.some((t) => t.message === message)) {
        return prev;
      }
      return [...prev, { id, message, type }];
    });

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast, success: (msg) => addToast(msg, "success"), error: (msg) => addToast(msg, "error"), warning: (msg) => addToast(msg, "warning"), info: (msg) => addToast(msg, "info") }}>
      {children}
      {/* Toast Overlay Container */}
      <div
        style={{
          position: "fixed",
          bottom: "1.5rem",
          right: "1.5rem",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
          maxWidth: "380px",
          width: "100%",
        }}
      >
        {toasts.map((toast) => {
          let bg = "var(--bg-surface)";
          let border = "var(--border-color)";
          let text = "var(--text-main)";
          let Icon = Info;
          let iconColor = "var(--color-wood)";

          if (toast.type === "success") {
            bg = "var(--status-good-bg)";
            border = "var(--status-good-border)";
            text = "var(--status-good-text)";
            Icon = CheckCircle2;
            iconColor = "var(--color-sage)";
          } else if (toast.type === "error") {
            bg = "var(--status-bad-bg)";
            border = "var(--status-bad-border)";
            text = "var(--status-bad-text)";
            Icon = AlertCircle;
            iconColor = "var(--color-terracotta)";
          } else if (toast.type === "warning") {
            bg = "var(--status-buffer-bg)";
            border = "var(--status-buffer-border)";
            text = "var(--status-buffer-text)";
            Icon = AlertTriangle;
            iconColor = "var(--status-buffer-text)";
          }

          return (
            <div
              key={toast.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.75rem 1rem",
                background: bg,
                border: `1px solid ${border}`,
                borderRadius: "6px",
                color: text,
                boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                fontSize: "0.9rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <Icon size={18} color={iconColor} />
                <span>{toast.message}</span>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                style={{ background: "transparent", border: "none", color: text, cursor: "pointer", padding: "2px" }}
              >
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
