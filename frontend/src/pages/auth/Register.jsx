import React, { useState } from "react";
import Button from "../../components/common/Button";
import CameraFaceCapture from "../../components/auth/CameraFaceCapture";
import { apiRequest, setAuthToken, setCurrentUser } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import { BrainCircuit, UserPlus, LogIn, ArrowRight, ArrowLeft, Camera, CheckCircle2, ShieldCheck, AlertCircle } from "lucide-react";

export default function Register({ onRegisterSuccess, onSwitchToLogin }) {
  // Step 1: Account Details | Step 2: Face Biometrics Enrollment
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
    confirm_password: "",
    institution: "",
    face_image_base64: null,
  });

  const [loading, setLoading] = useState(false);
  const [faceValidating, setFaceValidating] = useState(false);
  const [faceCaptured, setFaceCaptured] = useState(false);
  const [faceStatusMsg, setFaceStatusMsg] = useState(null);
  const [faceErrorMsg, setFaceErrorMsg] = useState(null);
  const toast = useToast();

  const handleDetailsSubmit = (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) {
      toast.error("Passwords do not match. Please verify.");
      return;
    }
    if (formData.password.length < 6) {
      toast.error("Password must be at least 6 characters long.");
      return;
    }
    setStep(2); // Proceed to Face Registration step
  };

  const handleFaceCaptured = async (frameBase64) => {
    setFaceValidating(true);
    setFaceErrorMsg(null);
    setFaceStatusMsg(null);

    try {
      // Validate frame with backend
      const res = await apiRequest("/auth/face/validate", {
        method: "POST",
        body: JSON.stringify({ face_image_base64: frameBase64 }),
      });

      if (res.valid) {
        setFormData((prev) => ({ ...prev, face_image_base64: frameBase64 }));
        setFaceCaptured(true);
        setFaceStatusMsg("Face detected & biometric template created successfully!");
        toast.success("Face verified and template ready!");
      } else {
        setFaceCaptured(false);
        setFaceErrorMsg(res.message || "Face detection failed. Please align your face and ensure good lighting.");
        toast.error(res.message || "Face detection failed");
      }
    } catch (err) {
      setFaceCaptured(false);
      setFaceErrorMsg(err.message || "Error validating face frame.");
      toast.error("Face validation error");
    } finally {
      setFaceValidating(false);
    }
  };

  const handleFinalRegister = async (skipFace = false) => {
    setLoading(true);
    try {
      const payload = {
        full_name: formData.full_name,
        username: formData.username,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirm_password,
        institution: formData.institution || null,
        face_image_base64: skipFace ? null : formData.face_image_base64,
      };

      const data = await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setAuthToken(data.access_token);
      setCurrentUser(data);
      toast.success(`Account created! Welcome to AI StudySense, ${data.full_name}`);
      onRegisterSuccess(data);
    } catch (err) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
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
        padding: "2rem 1.5rem",
      }}
    >
      <div
        className="card-box"
        style={{
          maxWidth: "480px",
          width: "100%",
          padding: "2.25rem 2rem",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.04)",
        }}
      >
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
            Create Student Profile
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "2px" }}>
            {step === 1 ? "Step 1 of 2: Account Details" : "Step 2 of 2: Face Biometrics Registration"}
          </p>
        </div>

        {/* Step 1: Form details */}
        {step === 1 && (
          <form onSubmit={handleDetailsSubmit}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Alex Rivera"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
              />
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">User ID (Username)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="alexr"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="alex@university.edu"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Confirm Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={formData.confirm_password}
                  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">College / Institution</label>
              <input
                type="text"
                className="form-input"
                placeholder="University or College Name"
                value={formData.institution}
                onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
              />
            </div>

            <Button
              variant="primary"
              type="submit"
              style={{ width: "100%", marginTop: "0.5rem" }}
            >
              Continue to Face Registration &rarr;
            </Button>
          </form>
        )}

        {/* Step 2: Face Biometrics Registration */}
        {step === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", alignItems: "center" }}>
            <div style={{ textAlign: "center", width: "100%" }}>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                Position your face within the guide reticle in good lighting, then click <strong>Scan & Register Face</strong>.
              </p>
            </div>

            <CameraFaceCapture
              onCaptureFrame={handleFaceCaptured}
              isVerifying={faceValidating}
              verificationSuccess={faceCaptured}
              verificationError={faceErrorMsg}
              buttonText="Scan & Register Face"
            />

            {faceStatusMsg && (
              <div
                style={{
                  fontSize: "0.85rem",
                  color: "var(--status-good-text)",
                  backgroundColor: "var(--status-good-bg)",
                  border: "1px solid var(--status-good-border)",
                  padding: "0.5rem 0.75rem",
                  borderRadius: "6px",
                  width: "100%",
                  textAlign: "center",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.4rem",
                }}
              >
                <CheckCircle2 size={16} />
                <span>{faceStatusMsg}</span>
              </div>
            )}

            <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "0.6rem", marginTop: "0.5rem" }}>
              <Button
                variant="primary"
                loading={loading}
                icon={UserPlus}
                onClick={() => handleFinalRegister(false)}
                disabled={!faceCaptured}
                style={{ width: "100%" }}
              >
                Complete Registration with Face
              </Button>

              <Button
                variant="ghost"
                onClick={() => handleFinalRegister(true)}
                disabled={loading}
                style={{ width: "100%", fontSize: "0.82rem" }}
              >
                Skip Face Registration for Now
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
                <span>Back to edit details</span>
              </button>
            </div>
          </div>
        )}

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
          Already have an account?{" "}
          <button
            onClick={onSwitchToLogin}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--color-sage)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
}
