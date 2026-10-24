import React, { useState } from "react";
import { BrainCircuit, Camera, Lock, LogIn, User, UserPlus } from "lucide-react";
import { apiRequest, setAuthToken, setCurrentUser } from "../api/client";

export default function Auth({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState("student1");
  const [password, setPassword] = useState("Password123!");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [institution, setInstitution] = useState("");
  const [course, setCourse] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      const data = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setAuthToken(data.access_token);
      setCurrentUser(data);
      onLoginSuccess(data);
    } catch (err) {
      setErrorMsg(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      const data = await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          full_name: fullName,
          email,
          institution,
          course,
        }),
      });
      setAuthToken(data.access_token);
      setCurrentUser(data);
      onLoginSuccess(data);
    } catch (err) {
      setErrorMsg(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
        background: "radial-gradient(circle at top, #1e1b4b, #0f172a 70%)",
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: "440px",
          width: "100%",
          padding: "2rem",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "14px",
              background: "linear-gradient(135deg, #4f46e5, #06b6d4)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "0.75rem",
            }}
          >
            <BrainCircuit size={32} color="#fff" />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700 }}>AI StudySense</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            {isRegistering ? "Create your student account" : "Sign in with User ID or Biometrics"}
          </p>
        </div>

        {errorMsg && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid #ef4444",
              color: "#fca5a5",
              padding: "0.75rem",
              borderRadius: "8px",
              fontSize: "0.85rem",
              marginBottom: "1rem",
            }}
          >
            {errorMsg}
          </div>
        )}

        <form onSubmit={isRegistering ? handleRegister : handleLogin} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {isRegistering && (
            <>
              <div>
                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Alex Johnson"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Email</label>
                <input
                  type="email"
                  placeholder="student@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>College / Institution</label>
                <input
                  type="text"
                  placeholder="University Name"
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                />
              </div>
            </>
          )}

          <div>
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>User ID / Username</label>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" style={{ justifyContent: "center", marginTop: "0.5rem" }} disabled={loading}>
            {isRegistering ? <UserPlus size={18} /> : <LogIn size={18} />}
            <span>{loading ? "Processing..." : isRegistering ? "Register Account" : "Sign In"}</span>
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
          {isRegistering ? (
            <span>
              Already have an account?{" "}
              <button
                onClick={() => setIsRegistering(false)}
                style={{ background: "transparent", color: "var(--primary)", fontWeight: 600 }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              New student?{" "}
              <button
                onClick={() => setIsRegistering(true)}
                style={{ background: "transparent", color: "var(--primary)", fontWeight: 600 }}
              >
                Register
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
