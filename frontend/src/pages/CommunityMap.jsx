import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import L from 'leaflet';
import 'leaflet.markercluster';
import { API_BASE_URL } from '../config';

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const ISSUE_COLORS = {
  smoke: '#ef4444', smell: '#a855f7', dust: '#eab308',
  water: '#3b82f6', waste: '#16a34a', symptoms: '#f97316',
};

function createIcon(type) {
  const color = ISSUE_COLORS[type] || '#6b7280';
  return L.divIcon({
    className: '',
    html: `<div class="w-6 h-6 rounded-full border-2 border-white shadow-md flex items-center justify-center" style="background:${color}"></div>`,
    iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -14],
  });
}

// API points to the unified backend (FastAPI)
const API = `${API_BASE_URL}/api/v1/community`;

function MapClick({ onMapClick }) {
  useMapEvents({ click(e) { onMapClick(e.latlng.lat, e.latlng.lng); } });
  return null;
}

function DetailPopup({ report }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${API}/reports/${report.id}`)
      .then(r => r.json())
      .then(d => { if (!cancelled) setDetails(d); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [report.id]);

  const riskClasses = (level) => {
    if (level === 'high') return 'bg-red-100 text-red-700';
    if (level === 'medium') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <div className="font-sans min-w-[250px] max-w-[300px]">
      <div className="flex items-center justify-between mb-2">
        <strong className="capitalize text-sm font-semibold">{report.issue_type.replace('_', ' ')}</strong>
        <span className={`text-xs px-2 py-0.5 rounded-full ${report.severity === 'high' ? 'bg-red-100 text-red-700' : report.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
          {report.severity}
        </span>
      </div>
      <div className="text-gray-500 text-xs mb-2">📅 {new Date(report.created_at).toLocaleString()}</div>
      {report.description && <p className="text-sm text-gray-700 border-l-2 border-blue-200 pl-2 my-2">{report.description}</p>}

      <div className="border-t border-gray-100 mt-2 pt-2">
        {loading ? (
          <div className="text-xs text-gray-400 text-center p-2">⏳ Loading AI insights...</div>
        ) : details ? (
          <div>
            {details.ai_summary && (
              <div className="flex gap-2 mb-2">
                <span className="text-sm">🧠</span>
                <p className="text-xs text-gray-600 m-0 leading-relaxed">{details.ai_summary}</p>
              </div>
            )}
            <div className="flex gap-2 text-xs text-gray-500 flex-wrap">
              {details.similar_count > 0 && <span>👥 {details.similar_count} similar</span>}
              {details.confidence_score > 0 && <span>📊 {Math.round(details.confidence_score * 100)}% confidence</span>}
              {details.risk_level && (
                <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${riskClasses(details.risk_level)}`}>
                  {details.risk_level} risk
                </span>
              )}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-300">No AI data available</div>
        )}
      </div>
    </div>
  );
}

function ClusterLayer({ reports, onSelectReport }) {
  const map = useMap();
  const clusterRef = useRef(null);

  useEffect(() => {
    if (!map) return;
    if (clusterRef.current) { map.removeLayer(clusterRef.current); }

    const cluster = L.markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 60,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      iconCreateFunction: (c) => {
        const count = c.getChildCount();
        const children = c.getAllChildMarkers();
        const typeCounts = {};
        children.forEach((m) => { const t = m.options._issueType || 'waste'; typeCounts[t] = (typeCounts[t] || 0) + 1; });
        const dominant = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'waste';
        const color = ISSUE_COLORS[dominant] || '#6b7280';
        const size = count < 10 ? 40 : count < 30 ? 55 : 70;
        
        return L.divIcon({
          className: '',
          html: `<div class="relative flex items-center justify-center rounded-full shadow-lg border-2 border-white/90 text-white font-bold" style="width:${size}px;height:${size}px;background:${color}">
            <div class="absolute inset-0 rounded-full animate-ping opacity-20" style="background:${color}"></div>
            <span class="relative z-10 ${count < 10 ? 'text-xs' : 'text-sm'}">${count}</span>
          </div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        });
      },
    });

    reports.forEach(r => {
      const marker = L.marker([r.rounded_lat, r.rounded_lng], {
        icon: createIcon(r.issue_type),
        _issueType: r.issue_type,
      });
      marker.on('click', () => onSelectReport(r));
      cluster.addLayer(marker);
    });

    map.addLayer(cluster);
    clusterRef.current = cluster;
    return () => { if (clusterRef.current) map.removeLayer(clusterRef.current); };
  }, [map, reports, onSelectReport]);

  return null;
}

export default function CommunityMap() {
  const [reports, setReports] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [clickPos, setClickPos] = useState(null);
  const [form, setForm] = useState({ issue_type: 'waste', severity: 'medium', description: '', symptoms: '' });
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  const loadReports = async () => {
    try {
      const params = new URLSearchParams();
      if (filterType) params.set('issue_type', filterType);
      if (filterSeverity) params.set('severity', filterSeverity);
      const res = await fetch(`${API}/reports?${params}`);
      if (res.ok) setReports(await res.json());
    } catch (e) { console.error('fetch error', e); }
  };

  useEffect(() => { loadReports(); const i = setInterval(loadReports, 30000); return () => clearInterval(i); }, [filterType, filterSeverity]);

  const handleMapClick = (lat, lng) => {
    if (!modalOpen) { setClickPos({ lat, lng }); setModalOpen(true); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!clickPos) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: clickPos.lat, lng: clickPos.lng,
          issue_type: form.issue_type, severity: form.severity,
          description: form.description || null,
          symptom_tags: form.symptoms ? form.symptoms.split(',').map(s => s.trim()) : [],
        }),
      });
      if (res.ok) { setModalOpen(false); loadReports(); setForm({ issue_type: 'waste', severity: 'medium', description: '', symptoms: '' }); }
      else alert('Submit failed');
    } catch { alert('Network error — is the backend running?'); }
    finally { setLoading(false); }
  };

  const types = ['smoke', 'smell', 'dust', 'water', 'waste', 'symptoms'];
  const typeLabels = { smoke:'🔥 Smoke', smell:'👃 Smell', dust:'🌫️ Dust', water:'💧 Water', waste:'🗑️ Waste', symptoms:'🩺 Symptoms' };

  return (
    <div className="w-full h-screen relative bg-slate-50 font-sans">
      {/* MAP */}
      <MapContainer center={[33.8815, 10.0982]} zoom={12} scrollWheelZoom className="h-full w-full z-0">
        <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapClick onMapClick={handleMapClick} />
        <ClusterLayer reports={reports} onSelectReport={setSelectedReport} />
      </MapContainer>

      {/* HEADER OVERLAY */}
      <div className="absolute top-20 left-4 z-10 bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-lg max-w-[320px] border border-white/40">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-xl p-2 text-white text-xl shadow-inner">🌍</div>
          <div>
            <div className="font-bold text-gray-900 text-lg leading-tight">Gabès Environment</div>
            <div className="text-[10px] text-gray-500 font-bold tracking-widest uppercase">Community Intelligence</div>
          </div>
        </div>
        <div className="text-xs text-gray-500 mt-2">Community-driven monitoring · Anonymous · AI-powered</div>
      </div>

      {/* INSTRUCTION */}
      {!modalOpen && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-10 bg-white/90 backdrop-blur-md px-6 py-2 rounded-full shadow-md pointer-events-none text-sm text-gray-600 font-medium border border-gray-100">
          🌍 Click anywhere on the map to report an issue
        </div>
      )}

      {/* FILTERS OVERLAY */}
      <div className="absolute bottom-6 left-4 z-10">
        <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-4 shadow-xl border border-white/50 min-w-[260px]">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Filter by type</div>
          <div className="flex flex-wrap gap-1.5">
            <button onClick={() => setFilterType('')} className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${filterType==='' ? 'border-2 border-cyan-500 bg-cyan-50 text-cyan-800' : 'border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100'}`}>All</button>
            {types.map(t => (
              <button key={t} onClick={() => setFilterType(t)} className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${filterType===t ? 'border-2 border-cyan-500 bg-cyan-50 text-cyan-800' : 'border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100'}`}>
                {typeLabels[t]}
              </button>
            ))}
          </div>
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-4 mb-2">Severity</div>
          <div className="flex gap-2">
            {['','low','medium','high'].map(s => (
              <button key={s} onClick={() => setFilterSeverity(s)} className={`flex-1 text-xs px-3 py-1.5 rounded-full font-medium transition-colors capitalize ${filterSeverity===s ? 'border-2 border-cyan-500 bg-cyan-50 text-cyan-800' : 'border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100'}`}>
                {s || 'All'}
              </button>
            ))}
          </div>
          <div className="mt-3 text-[10px] text-gray-400 font-medium">{reports.length} reports loaded</div>
        </div>
      </div>

      {/* SUBMISSION MODAL */}
      {modalOpen && clickPos && (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-gray-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50">
              <h2 className="text-lg font-bold text-gray-800 m-0">Report Issue</h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
              <div>
                <label className="text-sm font-semibold text-gray-600 block mb-1">Issue Type</label>
                <select value={form.issue_type} onChange={e => setForm({...form, issue_type: e.target.value})} className="w-full p-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition-all">
                  <option value="smoke">🔥 Smoke / Air Pollution</option>
                  <option value="smell">👃 Chemical Smell</option>
                  <option value="dust">🌫️ Chemical Dust</option>
                  <option value="water">💧 Water Contamination</option>
                  <option value="waste">🗑️ Industrial Waste</option>
                  <option value="symptoms">🩺 Health Symptoms</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600 block mb-2">Severity</label>
                <div className="flex gap-4">
                  {['low','medium','high'].map(s => (
                    <label key={s} className="flex items-center gap-2 text-sm cursor-pointer group">
                      <input type="radio" name="severity" value={s} checked={form.severity===s} onChange={e => setForm({...form, severity:e.target.value})} className="w-4 h-4 text-cyan-600 focus:ring-cyan-500 border-gray-300" />
                      <span className="capitalize text-gray-700 group-hover:text-gray-900">{s}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600 block mb-1">Description (optional)</label>
                <textarea rows="3" value={form.description} onChange={e => setForm({...form, description:e.target.value})} placeholder="What are you experiencing?" className="w-full p-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-cyan-500 outline-none resize-none" />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600 block mb-1">Symptoms (comma separated)</label>
                <input type="text" value={form.symptoms} onChange={e => setForm({...form, symptoms:e.target.value})} placeholder="e.g. coughing, headache" className="w-full p-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-cyan-500 outline-none" />
              </div>
              <button type="submit" disabled={loading} className={`mt-2 py-3 rounded-xl font-bold text-white shadow-lg transition-all ${loading ? 'bg-cyan-400 cursor-wait' : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 hover:shadow-cyan-500/25'}`}>
                {loading ? 'Submitting...' : 'Submit Anonymous Report'}
              </button>
              <p className="text-center text-[10px] text-gray-400 m-0">Your location is slightly randomized to protect privacy.</p>
            </form>
          </div>
        </div>
      )}

      {/* SELECTED REPORT DETAIL PANEL */}
      {selectedReport && !modalOpen && (
        <div className="absolute top-20 right-4 z-10 w-[320px] bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-in slide-in-from-right-8 duration-300">
          <div className="flex justify-between items-center p-3 border-b border-gray-100 bg-gray-50/80">
            <strong className="capitalize text-sm font-bold text-gray-800">{selectedReport.issue_type.replace('_',' ')}</strong>
            <button onClick={() => setSelectedReport(null)} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
          </div>
          <div className="p-4">
            <DetailPopup report={selectedReport} />
          </div>
        </div>
      )}
    </div>
  );
}
