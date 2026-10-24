import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import { Badge } from "../common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Cpu,
  Wifi,
  WifiOff,
  Radio,
  RefreshCw,
  Send,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Clock,
  Sparkles,
  Layers,
} from "lucide-react";

export default function HardwareControlDeck({ hardwareState, onStateChange }) {
  const [loading, setLoading] = useState(false);
  const [pingLoading, setPingLoading] = useState(false);
  const [customMessage, setCustomMessage] = useState("");
  const [selectedAnimation, setSelectedAnimation] = useState("good_posture");
  const [selectedLed, setSelectedLed] = useState("GREEN");
  const [liveStatus, setLiveStatus] = useState(hardwareState || {});

  const toast = useToast();

  const fetchStatus = async () => {
    try {
      const res = await apiRequest("/hardware/status");
      setLiveStatus(res);
      if (onStateChange) onStateChange(res);
    } catch (err) {
      console.error("Failed to fetch hardware status:", err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const executeTest = async (led, anim, msg) => {
    try {
      setLoading(true);
      const res = await apiRequest("/hardware/test-mode", {
        method: "POST",
        body: JSON.stringify({
          led_state: led,
          oled_animation: anim,
          custom_message: msg || undefined,
        }),
      });
      setLiveStatus(res.state);
      if (onStateChange) onStateChange(res.state);
      toast.success(`Dispatched: ${led} (${anim})`);
    } catch (err) {
      toast.error("Failed to send test command to hardware");
    } finally {
      setLoading(false);
    }
  };

  const pingDevices = async () => {
    try {
      setPingLoading(true);
      const res = await apiRequest("/hardware/ping", { method: "POST" });
      if (res.status === "disconnected") {
        toast.info("No active ESP32 device connected via Wi-Fi");
      } else {
        toast.success(`Ping sent to ${res.active_devices} connected ESP32(s)`);
      }
      fetchStatus();
    } catch (err) {
      toast.error("Ping request failed");
    } finally {
      setPingLoading(false);
    }
  };

  const isConnected = liveStatus.connected || false;
  const activeDevice = (liveStatus.devices && liveStatus.devices[0]) || null;
  const currentLed = (liveStatus.led_state || "GREEN").toUpperCase();
  const currentExpression = liveStatus.oled_expression || (
    currentLed === "GREEN" ? "^_^" : (currentLed === "YELLOW" ? "-_-" : ">_<")
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Top Hardware Status Header */}
      <Card
        title="Physical AI StudySense Hardware Controller"
        subtitle="ESP32 Wireless Module (Wi-Fi WebSocket) + 0.96″ OLED Display (SSD1306) + Traffic Light"
        icon={Cpu}
        action={
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <Button
              size="sm"
              variant="outline"
              icon={RefreshCw}
              onClick={pingDevices}
              disabled={pingLoading}
            >
              {pingLoading ? "Pinging..." : "Ping ESP32"}
            </Button>
            {isConnected ? (
              <Badge variant="good" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <Wifi size={14} /> ESP32 CONNECTED
              </Badge>
            ) : (
              <Badge variant="danger" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <WifiOff size={14} /> ESP32 DISCONNECTED
              </Badge>
            )}
          </div>
        }
      >
        <div className="grid-cols-3" style={{ gap: "1rem" }}>
          {/* 1. Device Telemetry Info */}
          <div
            style={{
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              Device Connection
            </div>
            <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-main)" }}>
              {liveStatus.device_id || (isConnected ? "esp32_studysense" : "No device paired")}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Status: <strong style={{ color: isConnected ? "var(--color-sage)" : "var(--color-terracotta)" }}>
                {isConnected ? "Active (Wi-Fi WebSocket)" : "Offline / Waiting for ESP32"}
              </strong>
            </div>
            {activeDevice && (
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                Firmware: v{activeDevice.firmware_version} &bull; Heap: {Math.round((activeDevice.free_heap_bytes || 220000) / 1024)} KB &bull; RSSI: {activeDevice.rssi_dbm || -52} dBm
              </div>
            )}
          </div>

          {/* 2. Physical Traffic Light Simulator */}
          <div
            style={{
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.6rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              Traffic Light (GPIO 18/19/23)
            </div>
            <div
              style={{
                display: "flex",
                gap: "0.75rem",
                padding: "0.5rem 1rem",
                backgroundColor: "#222222",
                borderRadius: "20px",
                border: "2px solid #333333",
              }}
            >
              {/* Red Lamp */}
              <div
                style={{
                  width: "18px",
                  height: "18px",
                  borderRadius: "50%",
                  backgroundColor: currentLed === "RED" ? "#FF4D4D" : "#4A1A1A",
                  boxShadow: currentLed === "RED" ? "0 0 10px #FF4D4D" : "none",
                  transition: "all 0.3s ease",
                }}
                title="RED (Bad Posture / Critical Alert)"
              />
              {/* Yellow Lamp */}
              <div
                style={{
                  width: "18px",
                  height: "18px",
                  borderRadius: "50%",
                  backgroundColor: currentLed === "YELLOW" ? "#FFC107" : "#4A3E10",
                  boxShadow: currentLed === "YELLOW" ? "0 0 10px #FFC107" : "none",
                  transition: "all 0.3s ease",
                }}
                title="YELLOW (Buffer Warning / Sit Straight)"
              />
              {/* Green Lamp */}
              <div
                style={{
                  width: "18px",
                  height: "18px",
                  borderRadius: "50%",
                  backgroundColor: currentLed === "GREEN" ? "#4CAF50" : "#1B3B1D",
                  boxShadow: currentLed === "GREEN" ? "0 0 10px #4CAF50" : "none",
                  transition: "all 0.3s ease",
                }}
                title="GREEN (Optimal Posture / Flow State)"
              />
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-main)" }}>
              Active Output: <span style={{ color: currentLed === "GREEN" ? "var(--color-sage)" : (currentLed === "YELLOW" ? "var(--color-sand)" : "var(--color-terracotta)") }}>{currentLed}</span>
            </div>
          </div>

          {/* 3. Simulated 0.96" OLED Screen (128x64) */}
          <div
            style={{
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              0.96″ OLED Screen (SSD1306)
            </div>
            <div
              style={{
                width: "100%",
                maxWidth: "180px",
                height: "80px",
                backgroundColor: "#0D1117",
                border: "2px solid #30363D",
                borderRadius: "4px",
                padding: "6px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                alignItems: "center",
                fontFamily: "monospace",
                color: "#58A6FF",
                boxShadow: "inset 0 0 8px rgba(0,0,0,0.8)",
              }}
            >
              <div style={{ fontSize: "0.68rem", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase" }}>
                {liveStatus.oled_title || "AI STUDYSENSE"}
              </div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#7EE787" }}>
                {currentExpression}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", width: "100%", fontSize: "0.62rem", color: "#8B949E" }}>
                <span>{liveStatus.oled_subtitle || "Optimal"}</span>
                <span>{liveStatus.timer_formatted || "25:00"}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Hardware Test Mode Controls */}
      <Card
        title="Hardware Verification & Test Mode"
        subtitle="Test individual LED pins and OLED screen expressions before starting live sessions."
        icon={Sparkles}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Click a preset below to instantly dispatch the structured JSON frame to the ESP32:
          </div>

          {/* Preset 1-Click Buttons */}
          <div style={{ display: "flex", gap: "0.65rem", flexWrap: "wrap" }}>
            <Button
              variant="outline"
              style={{ backgroundColor: "var(--status-good-bg)", borderColor: "var(--status-good-border)", color: "var(--status-good-text)" }}
              onClick={() => executeTest("GREEN", "good_posture", "GOOD POSTURE")}
              disabled={loading}
            >
              🟢 GREEN: Good Posture (^_^)
            </Button>

            <Button
              variant="outline"
              style={{ backgroundColor: "var(--status-buffer-bg)", borderColor: "var(--status-buffer-border)", color: "var(--status-buffer-text)" }}
              onClick={() => executeTest("YELLOW", "buffer_warning", "SIT STRAIGHT")}
              disabled={loading}
            >
              🟡 YELLOW: Buffer Warning (-_-)
            </Button>

            <Button
              variant="outline"
              style={{ backgroundColor: "var(--status-bad-bg)", borderColor: "var(--status-bad-border)", color: "var(--status-bad-text)" }}
              onClick={() => executeTest("RED", "bad_posture", "POSTURE ALERT")}
              disabled={loading}
            >
              🔴 RED: Bad Posture (&gt;_&lt;)
            </Button>

            <Button
              variant="outline"
              onClick={() => executeTest("GREEN", "focus_warning", "EYES ON SCREEN")}
              disabled={loading}
            >
              👁️ Focus Warning (O.O)
            </Button>

            <Button
              variant="outline"
              onClick={() => executeTest("GREEN", "break_time", "REST BREAK")}
              disabled={loading}
            >
              ☕ Break Time (Zzz)
            </Button>

            <Button
              variant="outline"
              onClick={() => executeTest("GREEN", "session_complete", "SESSION DONE")}
              disabled={loading}
            >
              🏆 Session Complete (★_★)
            </Button>
          </div>

          {/* Custom Command Builder */}
          <div
            style={{
              display: "flex",
              gap: "0.75rem",
              alignItems: "center",
              flexWrap: "wrap",
              paddingTop: "0.5rem",
              borderTop: "1px solid var(--border-subtle)",
            }}
          >
            <select
              value={selectedLed}
              onChange={(e) => setSelectedLed(e.target.value)}
              style={{
                padding: "0.45rem 0.65rem",
                borderRadius: "4px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-app)",
                fontSize: "0.85rem",
                color: "var(--text-main)",
              }}
            >
              <option value="GREEN">LED: GREEN</option>
              <option value="YELLOW">LED: YELLOW</option>
              <option value="RED">LED: RED</option>
              <option value="OFF">LED: OFF</option>
            </select>

            <select
              value={selectedAnimation}
              onChange={(e) => setSelectedAnimation(e.target.value)}
              style={{
                padding: "0.45rem 0.65rem",
                borderRadius: "4px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-app)",
                fontSize: "0.85rem",
                color: "var(--text-main)",
              }}
            >
              <option value="good_posture">OLED: Good Posture (^_^)</option>
              <option value="buffer_warning">OLED: Buffer Warning (-_-)</option>
              <option value="bad_posture">OLED: Bad Posture (&gt;_&lt;)</option>
              <option value="focus_warning">OLED: Focus Warning (O.O)</option>
              <option value="break_time">OLED: Break Time (Zzz)</option>
              <option value="session_complete">OLED: Complete (★_★)</option>
              <option value="idle">OLED: Ready / Idle</option>
            </select>

            <input
              type="text"
              placeholder="Custom OLED message..."
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              style={{
                padding: "0.45rem 0.75rem",
                borderRadius: "4px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-app)",
                fontSize: "0.85rem",
                flex: 1,
                minWidth: "160px",
                color: "var(--text-main)",
              }}
            />

            <Button
              variant="primary"
              size="sm"
              icon={Send}
              onClick={() => executeTest(selectedLed, selectedAnimation, customMessage)}
              disabled={loading}
            >
              Dispatch Custom
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
