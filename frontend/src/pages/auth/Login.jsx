import React, { useState } from "react";
import Button from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import CameraFaceCapture from "../../components/auth/CameraFaceCapture";
import { apiRequest, setAuthToken, setCurrentUser } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import { BrainCircuit, LogIn, Camera, Lock, User, ArrowLeft, ShieldCheck, KeyRound } from "lucide-react";

export default function Login({ onLoginSuccess, onSwitchToRegister }) {
  // Step 1: Credentials (User ID + Password) | Step 2: Face Recognition
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState("student1");
  const [password, setPassword] = useState("Password123!");
  const [verificationData, setVerificationData] = useState(null);

  // Loading & Error states
  const [credLoading, setCredLoading] = useState(false);
  const [faceVerifying, setFaceVerifying] = useState(false);
  const [faceSuccess, setFaceSuccess] = useState(false);
  const [faceError, setFaceError] = useState(null);
  const [fallbackLoading, setFallbackLoading] = useState(false);
  const toast = useToast();

  // Step 1: Verify User ID + Password
  const handleVerifyCredentials = async (e) => {
    e.preventDefault();
    setCredLoading(true);
    setFaceError(null);
    try {
      const res = await apiRequest("/auth/verify-credentials", {
        method: "POST",
        body: JSON.stringify({
          username: username.trim().toLowerCase(),
          password,
        }),
      });

      setVerificationData(res);
      toast.success("Password verified. Opening camera for face verification...");
      setStep(2); // Proceed to Face Recognition step
    } catch (err) {
      toast.error(err.message || "Invalid User ID or password");
    } finally {
      setCredLoading(false);
    }
  };

  // Step 2: Face Biometric Capture & Verification
  const handleFaceFrameCapture = async (frameBase64) => {
    setFaceVerifying(true);
    setFaceError(null);
    try {
      const tokenData = await apiRequest("/auth/face/login", {
        method: "POST",
        body: JSON.stringify({
          username: verificationData.username,
          session_challenge: verificationData.session_challenge,
          face_image_base64: frameBase64,
        }),
      });

      setFaceSuccess(true);
      setAuthToken(tokenData.access_token);
      setCurrentUser(tokenData);
      toast.success(`Face biometric verified! Welcome back, ${tokenData.full_name}`);
      setTimeout(() => {
        onLoginSuccess(tokenData);
      }, 700);
    } catch (err) {
      setFaceError(err.message || "Face verification failed. Please align your face or use fallback.");
      toast.error("Biometric mismatch");
    } finally {
      setFaceVerifying(false);
    }
  };

  // Secure Fallback Login
  const handleFallbackLogin = async () => {
    setFallbackLoading(true);
    try {
      const tokenData = await apiRequest("/auth/fallback-login", {
        method: "POST",
        body: JSON.stringify({
          username: username.trim().toLowerCase(),
          password,
          reason: "Student initiated password fallback",
        }),
      });
      setAuthToken(tokenData.access_token);
      setCurrentUser(tokenData);
      toast.info(`Fallback authentication successful. Welcome ${tokenData.full_name}`);
      onLoginSuccess(tokenData);
    } catch (err) {
      toast.error(err.message || "Fallback login failed");
    } finally {
      setFallbackLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--bg-app)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
      }}
    >
      <div
        className="card-box"
        style={{
          maxWidth: "440px",
          width: "100%",
          padding: "2.25rem 2rem",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.04)",
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "8px",
              backgroundColor: "var(--color-sage)",
              color: "#FFFFFF",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "0.75rem",
            }}
          >
            <BrainCircuit size={28} />
          </div>
          <h2 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)" }}>
            AI StudySense Login
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "2px" }}>
            {step === 1 ? "Step 1 of 2: User ID & Password" : "Step 2 of 2: Biometric Face Recognition"}
          </p>
        </div>

        {/* Step 1: User ID + Password Form */}
        {step === 1 && (
          <form onSubmit={handleVerifyCredentials}>
            <div className="form-group">
              <label className="form-label">User ID</label>
              <input
                type="text"
                className="form-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. student1"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <Button
              variant="primary"
              type="submit"
              icon={LogIn}
              loading={credLoading}
              style={{ width: "100%", marginTop: "0.75rem" }}
            >
              Verify Credentials &rarr;
            </Button>
          </form>
        )}

        {/* Step 2: Camera Face Recognition */}
        {step === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", alignItems: "center" }}>
            <div style={{ textAlign: "center", width: "100%" }}>
              <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--text-main)" }}>
                Authenticating: {verificationData?.full_name} (@{verificationData?.username})
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Look directly at the laptop camera to verify face embedding.
              </p>
            </div>

            <CameraFaceCapture
              onCaptureFrame={handleFaceFrameCapture}
              isVerifying={faceVerifying}
              verificationSuccess={faceSuccess}
              verificationError={faceError}
            />

            {/* Fallback Option */}
            <div style={{ width: "100%", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <Button
                variant="outline"
                icon={KeyRound}
                loading={fallbackLoading}
                onClick={handleFallbackLogin}
                style={{ width: "100%", fontSize: "0.85rem" }}
              >
                Use Password Fallback Login
              </Button>

              <button
                onClick={() => setStep(1)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.3rem",
                  marginTop: "4px",
                }}
              >
                <ArrowLeft size={14} />
                <span>Back to credentials</span>
              </button>
            </div>
          </div>
        )}

        {/* Switch to Register */}
        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
          New student?{" "}
          <button
            onClick={onSwitchToRegister}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--color-sage)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Register Student Profile
          </button>
        </div>
      </div>
    </div>
  );
}
