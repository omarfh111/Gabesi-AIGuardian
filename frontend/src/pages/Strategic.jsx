import React, { useState, useEffect } from 'react';
import { Wind, Anchor, Droplets, Map, AlertTriangle, Trash2, Upload, Target } from 'lucide-react';

const Strategic = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [activeFiles, setActiveFiles] = useState({ industry: [], fishing: [] });

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/strategic/analysis');
      const json = await res.json();
      setData(json);
      
      const filesRes = await fetch('/api/strategic/files');
      if (filesRes.ok) {
          const filesJson = await filesRes.json();
          setActiveFiles(filesJson);
      }
    } catch(e) {
      console.error(e);
      // Fallback if backend is down
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
          { text: "Lancer une campagne de surveillance sur la zone sud", priority: "normal" }
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
    setUploadStatus(`Analysing ${files.length} file(s)...`);
    
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('file', files[i]);
    }
    
    try {
      const res = await fetch('/api/strategic/upload', {
        method: 'POST',
        body: formData,
      });
      const result = await res.json();
      setUploadStatus(result.message || 'Success!');
      setTimeout(() => {
        setUploadStatus('');
        fetchAnalysis();
      }, 2000);
    } catch(err) {
      setUploadStatus('Upload Error');
    }
    setUploading(false);
  };

  const handleDeleteFile = async (type, filename) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}? The AI will lose all associated data.`)) return;
    try {
        setUploadStatus(`Purging ${filename}...`);
        const res = await fetch(`/api/strategic/files/${type}/${filename}`, { method: 'DELETE' });
        if (res.ok) {
           setUploadStatus('File deleted. Re-analysis complete.');
           setTimeout(() => { setUploadStatus(''); fetchAnalysis(); }, 2000);
        } else {
           setUploadStatus('Delete Error');
        }
    } catch(e) {
        setUploadStatus('Network Error');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
        <p className="text-accent animate-pulse">Loading Strategic Insights...</p>
      </div>
    );
  }

  const riskColor = (data?.global_risk ?? 0) > 0.7 ? '#ef4444' : '#f59e0b';

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-border pb-6">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-text-secondary bg-clip-text text-transparent">
            Strategic Intelligence Dashboard
          </h1>
          <p className="text-text-secondary mt-2">Gulf of Gabès: Multi-Agent Environmental Analysis</p>
        </div>
        <button 
          onClick={fetchAnalysis}
          className="px-4 py-2 glass-card hover:bg-accent/10 text-accent transition-all text-sm font-medium"
        >
          Force Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Global Risk Card */}
        <div className="lg:col-span-4 glass-card p-8 flex flex-col items-center justify-center text-center">
          <h3 className="text-text-secondary mb-8 font-medium">Global Risk Index</h3>
          <div 
            className="relative w-56 h-56 rounded-full border-[12px] flex items-center justify-center shadow-2xl transition-all duration-1000 mb-8"
            style={{ 
              borderColor: riskColor,
              boxShadow: `0 0 50px ${riskColor}20`
            }}
          >
            <div className="text-center">
              <span className="text-6xl font-black text-white leading-none">
                {data?.global_risk ? Math.round(data.global_risk * 100) : 0}<span className="text-2xl opacity-50 ml-1">%</span>
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-3 px-6 py-3 bg-white/5 rounded-2xl border border-white/10">
            <AlertTriangle size={20} className={(data?.global_risk ?? 0) > 0.7 ? "text-danger" : "text-warning"} />
            <div className="text-left">
              <p className="text-[10px] uppercase font-black text-text-muted leading-tight">AI Confidence Score</p>
              <p className="text-white font-bold">{data?.confidence ? Math.round(data.confidence * 100) : 0}%</p>
            </div>
          </div>
        </div>

        {/* Modules Grid */}
        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div className="glass-card p-6 border-l-4 border-l-accent">
            <div className="flex items-center gap-3 mb-4">
              <Droplets className="text-accent" />
              <h3 className="font-semibold text-lg">Industrial Pollution</h3>
            </div>
            <div className="space-y-3 text-sm">
              <p className="text-text-secondary">Level: <span className="text-white font-bold">{data.modules?.pollution?.level?.toUpperCase() || 'UNKNOWN'}</span></p>
              <p className="text-text-secondary text-xs">Primary Source: <span className="text-warning font-bold">
                {Array.isArray(data.modules?.pollution?.source) ? data.modules.pollution.source.join(', ') : (data.modules?.pollution?.source || 'N/A')}
              </span></p>
              
              {/* Detailed Capacities Context */}
              {data.modules?.pollution?.insight?.capacités_de_production && (
                <div className="mt-3 p-2 bg-white/5 rounded-lg border border-white/5 grid grid-cols-2 gap-x-4 gap-y-1">
                  {Object.entries(data.modules.pollution.insight.capacités_de_production).slice(0, 4).map(([cat, val]) => (
                    <div key={cat} className="text-[10px] text-text-muted flex justify-between">
                      <span className="truncate mr-1">{cat.split('_').pop()}:</span>
                      <span className="text-white font-mono">{Object.values(val)[0]}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="glass-card p-6 border-l-4 border-l-emerald-400">
            <div className="flex items-center gap-3 mb-4">
              <Wind className="text-emerald-400" />
              <h3 className="font-semibold text-lg">Marine Dynamics</h3>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-text-secondary">Wind Speed: <span className="text-white font-bold">{data.modules?.marine?.wind_speed || 0} km/h</span></p>
              <p className="text-text-secondary">Spread Direction: <span className="text-warning font-bold">{data.modules?.marine?.wind_effect?.replace('_', ' ') || 'N/A'}</span></p>
            </div>
          </div>

          <div className="glass-card p-6 border-l-4 border-l-blue-400">
            <div className="flex items-center gap-3 mb-4">
              <Anchor className="text-blue-400" />
              <h3 className="font-semibold text-lg">Fisheries Status</h3>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-text-secondary">Economic Trend: <span className={`font-bold ${data.modules?.fishing?.trend?.includes('hausse') ? 'text-emerald-400' : 'text-danger'}`}>
                {data.modules?.fishing?.trend?.toUpperCase() || 'UNKNOWN'}
              </span></p>
              <p className="text-text-secondary">Production: <span className="text-white font-mono">{data.modules?.fishing?.estimated_production_tons || 0} Tons</span></p>
              <p className="text-text-secondary text-xs">Expected Catch: <span className="text-white/80 italic">{data.modules?.fishing?.fish_types_expected?.join(', ') || '...'}</span></p>
            </div>
          </div>

          <div className="glass-card p-6 border-l-4 border-l-purple-400">
            <div className="flex items-center gap-3 mb-4">
              <Map className="text-purple-400" />
              <h3 className="font-semibold text-lg">Tourism Impact</h3>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-text-secondary">Sector Status: <span className="text-white font-bold">{data.modules?.tourism?.status?.toUpperCase() || 'UNKNOWN'}</span></p>
              <p className="text-text-secondary">Avg. Stay: <span className="text-white font-bold">{data.modules?.tourism?.avg_stay_days || 0} days</span></p>
            </div>
          </div>
        </div>

        {/* Action Plan Section */}
        <div className="lg:col-span-12 glass-card p-8">
            <div className="flex items-center gap-3 mb-6">
                <Target className="text-accent" />
                <h2 className="text-xl font-bold">Strategic Action Plan</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data?.recommendations?.map((rec, i) => (
                    <div key={i} className="bg-white/5 p-5 rounded-2xl border border-white/10 border-l-4 transition-all hover:bg-white/10"
                        style={{ borderLeftColor: rec.priority === 'high' ? '#ef4444' : '#06b6d4' }}>
                        <span className={`text-[10px] font-black uppercase px-2 py-1 rounded ${rec.priority === 'high' ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent'}`}>
                            {rec.priority || 'NORMAL'} PRIORITY
                        </span>
                        <p className="mt-3 text-white text-sm leading-relaxed">{rec.text}</p>
                    </div>
                )) || <p className="col-span-full text-text-muted italic text-center py-8">No strategic recommendations available at this time.</p>}
            </div>
        </div>

        {/* XAI Explanation */}
        {data.xai_explanation && (
          <div className="lg:col-span-12 glass-card p-8 border-t-2 border-t-accent/30 bg-gradient-to-br from-secondary to-primary">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-accent/10 rounded-lg text-accent">
                <AlertTriangle size={24} />
              </div>
              <h2 className="text-xl font-bold">XAI: Decision Transparency</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="p-6 bg-white/5 rounded-2xl border border-white/10">
                <h4 className="text-accent font-black uppercase text-xs mb-3 tracking-widest">Tourism Reasoning</h4>
                <p className="text-text-secondary text-sm leading-relaxed">{data.xai_explanation.tourism_reasoning}</p>
              </div>
              <div className="p-6 bg-white/5 rounded-2xl border border-white/10">
                <h4 className="text-purple-400 font-black uppercase text-xs mb-3 tracking-widest">Pollution & Marine Logic</h4>
                <p className="text-text-secondary text-sm leading-relaxed">{data.xai_explanation.pollution_reasoning}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-purple-400/10 rounded-xl border border-purple-400/20">
                <h4 className="text-purple-400 font-bold mb-2 text-xs uppercase tracking-wider">🏖️ Tourism Authorities</h4>
                <p className="text-text-secondary text-[11px] leading-relaxed">{data.xai_explanation.actionable_targets?.tourism_authorities}</p>
              </div>
              <div className="p-4 bg-accent/10 rounded-xl border border-accent/20">
                <h4 className="text-accent font-bold mb-2 text-xs uppercase tracking-wider">🎣 Local Fishermen</h4>
                <p className="text-text-secondary text-[11px] leading-relaxed">{data.xai_explanation.actionable_targets?.fishermen}</p>
              </div>
              <div className="p-4 bg-emerald-400/10 rounded-xl border border-emerald-400/20">
                <h4 className="text-emerald-400 font-bold mb-2 text-xs uppercase tracking-wider">🏭 Industry Sector</h4>
                <p className="text-text-secondary text-[11px] leading-relaxed">{data.xai_explanation.actionable_targets?.industrial_sector}</p>
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Management */}
        <div className="lg:col-span-12 glass-card p-8">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-lg font-bold">Knowledge Management</h3>
            <div className="flex items-center gap-4">
              {uploadStatus && (
                <span className="text-accent text-sm flex items-center gap-2">
                  <div className="w-2 h-2 bg-accent rounded-full animate-ping" />
                  {uploadStatus}
                </span>
              )}
              <label className="flex items-center gap-2 px-6 py-2.5 bg-accent text-primary rounded-xl font-black cursor-pointer hover:bg-white transition-all shadow-lg shadow-accent/20 text-xs uppercase tracking-widest">
                <Upload size={16} />
                Upload New Data
                <input type="file" multiple accept=".pdf,.xlsx,.csv" className="hidden" onChange={handleFileUpload} disabled={uploading}/>
              </label>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="space-y-4">
              <h4 className="text-accent text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                <Droplets size={14} /> Industrial Audits (Qdrant RAG)
              </h4>
              <div className="space-y-2">
                {activeFiles.industry.length > 0 ? activeFiles.industry.map(f => (
                  <div key={f} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl group border border-transparent hover:border-white/10 transition-all">
                    <span className="text-xs text-text-secondary overflow-hidden text-ellipsis whitespace-nowrap max-w-[80%] flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                        {f}
                    </span>
                    <button onClick={() => handleDeleteFile('industry', f)} className="p-2 text-text-muted hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity">
                      <Trash2 size={16} />
                    </button>
                  </div>
                )) : <p className="text-text-muted text-xs italic p-4 bg-white/5 rounded-2xl">No PDF documents indexed in vector database.</p>}
              </div>
            </div>
            <div className="space-y-4">
              <h4 className="text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                <Anchor size={14} /> Fishery Data (Excel/CSV)
              </h4>
              <div className="space-y-2">
                {activeFiles.fishing.length > 0 ? activeFiles.fishing.map(f => (
                  <div key={f} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl group border border-transparent hover:border-white/10 transition-all">
                    <span className="text-xs text-text-secondary overflow-hidden text-ellipsis whitespace-nowrap max-w-[80%] flex items-center gap-2">
                         <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                        {f}
                    </span>
                    <button onClick={() => handleDeleteFile('fishing', f)} className="p-2 text-text-muted hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity">
                      <Trash2 size={16} />
                    </button>
                  </div>
                )) : <p className="text-text-muted text-xs italic p-4 bg-white/5 rounded-2xl">No historical fishery data files uploaded.</p>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Strategic;
