import React, { useState, useEffect } from 'react';
import { Wind, Anchor, Droplets, Map, AlertTriangle } from 'lucide-react';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [activeFiles, setActiveFiles] = useState({ industry: [], fishing: [] });

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:3000/api/analysis');
      const json = await res.json();
      setData(json);
      
      const filesRes = await fetch('http://localhost:3000/api/files');
      if (filesRes.ok) {
          const filesJson = await filesRes.json();
          setActiveFiles(filesJson);
      }
    } catch(e) {
      console.error(e);
      // Fallback si pas de serveur allumé
      setData({
        global_risk: 0.82,
        confidence: 0.76,
        zone: "gabes",
        modules: {
          pollution: { level: "élevé", source: "GCT" },
          marine: { spread: "élevé", wind_effect: "vers la côte", wind_speed: 25 },
          fishing: { trend: "en baisse", insight: "Diminution de 30% récemment" },
          tourism: { status: "faible", avg_stay_days: 1.4 }
        },
        recommendations: [
          { text: "Réduire les rejets près des côtes à cause du vent", priority: "high" },
        ]
      });
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    setUploadStatus(`Téléversement et Ré-analyse de ${files.length} fichier(s)...`);
    
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('file', files[i]);
    }
    
    try {
      const res = await fetch('http://localhost:3000/api/upload', {
        method: 'POST',
        body: formData,
      });
      const result = await res.json();
      setUploadStatus(result.message || 'Succès !');
      setTimeout(() => {
        setUploadStatus('');
        fetchAnalysis(); // Refresh after injection
      }, 2000);
    } catch(err) {
      setUploadStatus('Erreur de téléversement');
    }
    setUploading(false);
  };

  const handleDeleteFile = async (type, filename) => {
    if (!window.confirm(`Voulez-vous vraiment supprimer définitivement le fichier ${filename} ? L'IA va oublier toutes ses données associées.`)) return;
    try {
        setUploadStatus(`Suppression vectorielle et locale de ${filename}...`);
        const res = await fetch(`http://localhost:3000/api/files/${type}/${filename}`, { method: 'DELETE' });
        if (res.ok) {
           setUploadStatus('Fichier supprimé. Ré-analyse achevée.');
           setTimeout(() => { setUploadStatus(''); fetchAnalysis(); }, 2000);
        } else {
           setUploadStatus('Erreur lors de la suppression.');
        }
    } catch(e) {
        setUploadStatus('Erreur réseau lors de la suppression.');
    }
  };


  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <div className="status-dot active" style={{ width: '16px', height: '16px' }}></div>
        <span style={{ color: 'var(--accent-cyan)', fontFamily: 'Outfit' }}>Loading Agents Data...</span>
      </div>
    );
  }

  const riskColor = data.global_risk > 0.7 ? 'var(--accent-crimson)' : 'var(--accent-warning)';

  return (
    <div className="animate-fade-in">
      <div className="header-container">
        <div>
          <h1 className="title-gradient">Gulf Analysis Dashboard</h1>
          <p className="subtitle">Real-time fusion of Pollution, Marine, Fishing, & Tourism metrics</p>
        </div>
        <button className="glass-button" onClick={() => window.location.reload()}>
          Force Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem' }}>
        
        {/* Risk Score Panel */}
        <div className="glass-panel" style={{ gridColumn: 'span 4', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem' }}>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Global Risk Score</h3>
          <div style={{ 
            width: '180px', height: '180px', borderRadius: '50%', 
            border: `8px solid ${riskColor}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 0 30px ${riskColor}40`,
            marginBottom: '1rem'
            }}>
            <span style={{ fontSize: '3rem', fontWeight: 700, color: '#fff', fontFamily: 'Outfit' }}>
              {Math.round(data.global_risk * 100)}<span style={{ fontSize: '1.5rem', opacity: 0.7 }}>%</span>
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
            <AlertTriangle size={16} color={riskColor} />
            <span>Confidence: {Math.round(data.confidence * 100)}%</span>
          </div>
        </div>

        {/* Modules Grid */}
        <div style={{ gridColumn: 'span 8', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          
          <div className="glass-panel delay-1 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <Droplets color="var(--accent-cyan)" />
              <h3>Pollution</h3>
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>
              Level: <strong style={{ color: '#fff' }}>{data.modules.pollution.level.toUpperCase()}</strong><br/>
              Source: <span style={{ color: 'var(--accent-warning)' }}>{data.modules.pollution.source}</span>
            </div>
          </div>

          <div className="glass-panel delay-1 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <Wind color="var(--accent-emerald)" />
              <h3>Marine & Wind</h3>
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>
              Speed: <strong style={{ color: '#fff' }}>{data.modules.marine.wind_speed} km/h</strong><br/>
              Spread: <span style={{ color: 'var(--accent-warning)' }}>{data.modules.marine.wind_effect.replace('_', ' ')}</span>
            </div>
          </div>

          <div className="glass-panel delay-2 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <Anchor color="var(--accent-blue)" />
              <h3>Fishing</h3>
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>
              Trend: <strong style={{ color: 'var(--accent-crimson)' }}>{data.modules.fishing.trend.toUpperCase()}</strong><br/>
              Zones: <span style={{ color: 'var(--accent-warning)' }}>{data.modules.fishing.best_zones ? data.modules.fishing.best_zones.join(', ') : '...'}</span><br/>
              Poissons: <span>{data.modules.fishing.fish_types_expected ? data.modules.fishing.fish_types_expected.join(', ') : '...'}</span><br/>
              Insight: <span style={{ fontSize: '0.8rem' }}>{data.modules.fishing.insight}</span>
            </div>
          </div>

          <div className="glass-panel delay-2 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <Map color="#a78bfa" />
              <h3>Tourism</h3>
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>
              Status: <strong style={{ color: '#fff' }}>{data.modules.tourism.status.toUpperCase()}</strong><br/>
              Avg Stay: <span>{data.modules.tourism.avg_stay_days} days</span><br/>
              Insight: <span style={{ fontSize: '0.8rem' }}>{data.modules.tourism.insight}</span>
            </div>
          </div>

        </div>

        {/* Recommendations */}
        <div className="glass-panel delay-3 animate-fade-in" style={{ gridColumn: 'span 12' }}>
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>Agent Recommendations</h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {data.recommendations.map((rec, i) => (
              <li key={i} style={{ 
                background: 'rgba(255,255,255,0.03)', 
                padding: '1rem', 
                borderRadius: '8px', 
                borderLeft: `4px solid ${rec.priority === 'high' ? 'var(--accent-crimson)' : 'var(--accent-warning)'}`
              }}>
                <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{rec.priority} Priority</span>
                <p style={{ marginTop: '0.25rem', color: '#fff' }}>{rec.text}</p>
              </li>
            ))}
          </ul>
        </div>
        
        {/* Upload Section */}
        <div className="glass-panel delay-3 animate-fade-in" style={{ gridColumn: 'span 12', marginTop: '1rem' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Mettre à Jour la Donnée (PDF Audit ou Excel Pêche)</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <label className="glass-button" style={{ display: 'inline-block', cursor: 'pointer' }}>
              + Uploader un ou plusieurs Fichiers
              <input type="file" multiple accept=".pdf,.xlsx,.csv" style={{ display: 'none' }} onChange={handleFileUpload} disabled={uploading}/>
            </label>
            {uploadStatus && (
              <span style={{ color: uploading ? 'var(--accent-cyan)' : 'var(--accent-emerald)', fontSize: '0.9rem' }}>
                {uploading && <span className="status-dot active"></span>}
                {uploadStatus}
              </span>
            )}
          </div>
          
          <div style={{ marginTop: '1.5rem', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>📚 Fichiers Actifs Référencés par l'IA :</h4>
            <div style={{ display: 'flex', gap: '2rem' }}>
                <div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)' }}>INDUSTRIE (Qdrant RAG)</span>
                    <ul style={{ listStyle: 'none', marginTop: '0.25rem' }}>
                        {activeFiles.industry.length > 0 ? activeFiles.industry.map(f => (
                            <li key={f} style={{ fontSize: '0.85rem', color: '#9ca3af', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                📄 {f}
                                <button onClick={() => handleDeleteFile('industry', f)} style={{ background: 'none', border: 'none', cursor: 'pointer', opacity: 0.6 }} title="Supprimer de l'IA">🗑️</button>
                            </li>
                        )) : <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Aucun PDF</span>}
                    </ul>
                </div>
                <div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue)' }}>PÊCHE (CSV/Excel)</span>
                    <ul style={{ listStyle: 'none', marginTop: '0.25rem' }}>
                        {activeFiles.fishing.length > 0 ? activeFiles.fishing.map(f => (
                            <li key={f} style={{ fontSize: '0.85rem', color: '#9ca3af', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                📊 {f}
                                <button onClick={() => handleDeleteFile('fishing', f)} style={{ background: 'none', border: 'none', cursor: 'pointer', opacity: 0.6 }} title="Supprimer de l'IA">🗑️</button>
                            </li>
                        )) : <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Aucun Excel</span>}
                    </ul>
                </div>
            </div>
          </div>
        </div>

        {/* XAI Explanation Section */}
        {data.xai_explanation && (
          <div className="glass-panel delay-4 animate-fade-in" style={{ gridColumn: 'span 12', marginTop: '1.5rem', borderLeft: '4px solid var(--accent-blue)' }}>
            <h2 style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
              🤖 XAI : Explicabilité des Décisions (Transparence)
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>Raisonnement Tourisme</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>{data.xai_explanation.tourism_reasoning}</p>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: '#a78bfa', marginBottom: '0.5rem' }}>Raisonnement Pollution & Marine</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>{data.xai_explanation.pollution_reasoning}</p>
              </div>
            </div>

            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>🎯 Recommandations Sectorielles Ciblées</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
              <div style={{ background: 'rgba(167, 139, 250, 0.1)', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(167, 139, 250, 0.2)' }}>
                <h4 style={{ color: '#a78bfa', marginBottom: '0.5rem' }}>🏖️ Autorités Tourisme</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{data.xai_explanation.actionable_targets?.tourism_authorities}</p>
              </div>
              <div style={{ background: 'rgba(0, 240, 255, 0.1)', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(0, 240, 255, 0.2)' }}>
                <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>🎣 Pêcheurs Locaux</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{data.xai_explanation.actionable_targets?.fishermen}</p>
              </div>
              <div style={{ background: 'rgba(52, 211, 153, 0.1)', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(52, 211, 153, 0.2)' }}>
                <h4 style={{ color: 'var(--accent-emerald)', marginBottom: '0.5rem' }}>🏭 Industrie & GCT</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{data.xai_explanation.actionable_targets?.industrial_sector}</p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default Dashboard;
