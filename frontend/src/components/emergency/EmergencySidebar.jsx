import React, { useState } from 'react';
import {
  Brain,
  FileClock,
  Gauge,
  Loader2,
  MapPin,
  Search,
  Trash2,
  TrendingUp,
} from 'lucide-react';
import Sparkline from './Sparkline';
import { Badge, Button, Card, CardContent, FormField, Input, Select } from '../ui';

const RISK_COLORS = { danger: '#ef4444', warning: '#f59e0b', safe: '#10b981' };
const CAT_COLORS = { industrial: '#ef4444', agriculture: '#10b981', coastal: '#06b6d4', urban: '#f59e0b' };
const TABS = [
  { key: 'pollution', icon: Gauge, label: 'Pollution' },
  { key: 'locations', icon: MapPin, label: 'Locations' },
  { key: 'analysis', icon: Brain, label: 'AI Analysis' },
  { key: 'logs', icon: FileClock, label: 'Logs' },
];

const EmergencySidebar = ({
  overview, circles, locations, logs, onSearch, onDeleteLocation, onFlyTo, onFlyToCircle,
}) => {
  const [activeTab, setActiveTab] = useState('pollution');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchFeedback, setSearchFeedback] = useState({ text: '', type: '' });
  const [selectedFacility, setSelectedFacility] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

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
        setSearchFeedback({ text: `${data.name} -> ${data.category} / ${data.zone} (${data.elapsed}s)`, type: 'success' });
        setSearchQuery('');
        onFlyTo(data.lat, data.lng);
        onSearch();
      } else {
        setSearchFeedback({ text: data.error || 'Failed to add location.', type: 'error' });
      }
    } catch (err) {
      setSearchFeedback({ text: `Network error: ${err.message}`, type: 'error' });
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFacility) {
      alert('Please select a facility to analyze.');
      return;
    }
    setAnalysisLoading(true);
    try {
      const res = await fetch('/analyze-zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ facility: selectedFacility, zoneType: 'industrial' }),
      });
      const data = await res.json();
      setAnalysis(data);
    } catch {
      // noop
    } finally {
      setAnalysisLoading(false);
    }
  };

  const renderPollution = () => {
    const sorted = [...circles].sort((a, b) => b.riskScore - a.riskScore);
    if (!sorted.length) return <Empty text="Loading pollution data..." />;
    return sorted.map((c) => (
      <Card
        key={c.key}
        className="cursor-pointer border border-gray-200 bg-white transition hover:-translate-y-0.5 hover:border-sky-300"
        onClick={() => onFlyToCircle(c.lat, c.lng)}
      >
        <CardContent className="space-y-3 p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-semibold text-gray-900">{c.label}</p>
            <Badge
              variant={c.riskLevel === 'danger' ? 'high' : c.riskLevel === 'warning' ? 'medium' : 'low'}
              className="uppercase"
            >
              {c.riskLabel} {c.riskScore}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <StatBox label="t/day" value={c.meanDailyCO2} color="text-cyan-700" />
            <StatBox label="Max (m)" value={c.maxCO2} color="text-amber-700" />
            <StatBox label="Exceed" value={c.exceedanceCount} color="text-gray-800" />
          </div>
          {c.monthlyData ? <Sparkline data={c.monthlyData} color={c.color || RISK_COLORS[c.riskLevel]} height={30} /> : null}
          <div className="h-1.5 rounded-full bg-gray-100">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${Math.min(100, c.riskScore)}%`,
                background: RISK_COLORS[c.riskLevel],
              }}
            />
          </div>
        </CardContent>
      </Card>
    ));
  };

  const renderLocations = () => {
    if (!locations.length) return <Empty text="No locations yet. Search for a place to get started." />;
    return locations.map((loc) => {
      const color = CAT_COLORS[loc.category] || '#94a3b8';
      return (
        <Card
          key={loc.id}
          className="cursor-pointer border border-gray-200 bg-white transition hover:-translate-y-0.5 hover:border-sky-300"
          onClick={() => onFlyTo(loc.lat, loc.lng)}
        >
          <CardContent className="space-y-2 p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-gray-900">{loc.name}</p>
                <p className="text-xs text-gray-500">
                  {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
                  style={{ color, background: `${color}22` }}
                >
                  {loc.category}
                </span>
                <button
                  type="button"
                  className="rounded-md p-1 text-gray-500 transition hover:bg-red-100 hover:text-red-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteLocation(loc.id);
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-500">Zone: {loc.zone || 'unknown'}</p>
          </CardContent>
        </Card>
      );
    });
  };

  const renderAnalysis = () => {
    const a = analysis;
    const diag = a?.analysis?.diagnostic || {};
    const recs = a?.recommendations?.recommendations || [];
    const metrics = a?.analysis?.metrics || {};
    const carbon = a?.recommendations?.carbonMarket || {};
    const regulatory = a?.recommendations?.regulatoryAlert || {};

    return (
      <Card className="border border-gray-200 bg-white">
        <CardContent className="space-y-4 p-3">
          <FormField label="Facility">
            <Select
              value={selectedFacility}
              onChange={(e) => setSelectedFacility(e.target.value)}
              className="border-gray-300 bg-white text-gray-900 focus:border-sky-500"
            >
              <option value="" style={{ color: '#111827', backgroundColor: '#ffffff' }}>Select a facility to analyze...</option>
              {circles.map((c) => (
                <option key={c.key} value={c.key} style={{ color: '#111827', backgroundColor: '#ffffff' }}>
                  {c.label} (Risk: {c.riskScore})
                </option>
              ))}
            </Select>
          </FormField>
          <Button className="w-full" onClick={handleAnalyze} disabled={analysisLoading}>
            {analysisLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
            {analysisLoading ? 'Analyzing...' : 'Analyze with AI'}
          </Button>

          {a ? (
            <div className="space-y-3">
              {diag.summary ? <InfoRow title="Diagnostic" text={diag.summary} /> : null}
              {diag.trend ? <InfoRow title="Trend" text={`${diag.trend} ${diag.trendDetail || ''}`} /> : null}
              {diag.seasonalPattern ? <InfoRow title="Seasonal Pattern" text={diag.seasonalPattern} /> : null}
              {diag.complianceDetail ? <InfoRow title="Compliance" text={diag.complianceDetail} /> : null}

              {metrics.peakMonth ? (
                <div className="grid grid-cols-2 gap-2">
                  <StatBox label={metrics.peakMonth} value={`${metrics.peakValue} t`} color="text-red-700" />
                  <StatBox label={metrics.lowestMonth} value={`${metrics.lowestValue} t`} color="text-green-700" />
                </div>
              ) : null}

              {recs.length ? (
                <div className="space-y-2">
                  {recs.map((r, i) => (
                    <div key={`${r.title}-${i}`} className="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
                      <div className="mb-1 flex items-center gap-2">
                        <Badge
                          variant={r.priority === 'critique' ? 'high' : r.priority === 'important' ? 'medium' : 'low'}
                          className="uppercase"
                        >
                          {r.priority}
                        </Badge>
                        <p className="text-sm font-medium text-gray-900">{r.title}</p>
                      </div>
                      <p className="text-xs text-gray-600">{r.description}</p>
                    </div>
                  ))}
                </div>
              ) : null}

              {carbon.eligible !== undefined ? (
                <p className="rounded-lg border border-gray-200 bg-gray-50 p-2 text-xs text-gray-700">
                  Carbon Market: {carbon.eligible ? 'Eligible' : 'Not eligible'} - {carbon.detail}
                </p>
              ) : null}

              {regulatory.hasAlert ? (
                <p className="rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700">
                  Regulatory Alert: {regulatory.detail}
                </p>
              ) : null}

              <p className="text-center text-[11px] text-gray-500">Completed in {a.elapsed || '?'}s via GPT-4o-mini</p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    );
  };

  const renderLogs = () => {
    if (!logs.length) return <Empty text="No logs yet." />;
    return logs.map((log, i) => {
      const statusColor =
        log.status === 'success' ? 'text-green-700 bg-green-100' : log.status === 'rejected' ? 'text-amber-700 bg-amber-100' : 'text-red-700 bg-red-100';
      const time = new Date(log.timestamp).toLocaleTimeString();
      return (
        <Card key={i} className="border border-gray-200 bg-white">
          <CardContent className="flex items-center gap-2 p-2.5">
            <div className={`rounded-md px-2 py-1 text-[11px] font-semibold uppercase ${statusColor}`}>{log.status}</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-gray-900">{log.query}</p>
              <p className="truncate text-xs text-gray-500">{log.detail || ''}</p>
            </div>
            <div className="text-right text-[11px] text-gray-500">
              {log.elapsed ? <p>{log.elapsed}s</p> : null}
              <p>{time}</p>
            </div>
          </CardContent>
        </Card>
      );
    });
  };

  return (
    <aside className="flex h-full flex-col bg-white text-gray-900">
      <div className="space-y-3 border-b border-gray-200 p-3">
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search location in Gabes..."
            className="border-gray-300 bg-white text-gray-900 placeholder:text-gray-400 focus:border-sky-500"
          />
          <Button onClick={handleSearch} disabled={searchLoading}>
            {searchLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Search
          </Button>
        </div>
        {searchFeedback.text ? (
          <p
            className={`text-xs ${
              searchFeedback.type === 'success'
                ? 'text-green-700'
                : searchFeedback.type === 'error'
                ? 'text-red-700'
                : 'text-sky-700'
            }`}
          >
            {searchFeedback.text}
          </p>
        ) : null}
      </div>

      {overview ? (
        <div className="grid grid-cols-3 gap-2 border-b border-gray-200 p-3">
          <StatTile label="Avg CO2/day" value={overview.avgDailyCO2} color="text-cyan-700" />
          <StatTile
            label="Total 6 months"
            value={
              overview.gctSynthesis?.totalCO2_6months > 1000
                ? `${Math.round(overview.gctSynthesis.totalCO2_6months / 1000)}k`
                : overview.gctSynthesis?.totalCO2_6months
            }
            color="text-violet-700"
          />
          <StatTile
            label="Exceedance"
            value={overview.gctSynthesis?.exceedanceRate}
            color={parseInt(overview.gctSynthesis?.exceedanceRate, 10) > 25 ? 'text-red-700' : 'text-amber-700'}
          />
        </div>
      ) : null}

      <div className="grid grid-cols-4 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`flex flex-col items-center gap-1 px-1 py-2 text-[11px] font-medium transition ${
              activeTab === tab.key ? 'border-b-2 border-sky-500 bg-sky-50 text-sky-700' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            {React.createElement(tab.icon, { className: 'h-3.5 w-3.5' })}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto p-2.5">
        {activeTab === 'pollution' ? renderPollution() : null}
        {activeTab === 'locations' ? renderLocations() : null}
        {activeTab === 'analysis' ? renderAnalysis() : null}
        {activeTab === 'logs' ? renderLogs() : null}
      </div>
    </aside>
  );
};

const Empty = ({ text }) => (
  <Card className="border border-dashed border-gray-300 bg-gray-50">
    <CardContent className="py-8 text-center text-sm text-gray-500">
      <TrendingUp className="mx-auto mb-2 h-5 w-5 text-gray-400" />
      {text}
    </CardContent>
  </Card>
);

const StatBox = ({ label, value, color }) => (
  <div className="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-center">
    <p className={`text-sm font-semibold ${color}`}>{value ?? '--'}</p>
    <p className="text-[10px] uppercase tracking-wide text-gray-500">{label}</p>
  </div>
);

const StatTile = ({ label, value, color }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-2 text-center">
    <p className={`text-xl font-semibold ${color}`}>{value ?? '--'}</p>
    <p className="text-[10px] uppercase tracking-wide text-gray-500">{label}</p>
  </div>
);

const InfoRow = ({ title, text }) => (
  <div>
    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-sky-700">{title}</p>
    <p className="text-xs leading-relaxed text-gray-700">{text}</p>
  </div>
);

export default EmergencySidebar;
