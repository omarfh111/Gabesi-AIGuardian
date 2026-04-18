import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import L from 'leaflet';
import 'leaflet.markercluster';

// Fix Leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const ISSUE_COLORS: Record<string, string> = {
  smoke: '#ef4444', smell: '#a855f7', dust: '#eab308',
  water: '#3b82f6', waste: '#16a34a', symptoms: '#f97316',
};

function createIcon(type: string) {
  const color = ISSUE_COLORS[type] || '#6b7280';
  return L.divIcon({
    className: '',
    html: `<div style="width:24px;height:24px;background:${color};border:3px solid #fff;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>`,
    iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -14],
  });
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Report {
  id: string;
  rounded_lat: number;
  rounded_lng: number;
  issue_type: string;
  severity: string;
  description?: string;
  created_at: string;
}

function MapClick({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({ click(e) { onMapClick(e.latlng.lat, e.latlng.lng); } });
  return null;
}

function DetailPopup({ report }: { report: Report }) {
  const [details, setDetails] = useState<any>(null);
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

  const riskColor = (level: string) => {
    if (level === 'high') return { bg: '#fee2e2', color: '#b91c1c' };
    if (level === 'medium') return { bg: '#fef3c7', color: '#92400e' };
    return { bg: '#dcfce7', color: '#166534' };
  };

  return (
    <div style={{ fontFamily: 'Inter,sans-serif', minWidth: 250, maxWidth: 300 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <strong style={{ textTransform: 'capitalize', fontSize: 15 }}>{report.issue_type.replace('_', ' ')}</strong>
        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: report.severity === 'high' ? '#fee2e2' : report.severity === 'medium' ? '#fef3c7' : '#dcfce7', color: report.severity === 'high' ? '#b91c1c' : report.severity === 'medium' ? '#92400e' : '#166534' }}>{report.severity}</span>
      </div>
      <div style={{ color: '#999', fontSize: 11, marginBottom: 6 }}>📅 {new Date(report.created_at).toLocaleString()}</div>
      {report.description && <p style={{ fontSize: 13, color: '#444', borderLeft: '3px solid #e0f2fe', paddingLeft: 8, margin: '6px 0' }}>{report.description}</p>}

      <div style={{ borderTop: '1px solid #f0f0f0', marginTop: 8, paddingTop: 8 }}>
        {loading ? (
          <div style={{ fontSize: 12, color: '#aaa', textAlign: 'center', padding: 8 }}>⏳ Loading AI insights...</div>
        ) : details ? (
          <div>
            {details.ai_summary && (
              <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                <span style={{ fontSize: 14 }}>🧠</span>
                <p style={{ fontSize: 12, color: '#555', margin: 0, lineHeight: 1.5 }}>{details.ai_summary}</p>
              </div>
            )}
            <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#777', flexWrap: 'wrap' }}>
              {details.similar_count > 0 && (
                <span>👥 {details.similar_count} similar</span>
              )}
              {details.confidence_score > 0 && (
                <span>📊 {Math.round(details.confidence_score * 100)}% confidence</span>
              )}
              {details.risk_level && (
                <span style={{ padding: '1px 8px', borderRadius: 8, fontSize: 10, fontWeight: 600, textTransform: 'uppercase', ...riskColor(details.risk_level) }}>
                  {details.risk_level} risk
                </span>
              )}
            </div>
          </div>
        ) : (
          <div style={{ fontSize: 12, color: '#ccc' }}>No AI data available</div>
        )}
      </div>
    </div>
  );
}

function ClusterLayer({ reports, onSelectReport }: { reports: Report[]; onSelectReport: (r: Report) => void }) {
  const map = useMap();
  const clusterRef = useRef<any>(null);

  useEffect(() => {
    if (!map) return;
    if (clusterRef.current) { map.removeLayer(clusterRef.current); }

    const cluster = (L as any).markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 60,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: true,
      zoomToBoundsOnClick: true,
      iconCreateFunction: (c: any) => {
        const count = c.getChildCount();
        const children = c.getAllChildMarkers();
        // Find dominant issue type
        const typeCounts: Record<string, number> = {};
        children.forEach((m: any) => { const t = m.options._issueType || 'waste'; typeCounts[t] = (typeCounts[t] || 0) + 1; });
        const dominant = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'waste';
        const color = ISSUE_COLORS[dominant] || '#6b7280';
        const size = count < 10 ? 50 : count < 30 ? 65 : 80;
        const pulse = count < 10 ? 70 : count < 30 ? 90 : 110;
        return L.divIcon({
          className: '',
          html: `<div style="position:relative;width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center">
            <div style="position:absolute;inset:0;border-radius:50%;background:${color};opacity:0.15;animation:pulse 2s ease-in-out infinite;width:${pulse}px;height:${pulse}px;margin:${-(pulse-size)/2}px"></div>
            <div style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle,${color}44 0%,${color}11 60%,transparent 70%)"></div>
            <div style="position:relative;z-index:2;width:${size*0.6}px;height:${size*0.6}px;border-radius:50%;background:${color};border:3px solid rgba(255,255,255,.9);box-shadow:0 2px 12px ${color}66;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:${count<10?13:12}px;font-family:Inter,sans-serif">${count}</div>
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
      } as any);
      marker.on('click', () => onSelectReport(r));
      cluster.addLayer(marker);
    });

    map.addLayer(cluster);
    clusterRef.current = cluster;
    return () => { if (clusterRef.current) map.removeLayer(clusterRef.current); };
  }, [map, reports, onSelectReport]);

  return null;
}

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [clickPos, setClickPos] = useState<{ lat: number; lng: number } | null>(null);
  const [form, setForm] = useState({ issue_type: 'waste', severity: 'medium', description: '', symptoms: '' });
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

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

  const handleMapClick = (lat: number, lng: number) => {
    if (!modalOpen) { setClickPos({ lat, lng }); setModalOpen(true); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
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
  const typeLabels: Record<string,string> = { smoke:'🔥 Smoke', smell:'👃 Smell', dust:'🌫️ Dust', water:'💧 Water', waste:'🗑️ Waste', symptoms:'🩺 Symptoms' };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', fontFamily: "'Inter',system-ui,sans-serif" }}>
      {/* MAP */}
      <MapContainer center={[33.8815, 10.0982]} zoom={12} scrollWheelZoom style={{ height: '100%', width: '100%' }}>
        <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapClick onMapClick={handleMapClick} />
        <ClusterLayer reports={reports} onSelectReport={setSelectedReport} />
      </MapContainer>

      {/* HEADER */}
      <div style={{ position:'absolute', top:16, left:16, zIndex:1000, background:'rgba(255,255,255,.92)', backdropFilter:'blur(12px)', borderRadius:16, padding:'14px 20px', boxShadow:'0 4px 20px rgba(0,0,0,.08)', maxWidth:340, border:'1px solid rgba(255,255,255,.3)' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ background:'linear-gradient(135deg,#38bdf8,#34d399)', borderRadius:10, padding:8, color:'#fff', fontSize:20 }}>🌍</div>
          <div>
            <div style={{ fontWeight:700, fontSize:16, color:'#111' }}>Gabès Environment</div>
            <div style={{ fontSize:10, color:'#888', fontWeight:600, letterSpacing:2, textTransform:'uppercase' }}>Intelligence Platform</div>
          </div>
        </div>
        <div style={{ fontSize:12, color:'#777', marginTop:6 }}>Community-driven monitoring · Anonymous · AI-powered</div>
      </div>

      {/* INSTRUCTION */}
      {!modalOpen && (
        <div style={{ position:'absolute', top:16, left:'50%', transform:'translateX(-50%)', zIndex:1000, background:'rgba(255,255,255,.9)', backdropFilter:'blur(8px)', padding:'10px 24px', borderRadius:30, boxShadow:'0 2px 12px rgba(0,0,0,.08)', pointerEvents:'none', fontSize:14, color:'#555', fontWeight:500 }}>
          🌍 Click anywhere on the map to report an issue
        </div>
      )}

      {/* FILTERS */}
      <div style={{ position:'absolute', bottom:24, left:16, zIndex:1000 }}>
        <div style={{ background:'rgba(255,255,255,.95)', backdropFilter:'blur(12px)', borderRadius:16, padding:16, boxShadow:'0 4px 20px rgba(0,0,0,.1)', minWidth:240 }}>
          <div style={{ fontSize:11, fontWeight:700, color:'#888', textTransform:'uppercase', letterSpacing:1, marginBottom:8 }}>Filter by type</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:4 }}>
            <button onClick={() => setFilterType('')} style={{ fontSize:12, padding:'4px 12px', borderRadius:16, border: filterType==='' ? '2px solid #0ea5e9' : '1px solid #ddd', background: filterType==='' ? '#e0f2fe' : '#f9fafb', cursor:'pointer', fontWeight:500 }}>All</button>
            {types.map(t => (
              <button key={t} onClick={() => setFilterType(t)} style={{ fontSize:12, padding:'4px 12px', borderRadius:16, border: filterType===t ? '2px solid #0ea5e9' : '1px solid #ddd', background: filterType===t ? '#e0f2fe' : '#f9fafb', cursor:'pointer', fontWeight:500 }}>
                {typeLabels[t]}
              </button>
            ))}
          </div>
          <div style={{ fontSize:11, fontWeight:700, color:'#888', textTransform:'uppercase', letterSpacing:1, marginTop:12, marginBottom:6 }}>Severity</div>
          <div style={{ display:'flex', gap:4 }}>
            {['','low','medium','high'].map(s => (
              <button key={s} onClick={() => setFilterSeverity(s)} style={{ fontSize:12, padding:'4px 14px', borderRadius:16, border: filterSeverity===s ? '2px solid #0ea5e9' : '1px solid #ddd', background: filterSeverity===s ? '#e0f2fe' : '#f9fafb', cursor:'pointer', fontWeight:500, flex:1 }}>
                {s || 'All'}
              </button>
            ))}
          </div>
          <div style={{ marginTop:8, fontSize:11, color:'#aaa' }}>{reports.length} reports loaded</div>
        </div>
      </div>

      {/* MODAL */}
      {modalOpen && clickPos && (
        <div style={{ position:'fixed', inset:0, zIndex:2000, display:'flex', alignItems:'center', justifyContent:'center', background:'rgba(0,0,0,.4)', backdropFilter:'blur(4px)' }}>
          <div style={{ background:'#fff', borderRadius:20, boxShadow:'0 8px 40px rgba(0,0,0,.15)', width:'100%', maxWidth:420, overflow:'hidden' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'18px 24px', borderBottom:'1px solid #f0f0f0', background:'#fafafa' }}>
              <h2 style={{ margin:0, fontSize:18, fontWeight:600 }}>Report Environmental Issue</h2>
              <button onClick={() => setModalOpen(false)} style={{ background:'none', border:'none', fontSize:22, cursor:'pointer', color:'#999' }}>×</button>
            </div>
            <form onSubmit={handleSubmit} style={{ padding:24, display:'flex', flexDirection:'column', gap:16 }}>
              <div>
                <label style={{ fontSize:13, fontWeight:500, color:'#555', display:'block', marginBottom:4 }}>Issue Type</label>
                <select value={form.issue_type} onChange={e => setForm({...form, issue_type: e.target.value})} style={{ width:'100%', padding:10, borderRadius:10, border:'1px solid #ddd', fontSize:14 }}>
                  <option value="smoke">🔥 Smoke / Air Pollution</option>
                  <option value="smell">👃 Chemical Smell</option>
                  <option value="dust">🌫️ Chemical Dust</option>
                  <option value="water">💧 Water Contamination</option>
                  <option value="waste">🗑️ Industrial Waste</option>
                  <option value="symptoms">🩺 Health Symptoms</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize:13, fontWeight:500, color:'#555', display:'block', marginBottom:4 }}>Severity</label>
                <div style={{ display:'flex', gap:12 }}>
                  {['low','medium','high'].map(s => (
                    <label key={s} style={{ display:'flex', alignItems:'center', gap:4, fontSize:14, cursor:'pointer' }}>
                      <input type="radio" name="severity" value={s} checked={form.severity===s} onChange={e => setForm({...form, severity:e.target.value})} />
                      <span style={{ textTransform:'capitalize' }}>{s}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label style={{ fontSize:13, fontWeight:500, color:'#555', display:'block', marginBottom:4 }}>Description (optional)</label>
                <textarea rows={3} value={form.description} onChange={e => setForm({...form, description:e.target.value})} placeholder="What are you experiencing?" style={{ width:'100%', padding:10, borderRadius:10, border:'1px solid #ddd', fontSize:14, resize:'vertical', boxSizing:'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize:13, fontWeight:500, color:'#555', display:'block', marginBottom:4 }}>Symptoms (comma separated, optional)</label>
                <input type="text" value={form.symptoms} onChange={e => setForm({...form, symptoms:e.target.value})} placeholder="e.g. coughing, headache" style={{ width:'100%', padding:10, borderRadius:10, border:'1px solid #ddd', fontSize:14, boxSizing:'border-box' }} />
              </div>
              <button type="submit" disabled={loading} style={{ padding:'12px 0', borderRadius:12, border:'none', background:'#0ea5e9', color:'#fff', fontSize:15, fontWeight:600, cursor: loading?'wait':'pointer', opacity: loading?.7:1, boxShadow:'0 2px 12px rgba(14,165,233,.3)' }}>
                {loading ? 'Submitting...' : 'Submit Anonymous Report'}
              </button>
              <p style={{ textAlign:'center', fontSize:11, color:'#bbb', margin:0 }}>Your location is slightly randomized to protect privacy.</p>
            </form>
          </div>
        </div>
      )}

      {/* SELECTED REPORT DETAIL PANEL */}
      {selectedReport && !modalOpen && (
        <div style={{ position:'absolute', top:16, right:16, zIndex:1000, width:320, background:'rgba(255,255,255,.95)', backdropFilter:'blur(12px)', borderRadius:16, boxShadow:'0 4px 24px rgba(0,0,0,.12)', border:'1px solid rgba(0,0,0,.05)', overflow:'hidden' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 16px', borderBottom:'1px solid #f0f0f0' }}>
            <strong style={{ textTransform:'capitalize', fontSize:15 }}>{selectedReport.issue_type.replace('_',' ')}</strong>
            <button onClick={() => setSelectedReport(null)} style={{ background:'none', border:'none', fontSize:18, cursor:'pointer', color:'#999' }}>×</button>
          </div>
          <div style={{ padding:16 }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
              <span style={{ fontSize:11, padding:'2px 8px', borderRadius:12, background: selectedReport.severity==='high'?'#fee2e2':selectedReport.severity==='medium'?'#fef3c7':'#dcfce7', color: selectedReport.severity==='high'?'#b91c1c':selectedReport.severity==='medium'?'#92400e':'#166534', fontWeight:600 }}>{selectedReport.severity}</span>
              <span style={{ fontSize:11, color:'#999' }}>📅 {new Date(selectedReport.created_at).toLocaleString()}</span>
            </div>
            {selectedReport.description && <p style={{ fontSize:13, color:'#444', borderLeft:'3px solid #e0f2fe', paddingLeft:8, margin:'8px 0' }}>{selectedReport.description}</p>}
            <DetailPopup report={selectedReport} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
