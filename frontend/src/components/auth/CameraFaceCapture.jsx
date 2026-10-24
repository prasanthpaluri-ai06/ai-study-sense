import React, { useEffect, useRef, useState } from "react";
import Button from "../common/Button";
import { Badge } from "../common/Badge";
import { Camera, RefreshCw, AlertCircle, CheckCircle2, ShieldCheck, VideoOff, SunMedium } from "lucide-react";

/**
 * CameraFaceCapture Component
 * Manages webcam lifecycle, canvas frame capture, and displays explicit camera states:
 * - "Camera permission required"
 * - "Searching for face"
 * - "Face detected"
 * - "Verifying"
 * - "Verified"
 * - "Verification failed"
 */
export default function CameraFaceCapture({
  onCaptureFrame,
  isVerifying = false,
  verificationSuccess = false,
  verificationError = null,
  buttonText = "Scan & Verify Face",
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraState, setCameraState] = useState("Camera permission required");
  const [permissionDenied, setPermissionDenied] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function initWebcam() {
      setCameraState("Camera permission required");
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
          audio: false,
        });

        if (!mounted) {
          mediaStream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = mediaStream;
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          videoRef.current.play().catch((e) => console.log("Auto-play error:", e));
        }
        setCameraState("Searching for face");
        setPermissionDenied(false);

        setTimeout(() => {
          if (mounted) {
            setCameraState("Face detected");
          }
        }, 1000);
      } catch (err) {
        console.warn("Camera access failed:", err);
        if (mounted) {
          setPermissionDenied(true);
          setCameraState("Camera permission required");
        }
      }
    }

    initWebcam();

    return () => {
      mounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (isVerifying) {
      setCameraState("Verifying");
    } else if (verificationSuccess) {
      setCameraState("Verified");
    } else if (verificationError) {
      setCameraState("Verification failed");
    }
  }, [isVerifying, verificationSuccess, verificationError]);

  const captureFrameBase64 = () => {
    if (!videoRef.current || !canvasRef.current) return null;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const w = video.videoWidth || 480;
    const h = video.videoHeight || 360;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    // Draw unmirrored onto canvas
    ctx.drawImage(video, 0, 0, w, h);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.90);
    return dataUrl;
  };

  const handleManualCapture = () => {
    const frame = captureFrameBase64();
    if (frame && onCaptureFrame) {
      onCaptureFrame(frame);
    }
  };

  let stateBadgeVariant = "neutral";
  if (cameraState === "Verified") stateBadgeVariant = "good";
  else if (cameraState === "Verifying" || cameraState === "Searching for face") stateBadgeVariant = "warning";
  else if (cameraState === "Verification failed" || permissionDenied) stateBadgeVariant = "danger";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", alignItems: "center", width: "100%" }}>
      {/* Video Viewport with Target Framing Reticle */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "360px",
          height: "260px",
          backgroundColor: "#2D2824",
          borderRadius: "8px",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: `2px solid ${
            cameraState === "Verified"
              ? "var(--color-sage)"
              : cameraState === "Verification failed"
              ? "var(--color-terracotta)"
              : "var(--border-color)"
          }`,
        }}
      >
        {permissionDenied ? (
          <div style={{ textAlign: "center", padding: "1.5rem", color: "#EDE7DE" }}>
            <VideoOff size={36} color="var(--color-terracotta)" style={{ marginBottom: "0.5rem" }} />
            <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>Camera Permission Needed</div>
            <div style={{ fontSize: "0.78rem", color: "#A8A196", marginTop: "4px", lineHeight: 1.4 }}>
              Please allow browser webcam permissions in your browser URL bar or use the password fallback option.
            </div>
          </div>
        ) : (
          <video
            ref={videoRef}
            playsInline
            muted
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: "scaleX(-1)", // mirror view for intuitive alignment
            }}
          />
        )}

        {/* Framing Guide Reticle */}
        {!permissionDenied && (
          <div
            style={{
              position: "absolute",
              width: "170px",
              height: "200px",
              border: `2px dashed ${cameraState === "Verified" ? "var(--color-sage)" : "#E5DFD3"}`,
              borderRadius: "50%",
              pointerEvents: "none",
              boxShadow: cameraState === "Verified" ? "0 0 15px rgba(118, 139, 110, 0.4)" : "none",
            }}
          />
        )}

        {/* Hidden Canvas for Frame Grab */}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      {/* Explicit Camera State Display */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ fontSize: "0.82rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
          Status:
        </span>
        <Badge variant={stateBadgeVariant}>
          {cameraState}
        </Badge>
      </div>

      {verificationError && (
        <div
          style={{
            fontSize: "0.82rem",
            color: "var(--status-bad-text)",
            backgroundColor: "var(--status-bad-bg)",
            border: "1px solid var(--status-bad-border)",
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            width: "100%",
            textAlign: "center",
          }}
        >
          {verificationError}
        </div>
      )}

      {/* Capture trigger button */}
      {!permissionDenied && (
        <Button
          variant="primary"
          icon={Camera}
          loading={isVerifying}
          onClick={handleManualCapture}
          style={{ width: "100%", maxWidth: "360px" }}
        >
          {isVerifying ? "Verifying Face..." : buttonText}
        </Button>
      )}
    </div>
  );
}
