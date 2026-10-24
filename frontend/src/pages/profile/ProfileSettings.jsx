import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import { User, Camera, Cpu, Save, ShieldCheck, CheckCircle2 } from "lucide-react";

export default function ProfileSettings({ currentUser }) {
  const [profile, setProfile] = useState({
    institution: "",
    course: "",
    year: "",
    semester: "",
    target_study_hours_daily: 4,
    preferred_method: "Pomodoro",
  });
  const [hasFaceEnrolled, setHasFaceEnrolled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [faceEnrolling, setFaceEnrolling] = useState(false);
  const toast = useToast();

  useEffect(() => {
    async function loadProfile() {
      try {
        const user = await apiRequest("/users/me");
        if (user.profile) {
          setProfile(user.profile);
        }
        setHasFaceEnrolled(user.has_face_enrolled);
      } catch (err) {
        console.error(err);
      }
    }
    loadProfile();
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiRequest("/users/me/profile", {
        method: "PUT",
        body: JSON.stringify(profile),
      });
      toast.success("Student profile updated successfully");
    } catch (err) {
      toast.error(err.message || "Failed saving profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateFaceEnrollment = async () => {
    setFaceEnrolling(true);
    try {
      // Generate a 128-d mock embedding vector for biometric demonstration
      const mockVector = Array.from({ length: 128 }, () => Math.random() * 0.2 + 0.1);
      await apiRequest("/auth/face/enroll", {
        method: "POST",
        body: JSON.stringify({ face_embedding: mockVector }),
      });
      setHasFaceEnrolled(true);
      toast.success("Face biometric template registered successfully!");
    } catch (err) {
      toast.error("Failed registering face embedding");
    } finally {
      setFaceEnrolling(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
          Student Profile & Hardware Settings
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
          Manage your academic institution, face biometric credentials, and ESP32 parameters.
        </p>
      </div>

      <div className="grid-cols-2">
        {/* Left: Academic Profile */}
        <Card title="Academic Profile" subtitle="University and study preferences" icon={User}>
          <form onSubmit={handleSaveProfile}>
            <div className="form-group">
              <label className="form-label">College / University</label>
              <input
                type="text"
                className="form-input"
                value={profile.institution || ""}
                onChange={(e) => setProfile({ ...profile, institution: e.target.value })}
                placeholder="University Name"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Degree / Program</label>
              <input
                type="text"
                className="form-input"
                value={profile.course || ""}
                onChange={(e) => setProfile({ ...profile, course: e.target.value })}
                placeholder="e.g. B.Tech Computer Science"
              />
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Academic Year</label>
                <input
                  type="text"
                  className="form-input"
                  value={profile.year || ""}
                  onChange={(e) => setProfile({ ...profile, year: e.target.value })}
                  placeholder="3rd Year"
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Semester</label>
                <input
                  type="text"
                  className="form-input"
                  value={profile.semester || ""}
                  onChange={(e) => setProfile({ ...profile, semester: e.target.value })}
                  placeholder="6th Semester"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Daily Target Study Hours</label>
              <input
                type="number"
                min="1"
                max="16"
                className="form-input"
                value={profile.target_study_hours_daily || 4}
                onChange={(e) => setProfile({ ...profile, target_study_hours_daily: parseInt(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Preferred Study Method</label>
              <select
                className="form-select"
                value={profile.preferred_method || "Pomodoro"}
                onChange={(e) => setProfile({ ...profile, preferred_method: e.target.value })}
              >
                <option value="Pomodoro">Pomodoro (25/5)</option>
                <option value="52/17">52/17 Method</option>
                <option value="Active Recall">Active Recall</option>
                <option value="Spaced Repetition">Spaced Repetition</option>
                <option value="Feynman Technique">Feynman Technique</option>
              </select>
            </div>

            <Button
              variant="primary"
              type="submit"
              icon={Save}
              loading={loading}
              style={{ marginTop: "0.5rem" }}
            >
              Save Profile
            </Button>
          </form>
        </Card>

        {/* Right: Face Biometrics & Hardware Setup */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Face Biometrics Card */}
          <Card
            title="Biometric Face Authentication"
            subtitle="Enroll face vector embedding for passwordless authentication."
            icon={Camera}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "1rem",
                backgroundColor: hasFaceEnrolled ? "var(--status-good-bg)" : "var(--status-buffer-bg)",
                border: `1px solid ${hasFaceEnrolled ? "var(--status-good-border)" : "var(--status-buffer-border)"}`,
                borderRadius: "6px",
                marginBottom: "1rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <ShieldCheck size={24} color={hasFaceEnrolled ? "var(--color-sage)" : "var(--status-buffer-text)"} />
                <div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 700, color: hasFaceEnrolled ? "var(--status-good-text)" : "var(--status-buffer-text)" }}>
                    {hasFaceEnrolled ? "Face Biometrics Active" : "No Face Template Enrolled"}
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    {hasFaceEnrolled ? "128-d cosine vector stored securely" : "Enroll face via camera to enable biometric login"}
                  </div>
                </div>
              </div>
              <Badge variant={hasFaceEnrolled ? "good" : "warning"}>
                {hasFaceEnrolled ? "Enrolled" : "Pending"}
              </Badge>
            </div>

            <Button
              variant="outline"
              icon={Camera}
              loading={faceEnrolling}
              onClick={handleSimulateFaceEnrollment}
            >
              {hasFaceEnrolled ? "Re-calibrate Face Template" : "Enroll Face via Camera"}
            </Button>
          </Card>

          {/* Hardware Configuration */}
          <Card
            title="ESP32 IoT Bridge Parameters"
            subtitle="Wireless microcontroller configuration"
            icon={Cpu}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", fontSize: "0.88rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.4rem" }}>
                <span style={{ color: "var(--text-muted)" }}>WebSocket Path:</span>
                <code>/ws/esp32</code>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.4rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Posture Buffer Window:</span>
                <strong>5.0 seconds</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.4rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Bad Posture Threshold:</span>
                <strong>10.0 seconds</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>OLED Model:</span>
                <strong>SSD1306 (128x64 I2C)</strong>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
