import React, { useState } from 'react';
import Sparkline from './Sparkline';

const RISK_COLORS = { danger: '#ef4444', warning: '#f59e0b', safe: '#10b981' };
const CAT_COLORS = { industrial: '#ef4444', agriculture: '#10b981', coastal: '#06b6d4', urban: '#f59e0b' };
const TABS = [
  { key: 'pollution', icon: '🔴', label: 'Pollution' },
  { key: 'locations', icon: '📍', label: 'Locations' },
  { key: 'analysis', icon: '🧠', label: 'AI Analysis' },
  { key: 'logs', icon: '📄', label: 'Logs' },
];

const EmergencySidebar = ({
  overview, circles, locations, logs,
  onSearch, onDeleteLocation, onFlyTo, onFlyToCircle,
}) => {
  const [activeTab, setActiveTab] = useState('pollution');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchFeedback, setSearchFeedback] = useState({ text: '', type: '' });
  const [selectedFacility, setSelectedFacility] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // ── Search ──────────────────────────────────
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchFeedback({ text: 'Searching via SerpAPI + classifying with AI...', type: 'loading' });
    try {
      const res = await fetch('/search-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await res.json();
      if (data.valid) {
        setSearchFeedback({ text: `✓ ${data.name} → ${data.category} / ${data.zone} (${data.elapsed}s)`, type: 'success' });
        setSearchQuery('');
        onFlyTo(data.lat, data.lng);
        onSearch(); // triggers reload
      } else {
        setSearchFeedback({ text: data.error || 'Failed to add location.', type: 'error' });
      }
    } catch (err) {
      setSearchFeedback({ text: 'Network error: ' + err.message, type: 'error' });
    } finally {
      setSearchLoading(false);
    }
  };

  // ── AI Analysis ──────────────────────────────
  const handleAnalyze = async () => {
    if (!selectedFacility) { alert('Please select a facility to analyze.'); return; }
    setAnalysisLoading(true);
    try {
      const res = await fetch('/analyze-zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ facility: selectedFacility, zoneType: 'industrial' }),
      });
      const data = await res.json();
      setAnalysis(data);
    } catch { /* ignore */ }
    finally { setAnalysisLoading(false); }
  };

  // ── Render tabs ──────────────────────────────
  const renderPollution = () => {
    const sorted = [...circles].sort((a, b) => b.riskScore - a.riskScore);
    if (!sorted.length) return <Empty icon="📊" text="Loading pollution data..." />;
    return sorted.map((c, i) => (
      <div
        key={c.key}
        onClick={() => onFlyToCircle(c.lat, c.lng)}
        className="relative cursor-pointer rounded-xl p-3.5 mb-2 transition-all hover:translate-x-0.5 overflow-hidden"
        style={{ background: '#111630', border: '1px solid #1e2548', animationDelay: `${i * 0.05}s` }}
      >
        {/* Left accent bar */}
        <div className="absolute left-0 top-0 bottom-0 w-[3px]"
          style={{ background: RISK_COLORS[c.riskLevel] }} />
        <div className="flex items-center justify-between mb-2">
          <span className="text-[13px] font-bold text-white">{c.label}</span>
          <span className="text-[9px] px-2 py-0.5 rounded-full font-bold uppercase"
            style={{ background: `${RISK_COLORS[c.riskLevel]}20`, color: RISK_COLORS[c.riskLevel] }}>
            {c.riskLabel} {c.riskScore}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-1.5 mb-2">
          {[
            { val: c.meanDailyCO2, label: 't/day', color: '#06b6d4' },
            { val: c.maxCO2, label: 'Max (m)', color: RISK_COLORS[c.riskLevel] },
            { val: c.exceedanceCount, label: 'Exceed', color: '#eef0f8' },
          ].map(({ val, label, color }) => (
            <div key={label} className="text-center p-1 rounded" style={{ background: 'rgba(255,255,255,.03)' }}>
              <div className="text-sm font-bold" style={{ color }}>{val}</div>
              <div className="text-[8px] uppercase text-gray-500">{label}</div>
            </div>
          ))}
        </div>
        {c.monthlyData && <Sparkline data={c.monthlyData} color={c.color || RISK_COLORS[c.riskLevel]} height={28} />}
        <div className="h-1 rounded-full mt-2" style={{ background: 'rgba(255,255,255,.06)' }}>
          <div className="h-full rounded-full transition-all duration-1000"
            style={{ width: `${Math.min(100, c.riskScore)}%`, background: RISK_COLORS[c.riskLevel] }} />
        </div>
      </div>
    ));
  };

  const renderLocations = () => {
    if (!locations.length) return <Empty icon="📍" text="No locations yet. Search for a place to get started." />;
    return locations.map((loc, i) => {
      const color = CAT_COLORS[loc.category] || '#8b95b8';
      return (
        <div
          key={loc.id}
          onClick={() => onFlyTo(loc.lat, loc.lng)}
          className="relative cursor-pointer rounded-xl p-3 mb-1.5 transition-all hover:translate-x-0.5 hover:border-blue-500"
          style={{ background: '#111630', border: '1px solid #1e2548', animationDelay: `${i * 0.03}s` }}
        >
          <button
            onClick={e => { e.stopPropagation(); onDeleteLocation(loc.id); }}
            className="absolute top-1.5 right-1.5 text-gray-600 hover:text-red-500 text-xs w-5 h-5 flex items-center justify-center rounded"
            style={{ opacity: 0 }}
            onMouseEnter={e => e.currentTarget.style.opacity = 1}
            onMouseLeave={e => e.currentTarget.style.opacity = 0}
          >✕</button>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[13px] font-semibold text-white pr-6">{loc.name}</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold capitalize"
              style={{ background: `${color}18`, color }}>
              {loc.category}
            </span>
          </div>
          <div className="flex gap-3 text-[11px] text-gray-400">
            <span>📌 {loc.zone || 'unknown'}</span>
            <span className="font-mono text-[10px] text-gray-500">{loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}</span>
          </div>
        </div>
      );
    });
  };

  const renderAnalysis = () => {
    const a = analysis;
    const diag = a?.analysis?.diagnostic || {};
    const metrics = a?.analysis?.metrics || {};
    const recs = a?.recommendations?.recommendations || [];
    const carbon = a?.recommendations?.carbonMarket || {};
    const regulatory = a?.recommendations?.regulatoryAlert || {};

    return (
      <div className="rounded-xl p-4 mb-2" style={{ background: '#111630', border: '1px solid #1e2548' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xl"
            style={{ background: 'linear-gradient(135deg,#8b5cf6,#3b82f6)' }}>🧠</div>
          <div>
            <div className="text-sm font-bold text-white">AI Environmental Analysis</div>
            <div className="text-[11px] text-gray-400">Powered by GPT-4o-mini — Analyzes real data only</div>
          </div>
        </div>

        <select
          value={selectedFacility}
          onChange={e => setSelectedFacility(e.target.value)}
          className="w-full bg-[#0c1020] border border-[#1e2548] rounded-xl px-3 py-2.5 text-[13px] text-white mb-3 outline-none focus:border-cyan-500 appearance-none cursor-pointer"
        >
          <option value="">Select a facility to analyze...</option>
          {circles.map(c => (
            <option key={c.key} value={c.key}>{c.label} (Risk: {c.riskScore})</option>
          ))}
        </select>

        <button
          onClick={handleAnalyze}
          disabled={analysisLoading}
          className="w-full py-3 rounded-xl text-[13px] font-bold text-white transition-all hover:-translate-y-px disabled:opacity-60"
          style={{ background: 'linear-gradient(135deg,#8b5cf6,#3b82f6)' }}
        >
          {analysisLoading ? '⏳ Analyzing with AI...' : '🧠 Analyze with AI Agent'}
        </button>

        {a && (
          <div className="mt-4 space-y-3">
            {[
              { title: '📊 Diagnostic', content: diag.summary },
              { title: '📈 Tendance', content: diag.trend && `${diag.trend} — ${diag.trendDetail || ''}` },
              { title: '🌤 Pattern saisonnier', content: diag.seasonalPattern },
              { title: '⚠️ Conformité', content: diag.complianceDetail, highlight: diag.complianceStatus },
            ].map(({ title, content, highlight }) => content ? (
              <div key={title}>
                <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 mb-1">{title}</div>
                <div className="text-[12px] text-gray-300 leading-relaxed">
                  {highlight && <strong className="mr-1" style={{ color: highlight === 'critique' ? '#ef4444' : highlight === 'attention' ? '#f59e0b' : '#10b981' }}>{highlight} —</strong>}
                  {content}
                </div>
              </div>
            ) : null)}

            {metrics.peakMonth && (
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 mb-2">📊 Métriques clés</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,.03)' }}>
                    <div className="text-[10px] text-gray-500">Pic</div>
                    <div className="text-[13px] font-bold text-red-400">{metrics.peakValue} t</div>
                    <div className="text-[9px] text-gray-500">{metrics.peakMonth}</div>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,.03)' }}>
                    <div className="text-[10px] text-gray-500">Min</div>
                    <div className="text-[13px] font-bold text-green-400">{metrics.lowestValue} t</div>
                    <div className="text-[9px] text-gray-500">{metrics.lowestMonth}</div>
                  </div>
                </div>
              </div>
            )}

            {recs.length > 0 && (
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 mb-2">💡 Recommandations</div>
                {recs.map((r, i) => (
                  <div key={i} className="rounded-xl p-3 mb-2 transition-all hover:border-purple-500/50"
                    style={{ background: 'rgba(255,255,255,.03)', border: '1px solid #1e2548' }}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase"
                        style={{
                          background: r.priority === 'critique' ? 'rgba(239,68,68,.15)' : r.priority === 'important' ? 'rgba(245,158,11,.15)' : 'rgba(16,185,129,.15)',
                          color: r.priority === 'critique' ? '#ef4444' : r.priority === 'important' ? '#f59e0b' : '#10b981',
                        }}>
                        {r.priority}
                      </span>
                      <span className="text-[12px] font-semibold text-white">{r.title}</span>
                    </div>
                    <div className="text-[11px] text-gray-400 leading-relaxed">{r.description}</div>
                    <div className="flex gap-2 mt-1">
                      {[r.timeline, r.category].filter(Boolean).map(tag => (
                        <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(139,92,246,.1)', color: '#8b5cf6' }}>{tag}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {carbon.eligible !== undefined && (
              <div className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,.03)', border: '1px solid #1e2548' }}>
                <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                  <span>🏭 Marché Carbone</span>
                  <span style={{ color: carbon.eligible ? '#10b981' : '#ef4444', fontSize: 10 }}>
                    {carbon.eligible ? '✓ Éligible' : '✗ Non éligible'}
                  </span>
                </div>
                <div className="text-[11px] text-gray-400">{carbon.detail}</div>
              </div>
            )}

            {regulatory.hasAlert && (
              <div className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,.03)', border: '1px solid rgba(239,68,68,.3)' }}>
                <div className="text-[11px] font-bold text-red-400 mb-1">⚠️ Alerte Réglementaire</div>
                <div className="text-[11px] text-gray-400">{regulatory.detail}</div>
              </div>
            )}

            <div className="text-center text-[10px] text-gray-500">
              Analysis completed in {a.elapsed || '?'}s via GPT-4o-mini
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderLogs = () => {
    if (!logs.length) return <Empty icon="📄" text="No logs yet." />;
    return logs.map((log, i) => {
      const icon = log.status === 'success' ? '✓' : log.status === 'rejected' ? '↺' : '✗';
      const iconBg = log.status === 'success' ? 'rgba(16,185,129,.12)' : log.status === 'rejected' ? 'rgba(245,158,11,.12)' : 'rgba(239,68,68,.12)';
      const time = new Date(log.timestamp).toLocaleTimeString();
      return (
        <div key={i} className="flex items-center gap-2 p-2 rounded-lg mb-1 text-[11px]"
          style={{ background: '#111630', border: '1px solid #1e2548' }}>
          <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0" style={{ background: iconBg }}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-white font-medium truncate">{log.query}</div>
            <div className="text-gray-500 text-[10px] truncate">{log.detail || ''}</div>
          </div>
          <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
            {log.cacheHit && <span className="text-[9px] px-1 py-0.5 rounded" style={{ background: 'rgba(139,92,246,.12)', color: '#8b5cf6' }}>CACHE</span>}
            {log.elapsed && <span className="text-[9px] px-1 py-0.5 rounded" style={{ background: 'rgba(59,130,246,.12)', color: '#60a5fa' }}>{log.elapsed}s</span>}
            <span className="text-[10px] text-gray-500">{time}</span>
          </div>
        </div>
      );
    });
  };

  return (
    <aside className="flex flex-col h-full border-r border-[#1e2548] overflow-hidden" style={{ background: '#0c1020' }}>
      {/* Search */}
      <div className="p-3 border-b border-[#1e2548]">
        <div className="flex gap-2">
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search location in Gabès..."
            className="flex-1 bg-[#111630] border border-[#1e2548] rounded-xl px-3 py-2.5 text-[13px] text-white outline-none focus:border-cyan-500 transition-colors"
          />
          <button
            onClick={handleSearch}
            disabled={searchLoading}
            className="px-4 py-2 rounded-xl text-[13px] font-semibold text-white transition-all hover:-translate-y-px disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg,#3b82f6,#06b6d4)' }}
          >
            {searchLoading ? '...' : 'Search'}
          </button>
        </div>
        {searchFeedback.text && (
          <div className={`text-[12px] mt-1.5 ${searchFeedback.type === 'success' ? 'text-green-400' : searchFeedback.type === 'error' ? 'text-red-400' : 'text-cyan-400'}`}>
            {searchFeedback.text}
          </div>
        )}
      </div>

      {/* Overview bar */}
      {overview && (
        <div className="grid grid-cols-3 gap-2 p-3 border-b border-[#1e2548]">
          {[
            { id: 'avgDaily', val: overview.avgDailyCO2, label: 'Avg CO₂ t/day', color: '#06b6d4' },
            { id: 'total', val: overview.gctSynthesis?.totalCO2_6months > 1000 ? Math.round(overview.gctSynthesis.totalCO2_6months / 1000) + 'k' : overview.gctSynthesis?.totalCO2_6months, label: 'Total (6 months)', color: '#8b5cf6' },
            { id: 'exceed', val: overview.gctSynthesis?.exceedanceRate, label: 'Exceedance', color: parseInt(overview.gctSynthesis?.exceedanceRate) > 25 ? '#ef4444' : '#f59e0b' },
          ].map(({ id, val, label, color }) => (
            <div key={id} className="relative text-center py-2.5 px-1.5 rounded-xl overflow-hidden"
              style={{ background: '#111630', border: '1px solid #1e2548' }}>
              <div className="absolute top-0 inset-x-0 h-0.5"
                style={{ background: id === 'avgDaily' ? 'linear-gradient(90deg,#06b6d4,#3b82f6)' : id === 'total' ? 'linear-gradient(90deg,#8b5cf6,#3b82f6)' : 'linear-gradient(90deg,#ef4444,#f59e0b)' }} />
              <div className="text-[22px] font-black" style={{ color }}>{val ?? '--'}</div>
              <div className="text-[8px] uppercase tracking-wider text-gray-500 font-bold mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[#1e2548]">
        {TABS.map(({ key, icon, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex-1 py-2.5 text-[10px] font-bold uppercase tracking-wider transition-colors border-b-2 ${activeTab === key ? 'text-cyan-400 border-cyan-400' : 'text-gray-500 border-transparent hover:text-gray-300'}`}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {/* Panel content */}
      <div className="flex-1 overflow-y-auto p-2.5" style={{ scrollbarWidth: 'thin', scrollbarColor: '#1e2548 transparent' }}>
        {activeTab === 'pollution' && renderPollution()}
        {activeTab === 'locations' && renderLocations()}
        {activeTab === 'analysis' && renderAnalysis()}
        {activeTab === 'logs' && renderLogs()}
      </div>
    </aside>
  );
};

const Empty = ({ icon, text }) => (
  <div className="text-center py-8 text-gray-500">
    <div className="text-4xl mb-3">{icon}</div>
    <div className="text-[13px] leading-relaxed">{text}</div>
  </div>
);

export default EmergencySidebar;
