import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import "./Energy.css";

// ─── Palette ────────────────────────────────────────────────
const C = {
  gold:    "#f59e0b",
  green:   "#10b981",
  blue:    "#3b82f6",
  purple:  "#8b5cf6",
  red:     "#ef4444",
  slate:   "#64748b",
  muted:   "rgba(255,255,255,0.5)",
  gridStroke: "rgba(255,255,255,0.06)",
  bg:      "transparent",
};

const SOLUTION_COLORS = {
  "Panneaux PV":            C.gold,
  "Chauffe-eau Thermique":  C.green,
  "Isolation Thermique":    C.blue,
  "Micro-éolienne":         C.purple,
};

// ─── Tooltip personnalisé ────────────────────────────────────
function CustomTooltip({ active, payload, label, unit = "TND" }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="dash-tooltip">
      <div className="dash-tooltip__label">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="dash-tooltip__row">
          <span style={{ color: p.color }}>■</span>
          <span>{p.name}</span>
          <strong>{Number(p.value).toLocaleString("fr-TN")} {unit}</strong>
        </div>
      ))}
    </div>
  );
}

// ─── KPI Cards ──────────────────────────────────────────────
function KpiCard({ icon, label, value, sub, color = C.gold }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card__icon" style={{ color }}>{icon}</div>
      <div className="kpi-card__body">
        <div className="kpi-card__value" style={{ color }}>{value}</div>
        <div className="kpi-card__label">{label}</div>
        {sub && <div className="kpi-card__sub">{sub}</div>}
      </div>
    </div>
  );
}

// ─── Section title ───────────────────────────────────────────
function SectionTitle({ icon, title, sub }) {
  return (
    <div className="dash-section-title">
      <span className="dash-section-title__icon">{icon}</span>
      <div>
        <div className="dash-section-title__text">{title}</div>
        {sub && <div className="dash-section-title__sub">{sub}</div>}
      </div>
    </div>
  );
}

// ─── XAI Decision Tree ──────────────────────────────────────
function DecisionTree({ nodes = [] }) {
  return (
    <div className="xai-tree">
      {nodes.map((n, i) => (
        <div key={i} className={`xai-tree__node ${n.passed ? "xai-tree__node--pass" : "xai-tree__node--fail"}`}>
          <span className="xai-tree__icon">{n.passed ? "✓" : "✗"}</span>
          <span className="xai-tree__cond">{n.condition}</span>
          <span className="xai-tree__res">→ {n.result}</span>
        </div>
      ))}
    </div>
  );
}

// ─── XAI Feature Bar ────────────────────────────────────────
function FeatureBar({ feature, importance_pct, valeur, color = C.gold }) {
  return (
    <div className="xai-feature">
      <div className="xai-feature__top">
        <span className="xai-feature__name">{feature}</span>
        <div className="xai-feature__right">
          <span className="xai-feature__val">{valeur}</span>
          <span className="xai-feature__pct">{importance_pct}%</span>
        </div>
      </div>
      <div className="xai-feature__track">
        <div
          className="xai-feature__fill"
          style={{ width: `${importance_pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ─── XAI Agent Section ──────────────────────────────────────
function XaiAgentCard({ title, icon, confidence, facteurs = [], decision_tree = [], color, extra }) {
  return (
    <div className="xai-agent-card" style={{ borderColor: `${color}30` }}>
      <div className="xai-agent-card__header" style={{ borderBottomColor: `${color}20` }}>
        <span>{icon}</span>
        <div>
          <div className="xai-agent-card__title">{title}</div>
          <div className="xai-agent-card__conf">
            Confiance du modèle :
            <span style={{ color, marginLeft: 6, fontWeight: 700 }}>{confidence}%</span>
            <div className="conf-bar">
              <div className="conf-bar__fill" style={{ width: `${confidence}%`, background: color }} />
            </div>
          </div>
        </div>
      </div>

      {facteurs.length > 0 && (
        <div className="xai-agent-card__factors">
          <div className="xai-sub-label">Facteurs de décision</div>
          {facteurs.map((f, i) => (
            <div key={i} className="xai-factor">
              <div className="xai-factor__top">
                <span className="xai-factor__name">{f.facteur}</span>
                <span className="xai-factor__val" style={{ color: f.impact === "positif" ? C.green : f.impact === "négatif" ? C.red : C.muted }}>
                  {f.valeur} ({f.impact})
                </span>
                <span className="xai-factor__w">{f.poids_pct}%</span>
              </div>
              <div className="xai-factor__track">
                <div className="xai-factor__fill" style={{
                  width: `${f.poids_pct}%`,
                  background: f.impact === "positif" ? C.green : f.impact === "négatif" ? C.red : C.slate,
                }} />
              </div>
              <div className="xai-factor__expl">{f.explication}</div>
            </div>
          ))}
        </div>
      )}

      {decision_tree.length > 0 && (
        <div className="xai-agent-card__tree">
          <div className="xai-sub-label">Arbre de décision</div>
          <DecisionTree nodes={decision_tree} />
        </div>
      )}

      {extra && <div className="xai-agent-card__extra">{extra}</div>}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  MAIN DASHBOARD COMPONENT
// ══════════════════════════════════════════════════════════════
export default function Dashboard({ data }) {
  if (!data) return null;
  const {
    kpis, financial_projections, co2_projections,
    energy_mix, solution_comparison, xai,
  } = data;

  // Prepare radar data for solution comparison
  const radarData = solution_comparison.map(s => ({
    solution: s.solution.replace("Chauffe-eau ", ""),
    Score:    s.score * 20,
    ROI:      Math.max(0, Math.min(100, 100 - s.payback_ans * 5)),
    Budget:   s.dans_budget ? 80 : 30,
    CO2:      Math.min(100, s.co2_evite_an / 15),
  }));

  // Subset of projection rows (every 5 years for cleaner chart)
  const proj5 = financial_projections.filter(r => r.annee % 5 === 0 || r.annee === 1);
  const co25  = co2_projections.filter(r => r.annee % 5 === 0 || r.annee === 1);

  return (
    <div className="dashboard energy-unified-dashboard">

      {/* ─── KPIs ──────────────────────────────────────── */}
      <SectionTitle icon="📊" title="Tableau de bord synthèse" sub="Métriques clés calculées par l'orchestrateur" />
      <div className="kpi-grid">
        <KpiCard icon="💰" label="Investissement total (net subv.)"
          value={`${Number(kpis.investissement_total_tnd).toLocaleString("fr-TN")} TND`}
          sub={`Budget disponible suffisant : ${kpis.dans_budget ? "✓ Oui" : "✗ Partiellement"}`}
          color={C.gold} />
        <KpiCard icon="📉" label="Économie mensuelle estimée"
          value={`${kpis.economie_mensuelle_tnd} TND/mois`}
          sub={`−${kpis.reduction_facture_pct}% de la facture STEG`}
          color={C.green} />
        <KpiCard icon="⏱️" label="Retour sur investissement"
          value={`${kpis.payback_annees} ans`}
          sub="Combo PV + Thermique"
          color={C.blue} />
        <KpiCard icon="📈" label="Gain net sur 25 ans"
          value={`${Number(kpis.gain_net_25_ans_tnd).toLocaleString("fr-TN")} TND`}
          sub="Après remboursement investissement"
          color={C.gold} />
        <KpiCard icon="🌿" label="CO₂ évité / an"
          value={`${Number(kpis.co2_evite_annuel_kg).toLocaleString("fr-TN")} kg`}
          sub={`≈ ${kpis.arbres_equivalent_25ans} arbres sur 25 ans`}
          color={C.green} />
        <KpiCard icon="☀️" label="Ensoleillement annuel"
          value={`${kpis.heures_soleil_an} h/an`}
          sub={`${kpis.kwp_installe} kWp à installer`}
          color={C.gold} />
      </div>

      {/* ─── Courbe gains financiers ────────────────────── */}
      <SectionTitle icon="📈" title="Projections financières sur 25 ans"
        sub="Gains cumulés comparés à la dépense sans renouvelable (avec inflation STEG +5%/an)" />
      <div className="dash-chart-card">
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={financial_projections}
            margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
            <defs>
              <linearGradient id="gradCombo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={C.green} stopOpacity={0.3} />
                <stop offset="95%" stopColor={C.green} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradPV" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={C.gold} stopOpacity={0.25} />
                <stop offset="95%" stopColor={C.gold} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradSans" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={C.red} stopOpacity={0.2} />
                <stop offset="95%" stopColor={C.red} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={C.gridStroke} />
            <XAxis dataKey="annee" stroke={C.muted} tick={{ fontSize: 11 }} tickFormatter={v => `An ${v}`} />
            <YAxis stroke={C.muted} tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<CustomTooltip unit="TND" />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
            <Area type="monotone" dataKey="gain_combo_cumul" name="✦ Combo PV+Thermique" stroke={C.green} fill="url(#gradCombo)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="gain_pv_cumul" name="☀ PV seul" stroke={C.gold} fill="url(#gradPV)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="facture_sans_renouv" name="✗ Sans renouvelable" stroke={C.red} fill="url(#gradSans)" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
        <p className="dash-chart-note">
          💡 La courbe verte dépasse 0 à l'année {kpis.payback_annees} (point de rentabilité). La courbe rouge montre ce que vous dépenseriez sans transition.
        </p>
      </div>

      {/* ─── Économies annuelles par source ─────────────── */}
      <SectionTitle icon="💵" title="Économies annuelles par solution"
        sub="Montant économisé chaque année (en TND) avec inflation STEG incluse" />
      <div className="dash-chart-card">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={proj5} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.gridStroke} />
            <XAxis dataKey="annee" stroke={C.muted} tick={{ fontSize: 11 }} tickFormatter={v => `An ${v}`} />
            <YAxis stroke={C.muted} tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip unit="TND" />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
            <Bar dataKey="economie_annuelle_pv" name="☀ Panneaux PV" fill={C.gold} radius={[4, 4, 0, 0]} />
            <Bar dataKey="economie_annuelle_therm" name="🌡 Thermique" fill={C.green} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ─── CO2 & Mix énergétique ──────────────────────── */}
      <div className="dash-row-2col">
        <div>
          <SectionTitle icon="🌿" title="Réduction CO₂ sur 25 ans" sub="kg de CO₂ évités cumulativement" />
          <div className="dash-chart-card">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={co25} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.gridStroke} />
                <XAxis dataKey="annee" stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={v => `An ${v}`} />
                <YAxis stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(1)}t`} />
                <Tooltip content={<CustomTooltip unit="kg CO₂" />} />
                <Area type="monotone" dataKey="co2_evite_pv_kg" name="PV" stackId="1" stroke={C.gold} fill={C.gold} fillOpacity={0.3} dot={false} />
                <Area type="monotone" dataKey="co2_evite_therm_kg" name="Thermique" stackId="1" stroke={C.green} fill={C.green} fillOpacity={0.3} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div>
          <SectionTitle icon="⚡" title="Mix énergétique" sub="Actuel → Cible après transition" />
          <div className="dash-chart-card">
            <div className="dash-pie-row">
              <div>
                <div className="dash-pie-label">Actuel</div>
                <PieChart width={150} height={150}>
                  <Pie data={energy_mix.actuel} cx={65} cy={65} outerRadius={60} dataKey="value" startAngle={90} endAngle={-270}>
                    {energy_mix.actuel.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${v}%`} />
                </PieChart>
                <div className="dash-pie-legend">
                  {energy_mix.actuel.map((e, i) => (
                    <div key={i} style={{ display: "flex", gap: 6, fontSize: "0.7rem", alignItems: "center" }}>
                      <span style={{ width: 10, height: 10, borderRadius: 2, background: e.color, display: "inline-block" }} />
                      {e.name} {e.value}%
                    </div>
                  ))}
                </div>
              </div>
              <div className="dash-pie-arrow">→</div>
              <div>
                <div className="dash-pie-label">Cible</div>
                <PieChart width={150} height={150}>
                  <Pie data={energy_mix.cible} cx={65} cy={65} outerRadius={60} dataKey="value" startAngle={90} endAngle={-270}>
                    {energy_mix.cible.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${v}%`} />
                </PieChart>
                <div className="dash-pie-legend">
                  {energy_mix.cible.map((e, i) => (
                    <div key={i} style={{ display: "flex", gap: 6, fontSize: "0.7rem", alignItems: "center" }}>
                      <span style={{ width: 10, height: 10, borderRadius: 2, background: e.color, display: "inline-block" }} />
                      {e.name} {e.value}%
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <p className="dash-chart-note" style={{ marginTop: 8 }}>
              🎯 Objectif : {energy_mix.taux_renouv_cible_pct}% d'énergie renouvelable
            </p>
          </div>
        </div>
      </div>

      {/* ─── Comparaison solutions ──────────────────────── */}
      <SectionTitle icon="🎯" title="Comparaison des solutions"
        sub="Coût net, économie mensuelle et score par technologie" />
      <div className="dash-chart-card">
        <div className="dash-row-2col" style={{ gap: 24 }}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={solution_comparison} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.gridStroke} />
              <XAxis type="number" stroke={C.muted} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="solution" stroke={C.muted} tick={{ fontSize: 11 }} width={80} />
              <Tooltip content={<CustomTooltip unit="TND" />} />
              <Bar dataKey="cout_net_tnd" name="Coût net TND" radius={[0, 4, 4, 0]}>
                {solution_comparison.map((s, i) => <Cell key={i} fill={s.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <ResponsiveContainer width="100%" height={260}>
            <RadarChart outerRadius={90} data={radarData}>
              <PolarGrid stroke={C.gridStroke} />
              <PolarAngleAxis dataKey="solution" tick={{ fontSize: 10, fill: C.muted }} />
              <PolarRadiusAxis tick={{ fontSize: 9, fill: C.muted }} domain={[0, 100]} />
              <Radar name="Score" dataKey="Score" stroke={C.gold} fill={C.gold} fillOpacity={0.2} />
              <Radar name="ROI" dataKey="ROI" stroke={C.green} fill={C.green} fillOpacity={0.15} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ─── Solutions scoring cards ─────────────────────── */}
      <div className="solution-grid">
        {solution_comparison.map((s, i) => (
          <div key={i} className="solution-score-card" style={{ borderTopColor: s.color }}>
            <div className="solution-score-card__stars">
              {"★".repeat(s.score)}{"☆".repeat(5 - s.score)}
            </div>
            <div className="solution-score-card__name">{s.solution}</div>
            <div className="solution-score-card__rows">
              <div className="ssr">
                <span>Coût net</span>
                <strong style={{ color: s.color }}>{s.cout_net_tnd.toLocaleString("fr-TN")} TND</strong>
              </div>
              <div className="ssr">
                <span>Économie/mois</span>
                <strong style={{ color: C.green }}>{s.economie_mois} TND</strong>
              </div>
              <div className="ssr">
                <span>Payback</span>
                <strong>{s.payback_ans} ans</strong>
              </div>
              <div className="ssr">
                <span>CO₂ évité/an</span>
                <strong style={{ color: C.green }}>{s.co2_evite_an} kg</strong>
              </div>
              <div className="ssr">
                <span>Dans le budget</span>
                <strong style={{ color: s.dans_budget ? C.green : C.red }}>
                  {s.dans_budget ? "✓ Oui" : "✗ Non"}
                </strong>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════
          XAI — EXPLAINABLE AI SECTION
      ══════════════════════════════════════════════════════ */}
      <div className="xai-section">
        <div className="xai-header">
          <div className="xai-header__badge">XAI</div>
          <div>
            <div className="xai-header__title">Intelligence Artificielle Explicable</div>
            <div className="xai-header__sub">
              Comment chaque agent a pris ses décisions · Facteurs · Poids · Arbres de décision · Limites du modèle
            </div>
          </div>
        </div>

        {/* Importance globale des features */}
        <div className="xai-feature-section">
          <SectionTitle icon="🔍" title="Importance globale des variables"
            sub="Quels facteurs ont le plus influencé l'ensemble des recommandations ?" />
          <div className="dash-chart-card">
            <div className="xai-features-list">
              {xai.feature_importance_globale.map((f, i) => (
                <FeatureBar key={i} {...f}
                  color={i === 0 ? C.gold : i === 1 ? C.green : i === 2 ? C.blue : i === 3 ? C.purple : C.slate} />
              ))}
            </div>
          </div>
        </div>

        {/* Agent par agent */}
        <div className="xai-agents-grid">
          {/* Agent ENV */}
          <XaiAgentCard
            title="Agent Environnement — Potentiel solaire"
            icon="🌱"
            confidence={xai.agent_env_xai.confidence_pct}
            facteurs={xai.agent_env_xai.facteurs}
            decision_tree={xai.agent_env_xai.decision_tree}
            color={C.green}
            extra={
              <div className="xai-score-pill" style={{ background: `${C.green}20`, borderColor: `${C.green}40` }}>
                Score : {xai.agent_env_xai.score_final} / {xai.agent_env_xai.score_max}
              </div>
            }
          />

          {/* Agent Finance */}
          <XaiAgentCard
            title="Agent Finance — Capacité d'investissement"
            icon="💰"
            confidence={xai.agent_finance_xai.confidence_pct}
            facteurs={xai.agent_finance_xai.facteurs}
            decision_tree={xai.agent_finance_xai.decision_tree}
            color={C.gold}
            extra={
              <div className="xai-score-pill" style={{ background: `${C.gold}20`, borderColor: `${C.gold}40` }}>
                Score : {xai.agent_finance_xai.score_final} / {xai.agent_finance_xai.score_max}
              </div>
            }
          />
        </div>

        {/* Agent Énergie — Sources évaluées */}
        <div className="xai-energie-section">
          <SectionTitle icon="⚡" title="Agent Énergie — Sélection des sources"
            sub={`Algorithme : ${xai.agent_energie_xai.algorithme_selection}`} />
          <div className="dash-chart-card">
            <div className="xai-sources-grid">
              {xai.agent_energie_xai.sources_evaluees.map((s, i) => (
                <div key={i} className={`xai-source-card ${s.retenu ? "xai-source-card--ok" : "xai-source-card--no"}`}>
                  <div className="xai-source-card__top">
                    <span className="xai-source-card__badge" style={{
                      background: s.retenu ? `${C.green}20` : "rgba(100,116,139,0.2)",
                      color: s.retenu ? C.green : C.slate,
                    }}>
                      {s.retenu ? "✓ RETENU" : "✗ ÉCARTÉ"}
                    </span>
                    <strong>{s.source}</strong>
                  </div>
                  <div className="xai-source-score-track">
                    <div className="xai-source-score-fill" style={{
                      width: `${s.score}%`,
                      background: s.retenu ? C.green : C.slate,
                    }} />
                    <span>{s.score}/100</span>
                  </div>
                  <div className="xai-source-card__raison">{s.raison_principale}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Expert XAI — Biais & Limites */}
        <div className="xai-expert-section">
          <SectionTitle icon="🧠" title="Agent Expert — Transparence & Limites du modèle"
            sub={`Confiance globale : ${xai.agent_expert_xai.confidence_pct}%`} />
          <div className="dash-chart-card xai-expert-card">
            <div className="xai-expert-cols">
              <div>
                <div className="xai-sub-label xai-sub-label--green">✓ Points forts</div>
                <ul className="xai-list xai-list--green">
                  {xai.agent_expert_xai.points_forts.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
              <div>
                <div className="xai-sub-label xai-sub-label--amber">⚠ Biais identifiés</div>
                <ul className="xai-list xai-list--amber">
                  {xai.agent_expert_xai.biais_identifies.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </div>
              <div>
                <div className="xai-sub-label xai-sub-label--red">✗ Limites du modèle</div>
                <ul className="xai-list xai-list--red">
                  {xai.agent_expert_xai.limites_modele.map((l, i) => <li key={i}>{l}</li>)}
                </ul>
              </div>
            </div>
            <div className="xai-methodology">
              <strong>Méthodologie :</strong> {xai.methodology.description}
              <br /><strong>Modèle :</strong> {xai.methodology.model}
              <br /><strong>Sources :</strong> {xai.methodology.source_donnees.join(" · ")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
