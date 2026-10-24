import React, { useEffect, useState } from "react";
import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";
import Dashboard from "./pages/dashboard/Dashboard";
import StudyMethods from "./pages/study/StudyMethods";
import StudySession from "./pages/study/StudySession";
import Subjects from "./pages/academics/Subjects";
import Marks from "./pages/academics/Marks";
import Assignments from "./pages/academics/Assignments";
import SyllabusRoadmap from "./pages/syllabus/SyllabusRoadmap";
import AICoach from "./pages/ai/AICoach";
import QuizGenerator from "./pages/ai/QuizGenerator";
import RevisionGenerator from "./pages/ai/RevisionGenerator";
import ResourceFinder from "./pages/ai/ResourceFinder";
import SessionAnalytics from "./pages/analytics/SessionAnalytics";
import StudyHealth from "./pages/analytics/StudyHealth";
import ProfileSettings from "./pages/profile/ProfileSettings";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { getCurrentUser, setAuthToken, setCurrentUser } from "./api/client";
import { createDashboardWebSocket } from "./api/ws";

export default function App() {
  const [currentUser, setCurrentUserState] = useState(getCurrentUser());
  const [authView, setAuthView] = useState("login"); // login | register
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedStudyMethod, setSelectedStudyMethod] = useState("Pomodoro");
  const [selectedSessionData, setSelectedSessionData] = useState({
    topic: "",
    method: "Pomodoro",
    duration: 25,
    break_duration: 5,
    cycles: 4,
  });

  const handleSelectMethodWithData = (method, customData = {}) => {
    setSelectedStudyMethod(method);
    setSelectedSessionData((prev) => ({
      ...prev,
      method: method,
      ...customData,
    }));
  };
  const [hardwareState, setHardwareState] = useState({
    connected: false,
    led_state: "GREEN",
    posture: "good",
    oled_animation: "idle",
  });

  useEffect(() => {
    // Setup real-time WebSocket connection to backend
    const ws = createDashboardWebSocket((msg) => {
      if (msg.type === "HARDWARE_STATUS" || msg.type === "STUDY_TELEMETRY") {
        setHardwareState(msg.data);
      } else if (msg.type === "ESP32_CONNECTED") {
        setHardwareState((prev) => ({ ...prev, connected: true, device_id: msg.device_id }));
      } else if (msg.type === "ESP32_DISCONNECTED") {
        setHardwareState((prev) => ({ ...prev, connected: false }));
      }
    });

    return () => ws.close();
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUserState(user);
    setActivePage("dashboard");
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
    setCurrentUserState(null);
    setAuthView("login");
  };

  if (!currentUser) {
    if (authView === "register") {
      return (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          onSwitchToLogin={() => setAuthView("login")}
        />
      );
    }
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToRegister={() => setAuthView("register")}
      />
    );
  }

  // Get Page Meta
  const pageMetaMap = {
    dashboard: { title: "Overview Dashboard", category: "AI StudySense" },
    "study-methods": { title: "Study Method Frameworks", category: "Study Execution" },
    "study-session": { title: "Live Study Session", category: "Study Execution" },
    subjects: { title: "Course Subjects", category: "Academic Growth" },
    marks: { title: "Marks & Assessment Tracker", category: "Academic Growth" },
    assignments: { title: "Assignments & Deadlines", category: "Academic Growth" },
    roadmap: { title: "Syllabus Checklist Roadmap", category: "Syllabus Intelligence" },
    "ai-coach": { title: "AI Academic Planner & Command Center", category: "Academic Planning" },
    "quiz-generator": { title: "Topic Quiz Generator", category: "AI Academic Tools" },
    "revision-generator": { title: "High-Yield Revision Packages", category: "AI Academic Tools" },
    "resource-finder": { title: "Curated Resource Finder", category: "AI Academic Tools" },
    "session-analytics": { title: "Session Telemetry & History", category: "Analytics" },
    "study-health": { title: "Study Health Score Diagnostic", category: "Analytics" },
    profile: { title: "Student Profile & Face Auth", category: "Account & Settings" },
  };

  const currentMeta = pageMetaMap[activePage] || { title: "AI StudySense", category: "Academic Companion" };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Content Viewport */}
      <div className="main-viewport">
        <Header
          pageTitle={currentMeta.title}
          pageCategory={currentMeta.category}
          setActivePage={setActivePage}
          hardwareState={hardwareState}
        />

        <main className="content-container">
          <ErrorBoundary setActivePage={setActivePage}>
            {activePage === "dashboard" && (
              <Dashboard
                setActivePage={setActivePage}
                hardwareState={hardwareState}
                setSelectedSessionData={setSelectedSessionData}
                onSelectMethod={(m) => handleSelectMethodWithData(m)}
              />
            )}
            {activePage === "study-methods" && (
              <StudyMethods
                setActivePage={setActivePage}
                onSelectMethod={(m, data) => handleSelectMethodWithData(m, data)}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {(activePage === "study-session" || activePage === "session") && (
              <StudySession
                hardwareState={hardwareState}
                initialMethod={selectedStudyMethod}
                initialSessionData={selectedSessionData}
                setActivePage={setActivePage}
              />
            )}
            {activePage === "subjects" && <Subjects />}
            {activePage === "marks" && <Marks />}
            {activePage === "assignments" && <Assignments />}
            {activePage === "roadmap" && (
              <SyllabusRoadmap
                setActivePage={setActivePage}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {activePage === "ai-coach" && (
              <AICoach
                setActivePage={setActivePage}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {activePage === "quiz-generator" && (
              <QuizGenerator
                setActivePage={setActivePage}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {activePage === "revision-generator" && (
              <RevisionGenerator
                setActivePage={setActivePage}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {activePage === "resource-finder" && (
              <ResourceFinder
                setActivePage={setActivePage}
                setSelectedSessionData={setSelectedSessionData}
              />
            )}
            {activePage === "session-analytics" && <SessionAnalytics setActivePage={setActivePage} />}
            {activePage === "study-health" && <StudyHealth setActivePage={setActivePage} />}
            {activePage === "profile" && <ProfileSettings currentUser={currentUser} />}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
