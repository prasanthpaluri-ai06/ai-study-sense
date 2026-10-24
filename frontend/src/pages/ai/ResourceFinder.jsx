import React, { useState } from "react";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Badge, EmptyState } from "../../components/common/Badge";
import { apiRequest } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import {
  Search,
  ExternalLink,
  Video,
  FileText,
  Code2,
  BookOpen,
  Sparkles,
  Globe,
  PlayCircle,
  Compass,
} from "lucide-react";

export default function ResourceFinder({ setActivePage, setSelectedSessionData }) {
  const [query, setQuery] = useState("Binary Search");
  const [resourceData, setResourceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await apiRequest(`/ai/resources?query=${encodeURIComponent(query.trim())}`);
      setResourceData(res);
      toast.success(`Found verified resources for ${res.topic}`);
    } catch (err) {
      toast.error(err.message || "Failed finding resources.");
    } finally {
      setLoading(false);
    }
  };

  const startTopicStudy = (topicTitle) => {
    if (setSelectedSessionData) {
      setSelectedSessionData({
        topic: topicTitle,
        method: "Active Recall",
      });
    }
    if (setActivePage) {
      setActivePage("session");
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "Videos":
        return Video;
      case "Practice":
        return Code2;
      case "Educational Websites":
        return Globe;
      case "Documentation":
        return FileText;
      default:
        return BookOpen;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-main)" }}>
          AI Academic Resource Finder
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
          Curated conceptual video lectures, peer-reviewed educational sites, authoritative documentation, and practice problem sets.
        </p>
      </div>

      {/* Search Input Card */}
      <Card>
        <form onSubmit={handleSearch} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: "260px" }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search topic (e.g. Binary Search, AVL Trees, Dynamic Programming, Bayes Theorem, Dijkstra's Algorithm)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
              />
            </div>
            <Button
              variant="primary"
              type="submit"
              icon={Search}
              loading={loading}
            >
              {loading ? "Searching Verified Sources..." : "Find Verified Resources"}
            </Button>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", fontSize: "0.82rem", color: "var(--text-muted)" }}>
            <span>Popular Queries:</span>
            {["Binary Search", "AVL Trees", "Dijkstra's Algorithm", "Bayes Theorem", "Process Scheduling"].map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => {
                  setQuery(tag);
                }}
                style={{
                  background: "var(--bg-app)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "12px",
                  padding: "2px 8px",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  color: "var(--color-sage)",
                  fontWeight: 500,
                }}
              >
                {tag}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {/* Results View */}
      {resourceData && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* AI Pedagogical Guidance Banner */}
          <Card style={{ backgroundColor: "var(--color-sage-soft)", border: "1px solid var(--status-good-border)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "0.85rem" }}>
              <div style={{ padding: "6px", backgroundColor: "var(--color-sage)", color: "#FFFFFF", borderRadius: "6px" }}>
                <Sparkles size={20} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--color-sage-hover)" }}>
                    Pedagogical Study Roadmap: {resourceData.topic}
                  </h3>
                  <Badge variant="neutral">Domain: {resourceData.domain}</Badge>
                </div>
                <p style={{ fontSize: "0.88rem", color: "var(--text-main)", marginTop: "4px", lineHeight: 1.5 }}>
                  {resourceData.ai_guidance}
                </p>
                <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
                  <Button
                    size="sm"
                    variant="primary"
                    icon={PlayCircle}
                    onClick={() => startTopicStudy(resourceData.topic)}
                  >
                    Start Focused Study Session
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Categorized Resource Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
            {resourceData.resources.map((res, i) => {
              const Icon = getCategoryIcon(res.category);

              return (
                <Card
                  key={i}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    borderTop: "3px solid var(--color-sage)",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.6rem" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <Icon size={16} color="var(--color-sage)" />
                        <span style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", color: "var(--color-sage)" }}>
                          {res.category}
                        </span>
                      </div>
                      <Badge variant="neutral">{res.source}</Badge>
                    </div>

                    <h4 style={{ fontSize: "0.98rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.4rem" }}>
                      {res.title}
                    </h4>

                    <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", lineHeight: 1.45 }}>
                      {res.description}
                    </p>
                  </div>

                  <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      Verified External Platform
                    </span>
                    <a
                      href={res.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        color: "var(--color-sage)",
                        fontSize: "0.85rem",
                        fontWeight: 700,
                        textDecoration: "none",
                      }}
                    >
                      <span>Open Link</span>
                      <ExternalLink size={13} />
                    </a>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
