import React, { useEffect, useState } from 'react';
import { AlertTriangle, Anchor, Droplets, Map, RefreshCw, Target, Trash2, Upload, Wind } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';

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
    } catch (e) {
      console.error(e);
      setData({
        global_risk: 0.82,
        confidence: 0.76,
        zone: 'gabes',
        modules: {
          pollution: { level: 'elevated', source: 'GCT' },
          marine: { spread: 'elevated', wind_effect: 'toward coast', wind_speed: 25 },
          fishing: { trend: 'declining', insight: 'Decline over recent period' },
          tourism: { status: 'weak', avg_stay_days: 1.4 },
        },
        recommendations: [
          { text: 'Reduce discharges near coastal zones due to prevailing winds', priority: 'high' },
          { text: 'Launch targeted monitoring campaign for southern area', priority: 'normal' },
        ],
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    const initialLoad = setTimeout(() => {
      fetchAnalysis();
    }, 0);
    return () => clearTimeout(initialLoad);
  }, []);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadStatus(`Analyzing ${files.length} file(s)...`);

    const formData = new FormData();
    for (let i = 0; i < files.length; i += 1) {
      formData.append('file', files[i]);
    }

    try {
      const res = await fetch('/api/strategic/upload', {
        method: 'POST',
        body: formData,
      });
      const result = await res.json();
      setUploadStatus(result.message || 'Success');
      setTimeout(() => {
        setUploadStatus('');
        fetchAnalysis();
      }, 1500);
    } catch {
      setUploadStatus('Upload error');
    }
    setUploading(false);
  };

  const handleDeleteFile = async (type, filename) => {
    if (!window.confirm(`Delete ${filename}?`)) return;
    try {
      setUploadStatus(`Deleting ${filename}...`);
      const res = await fetch(`/api/strategic/files/${type}/${filename}`, { method: 'DELETE' });
      if (res.ok) {
        setUploadStatus('File deleted. Re-analysis complete.');
        setTimeout(() => {
          setUploadStatus('');
          fetchAnalysis();
        }, 1500);
      } else {
        setUploadStatus('Delete error');
      }
    } catch {
      setUploadStatus('Network error');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 bg-gray-50">
        <RefreshCw className="h-8 w-8 animate-spin text-sky-600" />
        <p className="text-sm text-gray-600">Loading strategic insights...</p>
      </div>
    );
  }

  const risk = Math.round((data?.global_risk || 0) * 100);
  const confidence = Math.round((data?.confidence || 0) * 100);
  const riskVariant = risk > 70 ? 'high' : risk > 45 ? 'medium' : 'low';
  const circumference = 2 * Math.PI * 74;
  const ringOffset = circumference - (risk / 100) * circumference;

  const moduleTone = {
    pollution: {
      icon: 'text-red-500',
      title: 'text-gray-900',
      border: 'border-red-200',
      bg: 'from-red-50 via-white to-white',
      value: 'text-red-600',
    },
    marine: {
      icon: 'text-cyan-500',
      title: 'text-gray-900',
      border: 'border-cyan-200',
      bg: 'from-cyan-50 via-white to-white',
      value: 'text-cyan-700',
    },
    fishing: {
      icon: 'text-emerald-500',
      title: 'text-gray-900',
      border: 'border-emerald-200',
      bg: 'from-emerald-50 via-white to-white',
      value: 'text-emerald-700',
    },
    tourism: {
      icon: 'text-violet-500',
      title: 'text-gray-900',
      border: 'border-violet-200',
      bg: 'from-violet-50 via-white to-white',
      value: 'text-violet-700',
    },
  };

  const modules = [
    {
      key: 'pollution',
      title: 'Industrial Pollution',
      Icon: Droplets,
      content: [
        `Level: ${data?.modules?.pollution?.level || 'unknown'}`,
        `Source: ${
          Array.isArray(data?.modules?.pollution?.source)
            ? data.modules.pollution.source.join(', ')
            : data?.modules?.pollution?.source || 'n/a'
        }`,
      ],
    },
    {
      key: 'marine',
      title: 'Marine Dynamics',
      Icon: Wind,
      content: [
        `Wind speed: ${data?.modules?.marine?.wind_speed || 0} km/h`,
        `Spread: ${data?.modules?.marine?.wind_effect || 'n/a'}`,
      ],
    },
    {
      key: 'fishing',
      title: 'Fisheries Status',
      Icon: Anchor,
      content: [
        `Trend: ${data?.modules?.fishing?.trend || 'unknown'}`,
        `Insight: ${data?.modules?.fishing?.insight || 'n/a'}`,
      ],
    },
    {
      key: 'tourism',
      title: 'Tourism Impact',
      Icon: Map,
      content: [
        `Status: ${data?.modules?.tourism?.status || 'unknown'}`,
        `Average stay: ${data?.modules?.tourism?.avg_stay_days || 0} days`,
      ],
    },
  ];

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gradient-to-br from-slate-50 via-white to-sky-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <Card className="rounded-xl border border-gray-200 bg-white shadow-sm">
          <CardHeader className="flex-row items-center justify-between p-5">
            <div>
              <CardTitle className="text-3xl font-semibold leading-tight text-gray-900">Strategic Intelligence Dashboard</CardTitle>
              <p className="mt-1 text-base text-gray-600">Multi-agent environmental analysis for Gulf of Gabes.</p>
            </div>
            <Button variant="secondary" onClick={fetchAnalysis}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </CardHeader>
        </Card>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <Card className="rounded-xl border border-gray-200 bg-white shadow-sm lg:col-span-4">
            <CardContent className="space-y-5 p-6 text-center">
              <p className="text-2xl font-medium text-gray-700">Global Risk Index</p>
              <div className="relative mx-auto h-56 w-56">
                <svg viewBox="0 0 180 180" className="h-full w-full -rotate-90">
                  <circle cx="90" cy="90" r="74" className="stroke-gray-200" strokeWidth="12" fill="none" />
                  <circle
                    cx="90"
                    cy="90"
                    r="74"
                    stroke={risk > 70 ? '#ef4444' : risk > 45 ? '#f59e0b' : '#22c55e'}
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={circumference}
                    strokeDashoffset={ringOffset}
                    strokeLinecap="round"
                    className="transition-all duration-700"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-6xl font-semibold text-gray-900">
                    {risk}
                    <span className="text-3xl text-gray-500">%</span>
                  </p>
                </div>
              </div>
              <div className="mx-auto flex w-fit items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
                <Badge variant={riskVariant}>risk</Badge>
                <Badge variant="neutral">confidence {confidence}%</Badge>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:col-span-8">
            {modules.map((module) => (
              <Card
                key={module.key}
                className={`rounded-xl border ${moduleTone[module.key].border} bg-gradient-to-br ${moduleTone[module.key].bg} shadow-sm`}
              >
                <CardContent className="p-5">
                  <p className={`mb-3 flex items-center gap-2 text-base font-semibold ${moduleTone[module.key].title}`}>
                    <module.Icon className={`h-6 w-6 ${moduleTone[module.key].icon}`} />
                    {module.title}
                  </p>
                  <div className="space-y-2">
                    {module.content.map((line) => (
                      <p key={line} className="text-sm leading-snug text-gray-600">
                        <span className="font-medium text-gray-500">{line.split(':')[0]}:</span>{' '}
                        <span className={`font-semibold ${moduleTone[module.key].value}`}>{line.split(':').slice(1).join(':').trim()}</span>
                      </p>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="rounded-xl border border-gray-200 bg-white shadow-sm lg:col-span-12">
            <CardHeader className="p-5 pb-2">
              <CardTitle className="flex items-center gap-2 text-base font-medium text-gray-900">
                <Target className="h-4 w-4 text-cyan-600" />
                Strategic Action Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-3 p-5 pt-2 md:grid-cols-2 lg:grid-cols-3">
              {data?.recommendations?.length ? (
                data.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className={`rounded-xl border p-4 ${
                      rec.priority === 'high' ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'
                    }`}
                  >
                    <Badge variant={rec.priority === 'high' ? 'high' : 'medium'}>{rec.priority || 'normal'}</Badge>
                    <p className="mt-2 text-sm leading-relaxed text-gray-700">{rec.text}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">No recommendations available.</p>
              )}
            </CardContent>
          </Card>

          <Card className="rounded-xl border border-gray-200 bg-white shadow-sm lg:col-span-12">
            <CardHeader className="flex-row items-center justify-between p-5">
              <CardTitle className="text-base font-medium text-gray-900">Knowledge Management</CardTitle>
              <div className="flex items-center gap-3">
                {uploadStatus ? <p className="text-sm text-gray-600">{uploadStatus}</p> : null}
                <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-500">
                  <Upload className="h-4 w-4" />
                  Upload data
                  <input type="file" multiple accept=".pdf,.xlsx,.csv" className="hidden" onChange={handleFileUpload} disabled={uploading} />
                </label>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-6 p-5 pt-2 md:grid-cols-2">
              <div>
                <p className="mb-2 text-sm font-medium text-gray-800">Industrial Audits</p>
                <div className="space-y-2">
                  {activeFiles.industry.length ? (
                    activeFiles.industry.map((f) => (
                      <div key={f} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3">
                        <p className="max-w-[85%] truncate text-sm text-gray-700">{f}</p>
                        <button onClick={() => handleDeleteFile('industry', f)} className="text-gray-500 hover:text-red-600">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No industrial files uploaded.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="mb-2 text-sm font-medium text-gray-800">Fishery Data</p>
                <div className="space-y-2">
                  {activeFiles.fishing.length ? (
                    activeFiles.fishing.map((f) => (
                      <div key={f} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3">
                        <p className="max-w-[85%] truncate text-sm text-gray-700">{f}</p>
                        <button onClick={() => handleDeleteFile('fishing', f)} className="text-gray-500 hover:text-red-600">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No fishery files uploaded.</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {data?.xai_explanation ? (
            <Card className="rounded-xl border border-gray-200 bg-white shadow-sm lg:col-span-12">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="flex items-center gap-2 text-base font-medium text-gray-900">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  XAI Decision Transparency
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-4 p-5 pt-2 md:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <p className="text-xs text-gray-500">Tourism reasoning</p>
                  <p className="mt-1 text-sm text-gray-700">{data.xai_explanation.tourism_reasoning}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <p className="text-xs text-gray-500">Pollution and marine reasoning</p>
                  <p className="mt-1 text-sm text-gray-700">{data.xai_explanation.pollution_reasoning}</p>
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Strategic;
