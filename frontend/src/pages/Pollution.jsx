import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePollution } from '../hooks/usePollution';
import PollutionMap from '../components/pollution/PollutionMap';
import RiskBadge from '../components/pollution/RiskBadge';
import EventsTable from '../components/pollution/EventsTable';
import TrendChart from '../components/pollution/TrendChart';
import { FileDown, TrendingUp, TrendingDown, Minus, Activity, ShieldAlert, BarChart3, Wind } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const Pollution = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, fetchReport } = usePollution();
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    fetchReport({
      farmer_id: 'demo_farmer',
      plot_id: 'bahria_plot_a',
      language: 'en',
      window_days: 30,
    });
  }, [fetchReport]);

  const handleDownload = async () => {
    if (!data) return;
    setIsDownloading(true);
    try {
      const resp = await axios.post(
        `${API_BASE_URL}/api/v1/pollution/pdf`,
        {
          farmer_id: 'demo_farmer',
          plot_id: 'bahria_plot_a',
          language: 'en',
          window_days: 30,
        },
        { responseType: 'blob' }
      );

      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `pollution_dossier_${data.report_id.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="w-8 h-8 text-danger" />;
    if (trend === 'decreasing') return <TrendingDown className="w-8 h-8 text-green-400" />;
    return <Minus className="w-8 h-8 text-text-muted" />;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-[calc(100vh-64px)] bg-primary text-accent">
        <div className="relative w-16 h-16 mb-6">
          <div className="absolute inset-0 border-4 border-accent/20 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
        </div>
        <p className="text-xs font-black uppercase tracking-[0.2em] animate-pulse">Calculating exposure risk...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)] bg-primary">
        <div className="glass-card border-danger/30 p-8 flex flex-col items-center gap-4">
            <ShieldAlert className="w-12 h-12 text-danger" />
            <span className="text-sm font-black uppercase tracking-widest text-danger">{error || 'No data available'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-primary min-h-[calc(100vh-64px)] overflow-hidden flex flex-col">
      {/* Dashboard Sub-Header */}
      <div className="px-6 py-4 glass border-b border-border flex justify-between items-center relative z-20">
        <div className="flex items-center gap-4">
          <div className="p-3 glass-card bg-accent/10 border-accent/20">
            <Wind className="w-6 h-6 text-accent" />
          </div>
          <div>
            <h1 className="text-xl font-black uppercase tracking-tighter text-text-primary leading-none">
              {t('pollution.title')}
            </h1>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mt-1">
              Exposure Risk Dossier · Gabès Oasis Plot A
            </p>
          </div>
        </div>
        <button
          onClick={handleDownload}
          disabled={isDownloading}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-danger text-white text-[11px] font-black uppercase tracking-widest hover:bg-red-600 transition-all shadow-lg shadow-danger/20 disabled:opacity-50"
        >
          <FileDown className="w-4 h-4" />
          {isDownloading ? 'Processing...' : t('pollution.downloadPdf')}
        </button>
      </div>

      <div className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-y-auto">
        {/* Left: Map Section */}
        <div className="lg:col-span-7 glass-card overflow-hidden h-[400px] lg:h-full group relative">
          <div className="absolute top-4 left-4 z-10 flex gap-2">
            <span className="px-3 py-1.5 glass rounded-full text-[10px] font-black uppercase tracking-widest text-accent border-accent/30">
              Live Satellite Feed
            </span>
          </div>
          <PollutionMap />
        </div>

        {/* Right: Insights Section */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="col-span-1 md:col-span-2">
              <RiskBadge level={data.insights.risk_level} />
            </div>
            
            <div className="glass-card p-6 flex flex-col items-center justify-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Activity className="w-12 h-12" />
              </div>
              <span className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-3">SO₂ Average</span>
              <span className="text-3xl font-black text-text-primary">
                {Math.round(data.so2_stats?.mean || 0)} 
                <span className="text-xs text-text-muted ml-2">µg/m³</span>
              </span>
            </div>
            
            <div className="glass-card p-6 flex flex-col items-center justify-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <BarChart3 className="w-12 h-12" />
              </div>
              <span className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-3">NO₂ Average</span>
              <span className="text-3xl font-black text-text-primary">
                {Math.round(data.no2_stats?.mean || 0)} 
                <span className="text-xs text-text-muted ml-2">µg/m³</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="glass-card p-6 border-warning/20 group hover:border-warning/40">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[10px] font-black text-warning uppercase tracking-widest">Elevated Events</span>
                <Activity className="w-4 h-4 text-warning" />
              </div>
              <span className="text-4xl font-black text-warning">{data.total_elevated_days}</span>
              <div className="mt-2 text-[9px] font-bold text-text-muted uppercase">Last 30 Days</div>
            </div>
            <div className="glass-card p-6 border-danger/20 group hover:border-danger/40">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[10px] font-black text-danger uppercase tracking-widest">Severe Events</span>
                <ShieldAlert className="w-4 h-4 text-danger" />
              </div>
              <span className="text-4xl font-black text-danger">{data.total_severe_days}</span>
              <div className="mt-2 text-[9px] font-bold text-text-muted uppercase">Immediate Action Zone</div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] flex items-center gap-3">
                <Activity className="w-4 h-4 text-accent" />
                SO₂ Concentration Timeline
              </h3>
              <span className="text-[10px] font-black text-accent uppercase tracking-widest">30 Day Trend</span>
            </div>
            <TrendChart events={data.events} />
          </div>

          <div className="glass-card p-6 flex-1 min-h-[300px]">
            <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-6">Critical Event Log</h3>
            <EventsTable events={data.events?.slice(0, 5)} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pollution;
