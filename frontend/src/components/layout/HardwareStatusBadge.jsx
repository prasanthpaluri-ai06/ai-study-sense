import React from "react";
import { Cpu, Wifi } from "lucide-react";

export default function HardwareStatusBadge({ hardwareState }) {
  const isConnected = hardwareState?.connected;
  const led = hardwareState?.led_state || "GREEN";
  const posture = hardwareState?.posture || "good";

  let statusClass = "status-good";
  if (posture === "buffer" || led === "YELLOW") statusClass = "status-buffer";
  else if (posture === "bad" || led === "RED") statusClass = "status-bad";

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem" }}>
      {/* ESP32 Wi-Fi IoT Status */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.4rem",
          padding: "0.3rem 0.65rem",
          borderRadius: "4px",
          fontSize: "0.8rem",
          fontWeight: 600,
          backgroundColor: isConnected ? "var(--status-good-bg)" : "var(--status-bad-bg)",
          color: isConnected ? "var(--status-good-text)" : "var(--status-bad-text)",
          border: `1px solid ${isConnected ? "var(--status-good-border)" : "var(--status-bad-border)"}`,
        }}
      >
        <Cpu size={14} />
        <span>ESP32: {isConnected ? "CONNECTED" : "STANDBY"}</span>
      </div>

      {/* Traffic Light Solid Physical Indicator */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          padding: "4px 10px",
          borderRadius: "16px",
        }}
        title={`Hardware Traffic Light: ${led}`}
      >
        {/* Red */}
        <div
          style={{
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            backgroundColor: "#B24C3D",
            opacity: led === "RED" ? 1 : 0.25,
          }}
        />
        {/* Yellow */}
        <div
          style={{
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            backgroundColor: "#D4A373",
            opacity: led === "YELLOW" ? 1 : 0.25,
          }}
        />
        {/* Green */}
        <div
          style={{
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            backgroundColor: "#4E6E58",
            opacity: led === "GREEN" ? 1 : 0.25,
          }}
        />
        <span
          style={{
            fontSize: "0.72rem",
            fontWeight: 700,
            textTransform: "uppercase",
            color: "var(--text-muted)",
            marginLeft: "2px",
          }}
        >
          {posture}
        </span>
      </div>
    </div>
  );
}
