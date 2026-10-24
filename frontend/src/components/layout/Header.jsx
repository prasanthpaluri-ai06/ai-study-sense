import React, { useEffect, useState } from "react";
import HardwareStatusBadge from "./HardwareStatusBadge";
import Button from "../common/Button";
import { Play, Clock, Calendar } from "lucide-react";
import { formatDate, formatTime, getUserTimeZone } from "../../utils/dateUtils";

export default function Header({ pageTitle, pageCategory = "AI StudySense", setActivePage, hardwareState }) {
  const [currentRealTime, setCurrentRealTime] = useState(new Date());

  // Real-time ticking clock synchronized with system time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentRealTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const timeZoneName = getUserTimeZone();
  const shortTz = timeZoneName === "Asia/Kolkata" ? "IST" : timeZoneName.split("/").pop()?.replace(/_/g, " ") || "Local";

  return (
    <header
      style={{
        height: "var(--header-height)",
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-color)",
        padding: "0 2rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 30,
        gap: "1rem",
      }}
    >
      <div>
        <div style={{ fontSize: "0.72rem", color: "var(--text-subtle)", textTransform: "uppercase", letterSpacing: "0.04em", fontWeight: 600 }}>
          {pageCategory}
        </div>
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)", marginTop: "-2px" }}>
          {pageTitle}
        </h2>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        {/* Dynamic Real-Time Date & Clock Badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "4px 10px",
            backgroundColor: "var(--bg-app)",
            border: "1px solid var(--border-color)",
            borderRadius: "6px",
            fontSize: "0.8rem",
            color: "var(--text-main)",
          }}
          title={`System Real-Time Clock • Timezone: ${timeZoneName}`}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
            <Calendar size={13} color="var(--color-sage)" />
            <span>{formatDate(currentRealTime, { weekday: "short", month: "short", day: "numeric", year: "numeric" })}</span>
          </div>
          <div style={{ width: "1px", height: "12px", backgroundColor: "var(--border-color)" }} />
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontFamily: "monospace", fontWeight: 600 }}>
            <Clock size={13} color="var(--color-terracotta)" />
            <span>{formatTime(currentRealTime, true)}</span>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 400 }}>({shortTz})</span>
          </div>
        </div>

        <HardwareStatusBadge hardwareState={hardwareState} />

        <Button
          size="sm"
          variant="primary"
          icon={Play}
          onClick={() => setActivePage("study-session")}
        >
          Study Session
        </Button>
      </div>
    </header>
  );
}
