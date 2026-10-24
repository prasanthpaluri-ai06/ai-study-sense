import React from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleGoDashboard = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.setActivePage) {
      this.props.setActivePage("dashboard");
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "2.5rem 1.5rem", maxWidth: "720px", margin: "0 auto" }}>
          <div
            style={{
              background: "var(--color-surface, #ffffff)",
              border: "1px solid var(--color-border, #e5e0d8)",
              borderRadius: "16px",
              padding: "2rem",
              boxShadow: "0 8px 24px rgba(60, 50, 40, 0.06)",
              textAlign: "center",
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                background: "rgba(224, 114, 91, 0.12)",
                color: "var(--color-terracotta, #e0725b)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 1.25rem",
              }}
            >
              <AlertTriangle size={28} />
            </div>

            <h2
              style={{
                fontSize: "1.35rem",
                fontWeight: 600,
                color: "var(--color-charcoal, #2d2a26)",
                marginBottom: "0.5rem",
              }}
            >
              {this.props.fallbackTitle || "Something went wrong in this view"}
            </h2>

            <p
              style={{
                color: "var(--color-muted, #7c7267)",
                fontSize: "0.925rem",
                marginBottom: "1.5rem",
                lineHeight: 1.5,
              }}
            >
              An unexpected error occurred while rendering this component. You can reload this section or return to the overview dashboard.
            </p>

            {this.state.error && (
              <div
                style={{
                  textAlign: "left",
                  background: "var(--color-sand-light, #f7f5f0)",
                  border: "1px solid var(--color-border, #e5e0d8)",
                  borderRadius: "10px",
                  padding: "1rem",
                  marginBottom: "1.5rem",
                  fontFamily: "monospace",
                  fontSize: "0.825rem",
                  color: "var(--color-terracotta, #c05844)",
                  overflowX: "auto",
                  maxHeight: "180px",
                }}
              >
                <strong>{this.state.error.toString()}</strong>
                {this.state.errorInfo?.componentStack && (
                  <pre style={{ marginTop: "0.5rem", color: "#666", fontSize: "0.75rem", whiteSpace: "pre-wrap" }}>
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
              <button
                onClick={this.handleReset}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "0.65rem 1.25rem",
                  borderRadius: "10px",
                  border: "1px solid var(--color-border, #dcd5cc)",
                  background: "var(--color-surface, #ffffff)",
                  color: "var(--color-charcoal, #2d2a26)",
                  cursor: "pointer",
                  fontWeight: 500,
                  fontSize: "0.9rem",
                }}
              >
                <RefreshCw size={16} /> Try Again
              </button>

              <button
                onClick={this.handleGoDashboard}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "0.65rem 1.25rem",
                  borderRadius: "10px",
                  border: "none",
                  background: "var(--color-sage, #5a7d65)",
                  color: "#ffffff",
                  cursor: "pointer",
                  fontWeight: 500,
                  fontSize: "0.9rem",
                }}
              >
                <Home size={16} /> Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
