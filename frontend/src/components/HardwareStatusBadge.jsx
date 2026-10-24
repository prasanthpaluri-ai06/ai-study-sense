import React from "react";
import { Cpu, Wifi, WifiOff } from "lucide-react";

export default function HardwareStatusBadge({ hardwareState }) {
  const isConnected = hardwareState?.connected;
  const led = hardwareState?.led_state || "GREEN";
  const posture = hardwareState?.posture || "good";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
      {/* ESP32 Connection Badge */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: isConnected ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
          color: isConnected ? "#10b981" : "#ef4444",
          border: `1px solid ${isConnected ? "#10b981" : "#ef4444"}`,
          padding: "4px 12px",
          borderRadius: "20px",
          fontSize: "0.85rem",
          fontWeight: 600,
        }}
      >
        <Cpu size={15} />
        <span>ESP32: {isConnected ? "CONNECTED" : "OFFLINE"}</span>
      </div>

      {/* Traffic Light State */}
      <div className="traffic-light-box" title={`Physical Traffic Light Status: ${led}`}>
        <div
          className={`light-dot red ${led === "RED" ? "active" : ""}`}
          style={{ color: "#ef4444" }}
        />
        <div
          className={`light-dot yellow ${led === "YELLOW" ? "active" : ""}`}
          style={{ color: "#f59e0b" }}
        />
        <div
          className={`light-dot green ${led === "GREEN" ? "active" : ""}`}
          style={{ color: "#10b981" }}
        />
        <span style={{ fontSize: "0.75rem", color: "#94a3b8", marginLeft: "4px", textTransform: "uppercase" }}>
          {posture}
        </span>
      </div>
    </div>
  );
}
