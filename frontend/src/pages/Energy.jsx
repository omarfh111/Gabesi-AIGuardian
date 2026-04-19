import { useState, useEffect } from "react";
import EnergyProfileForm from "./EnergyProfileForm";
import EnergyDashboard from "./EnergyDashboard";
import "./Energy.css";

// API helpers scoped to the integrated route
const API_BASE = "/api/v1/energy";

async function fetchUserData() {
  const res = await fetch(`${API_BASE}/user-data`);
  if (!res.ok) throw new Error("Failed to fetch user data");
  return res.json();
}

async function runParallelAnalysis(userData = null) {
  const res = await fetch(`${API_BASE}/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: userData ? JSON.stringify(userData) : "{}",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("API unreachable");
  return res.json();
}

function Energy() {
  const [page, setPage] = useState("home"); // Changed to "home" by default for integration
  const [userData, setUserData] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking"); // "ok" | "error" | "checking"
  const [langsmithStatus, setLangsmithStatus] = useState("off");

  // Health check on mount
  useEffect(() => {
    async function init() {
      try {
        const health = await healthCheck();
        setApiStatus("ok");
        setLangsmithStatus(health.langsmith_tracing === "true" ? "on" : "off");

        const data = await fetchUserData();
        setUserData(data);
      } catch {
        setApiStatus("error");
      }
    }
    init();
  }, []);

  const handleAnalyse = async (overriddenData = null) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await runParallelAnalysis(overriddenData || userData);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const initials = userData
    ? `${(userData.identite?.prenom || "S")[0]}${(userData.identite?.nom || "B")[0]}`
    : "??";

  // Handler pour la soumission du formulaire
  const handleFormSubmit = (data) => {
    setUserData(data);
    setPage("home");
    handleAnalyse(data);
  };

  /**
   * Format agent analysis text by converting markdown-like patterns to JSX.
   */
  function formatAnalysis(text) {
    if (!text) return <span style={{ color: "var(--energy-text-muted)" }}>Aucune analyse disponible.</span>;

    return text.split("\n").map((line, i) => {
      if (line.startsWith("###")) {
        return (
          <h4 key={i} style={{ color: "var(--energy-text-primary)", margin: "16px 0 8px", fontSize: "0.95rem", fontWeight: 700 }}>
            {line.replace(/^###\s*/, "")}
          </h4>
        );
      }
      if (line.startsWith("##")) {
        return (
          <h3 key={i} style={{ color: "var(--energy-text-primary)", margin: "18px 0 8px", fontSize: "1rem", fontWeight: 700 }}>
            {line.replace(/^##\s*/, "")}
          </h3>
        );
      }
      if (line.startsWith("- ") || line.startsWith("• ")) {
        return (
          <div key={i} style={{ paddingLeft: "16px", position: "relative", marginBottom: "4px" }}>
            <span style={{ position: "absolute", left: 0, color: "var(--energy-accent-emerald)" }}>•</span>
            {renderBold(line.slice(2))}
          </div>
        );
      }
      const numMatch = line.match(/^(\d+)\.\s/);
      if (numMatch) {
        return (
          <div key={i} style={{ paddingLeft: "20px", position: "relative", marginBottom: "4px" }}>
            <span style={{ position: "absolute", left: 0, color: "var(--energy-accent-cyan)", fontWeight: 700, fontSize: "0.85rem" }}>
              {numMatch[1]}.
            </span>
            {renderBold(line.replace(/^\d+\.\s/, ""))}
          </div>
        );
      }
      if (line.trim() === "") return <br key={i} />;
      return <p key={i} style={{ marginBottom: "6px" }}>{renderBold(line)}</p>;
    });
  }

  function renderBold(text) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  }

  // Page router — must be after all hooks
  if (page === "form") {
    return (
      <div className="energy-page">
        <EnergyProfileForm onBack={() => setPage("home")} onSubmit={handleFormSubmit} />
      </div>
    );
  }

  return (
    <div className="energy-page">
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="header__badge">
            <span className="pulse-dot"></span>
            Énergie Renouvelable — Gabès
          </div>
          <h1 className="header__title">Conseiller IA Énergie</h1>
          <p className="header__subtitle">
            4 agents IA analysent votre profil énergétique et financier pour un plan de transition personnalisé.
          </p>
        </header>

        {/* Status Bar */}
        <div className="status-bar">
          <div className="status-item">
            <span className={`status-dot ${apiStatus === "ok" ? "status-dot--ok" : apiStatus === "error" ? "status-dot--err" : "status-dot--warn"}`}></span>
            API FastAPI {apiStatus === "ok" ? "connectée" : apiStatus === "error" ? "hors-ligne" : "vérification..."}
          </div>
          <div className="status-item">
            <span className={`status-dot ${langsmithStatus === "on" ? "status-dot--ok" : "status-dot--warn"}`}></span>
            LangSmith {langsmithStatus === "on" ? "actif" : "inactif"}
          </div>
          <div className="status-item">
            <span className="status-dot status-dot--ok"></span>
            GPT-4o-mini
          </div>
        </div>

        {/* User Profile Card */}
        {userData && (
          <div className="profile-card">
            <div className="profile-card__header">
              <div className="profile-card__avatar">{initials}</div>
              <div>
                <div className="profile-card__name">
                  {userData.identite?.prenom} {userData.identite?.nom}
                </div>
                <div className="profile-card__location">
                  📍 {userData.logement?.emplacement} — {userData.logement?.environement}
                </div>
              </div>
            </div>
            <div className="profile-grid">
              <div className="profile-stat">
                <div className="profile-stat__label">Salaire mensuel</div>
                <div className="profile-stat__value profile-stat__value--green">
                  {userData.identite?.["salaire_tnd_accumulé"] || userData.identite?.salaire_tnd_accumule} TND
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat__label">Facture STEG</div>
                <div className="profile-stat__value profile-stat__value--amber">
                  {userData.consommation?.avg_facture_steg_tnd} TND/mois
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat__label">Consommation</div>
                <div className="profile-stat__value profile-stat__value--blue">
                  {userData.consommation?.consommation_kwh_mensuelle} kWh/mois
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat__label">Type logement</div>
                <div className="profile-stat__value">
                  {userData.logement?.type_maison}
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat__label">Surface</div>
                <div className="profile-stat__value">
                  {userData.logement?.surface_m2} m²
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat__label">CO₂ estimé</div>
                <div className="profile-stat__value profile-stat__value--amber">
                  {userData.consommation?.taux_co2_kg_par_an} kg/an
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <span className="error-banner__icon">⚠️</span>
            <span>{error}</span>
            <button className="error-banner__dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Action Button */}
        <div className="action-section">
          <button
            className="btn-analyse"
            onClick={() => handleAnalyse()}
            disabled={loading || apiStatus !== "ok"}
            id="btn-run-analysis"
          >
            {!loading && <span className="btn-analyse__shimmer"></span>}
            {loading ? (
              <>
                <span className="spinner"></span>
                Analyse en cours…
              </>
            ) : (
              <>🚀 Lancer l'analyse</>
            )}
          </button>
          <button
            className="btn-create-profile"
            onClick={() => setPage("form")}
            id="btn-create-profile"
          >
            ✏️ Créer / mettre à jour le profil
          </button>
          <span className="btn-hint">
            4 agents IA : ENV → Énergie + Finance → Expert Synthèse
          </span>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-orbs">
              <div className="loading-orb"></div>
              <div className="loading-orb"></div>
              <div className="loading-orb"></div>
            </div>
            <div className="loading-text">4 agents en cours d'exécution…</div>
            <div className="loading-sub">
              🌱 ENV → ⚡ Énergie (séq.) &amp; 💰 Finance (///) → 🧠 Expert Synthèse
            </div>
          </div>
        )}

        {/* Results */}
        {results && (
          <>
            {/* Timing strip */}
            <div className="timing-strip">
              <div className="timing-item">
                <div className="timing-item__label">Temps total</div>
                <div className="timing-item__value">{results.total_time_seconds}s</div>
              </div>
              <div className="timing-item">
                <div className="timing-item__label">🌱 Env</div>
                <div className="timing-item__value timing-item__value--blue">
                  {results.env_result.execution_time_seconds}s
                </div>
              </div>
              <div className="timing-item">
                <div className="timing-item__label">⚡ Énergie</div>
                <div className="timing-item__value" style={{ color: "#a78bfa" }}>
                  {results.energie_result.execution_time_seconds}s
                </div>
              </div>
              <div className="timing-item">
                <div className="timing-item__label">💰 Finance</div>
                <div className="timing-item__value timing-item__value--amber">
                  {results.finance_result.execution_time_seconds}s
                </div>
              </div>
              <div className="timing-item">
                <div className="timing-item__label">🧠 Expert</div>
                <div className="timing-item__value" style={{ color: "#f59e0b" }}>
                  {results.expert_result.execution_time_seconds}s
                </div>
              </div>
            </div>

            {/* Top row: Env + Finance */}
            <div className="results-grid">
              <div className="agent-card agent-card--env">
                <div className="agent-card__header">
                  <div className="agent-card__title-group">
                    <div className="agent-card__icon">🌱</div>
                    <div>
                      <div className="agent-card__title">Agent Environnement</div>
                      <div className="agent-card__subtitle">Analyse écologique &amp; solaire</div>
                    </div>
                  </div>
                  <span className="agent-card__badge agent-card__badge--success">✓ Terminé</span>
                </div>
                <div className="agent-card__body">
                  <div className="agent-card__analysis">{formatAnalysis(results.env_result.analysis)}</div>
                </div>
                <div className="agent-card__footer">
                  <span>{results.env_result.raw_messages_count} messages LangGraph</span>
                  <span>Tracé sur LangSmith</span>
                </div>
              </div>

              <div className="agent-card agent-card--fin">
                <div className="agent-card__header">
                  <div className="agent-card__title-group">
                    <div className="agent-card__icon">💰</div>
                    <div>
                      <div className="agent-card__title">Agent Finance</div>
                      <div className="agent-card__subtitle">Plan d'investissement énergie</div>
                    </div>
                  </div>
                  <span className="agent-card__badge agent-card__badge--success">✓ Terminé</span>
                </div>
                <div className="agent-card__body">
                  <div className="agent-card__analysis">{formatAnalysis(results.finance_result.analysis)}</div>
                </div>
                <div className="agent-card__footer">
                  <span>{results.finance_result.raw_messages_count} messages LangGraph</span>
                  <span>Tracé sur LangSmith</span>
                </div>
              </div>
            </div>

            {/* Energie Agent — full width, purple */}
            <div className="agent-card agent-card--energie">
              <div className="agent-card__header">
                <div className="agent-card__title-group">
                  <div className="agent-card__icon">⚡</div>
                  <div>
                    <div className="agent-card__title">Agent Énergies Renouvelables</div>
                    <div className="agent-card__subtitle">
                      Recommandations personnalisées basées sur l'analyse environnementale
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "0.7rem", color: "#a78bfa", background: "rgba(139,92,246,0.12)", padding: "2px 8px", borderRadius: "20px", fontWeight: 700 }}>
                    SÉQUENTIEL (ENV →)
                  </span>
                  <span className="agent-card__badge agent-card__badge--success">✓ Terminé</span>
                </div>
              </div>
              <div className="agent-card__body">
                <div className="agent-card__analysis">{formatAnalysis(results.energie_result.analysis)}</div>
              </div>
              <div className="agent-card__footer">
                <span>{results.energie_result.raw_messages_count} messages LangGraph</span>
                <span style={{ color: "#a78bfa" }}>⚡ Alimenté par Agent Env</span>
              </div>
            </div>

            {/* Expert Agent — full width, gold */}
            <div className="agent-card agent-card--expert">
              <div className="agent-card__header">
                <div className="agent-card__title-group">
                  <div className="agent-card__icon">🧠</div>
                  <div>
                    <div className="agent-card__title">Agent Expert — Synthèse Finale</div>
                    <div className="agent-card__subtitle">
                      Coûts réels · Gains 5/10/25 ans · Plan d'installation · Subventions
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "0.7rem", color: "#f59e0b", background: "rgba(245,158,11,0.12)", padding: "2px 8px", borderRadius: "20px", fontWeight: 700 }}>
                    SYNTHÈSE FINALE
                  </span>
                  <span className="agent-card__badge agent-card__badge--success">✓ Terminé</span>
                </div>
              </div>
              <div className="agent-card__body">
                <div className="agent-card__analysis">{formatAnalysis(results.expert_result.analysis)}</div>
              </div>
              <div className="agent-card__footer">
                <span>{results.expert_result.raw_messages_count} messages LangGraph</span>
                <span style={{ color: "#f59e0b" }}>🧠 Alimenté par Énergie + Finance</span>
              </div>
            </div>

            {/* Dashboard — statistiques + graphiques + XAI */}
            {results.dashboard && (
              <EnergyDashboard data={results.dashboard} />
            )}
          </>
        )}

        {/* Footer */}
        <footer className="footer">
          Powered by <a href="https://python.langchain.com/docs/langgraph" target="_blank" rel="noreferrer">LangGraph</a>
          {" "}+ <a href="https://fastapi.tiangolo.com" target="_blank" rel="noreferrer">FastAPI</a>
          {" "}+ <a href="https://react.dev" target="_blank" rel="noreferrer">React</a>
          {" "}• Tracked by <a href="https://smith.langchain.com" target="_blank" rel="noreferrer">LangSmith</a>
        </footer>
      </div>
    </div>
  );
}

export default Energy;
