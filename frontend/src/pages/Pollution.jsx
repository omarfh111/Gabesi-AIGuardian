import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePollution } from '../hooks/usePollution';
import PollutionMap from '../components/pollution/PollutionMap';
import RiskBadge from '../components/pollution/RiskBadge';
import EventsTable from '../components/pollution/EventsTable';
import TrendChart from '../components/pollution/TrendChart';
import { FileDown, TrendingUp, TrendingDown, Minus, Activity, ShieldAlert } from 'lucide-react';
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
        `${API_BASE_URL}/api/v1/pollution/dossier`,
        {
          farmer_id: 'demo_farmer',
          plot_id: 'bahria_plot_a',
          language: 'en',
          window_days: 30,
        },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Gabes_Pollution_Report_${data.report_id.slice(0,8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="w-6 h-6 text-red-500" />;
    if (trend === 'decreasing') return <TrendingDown className="w-6 h-6 text-green-500" />;
    return <Minus className="w-6 h-6 text-gray-400" />;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)]">
        <div className="flex flex-col items-center gap-4 text-primary opacity-70">
          <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-primary"></div>
          <p className="text-sm font-bold animate-pulse">Calculating exposure risk...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)]">
        <div className="text-red-500 font-semibold bg-red-50 p-6 rounded-2xl flex flex-col items-center gap-3">
            <ShieldAlert className="w-10 h-10" />
            {error || 'No data available'}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:h-[calc(100vh-64px)]">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
        {/* Left Column: Map */}
        <div className="h-[400px] lg:h-full rounded-2xl overflow-hidden shadow-sm border bg-white relative z-0">
          <PollutionMap />
        </div>

        {/* Right Column: Stats Panel */}
        <div className="flex flex-col gap-6 lg:overflow-y-auto pr-1 pb-6">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border shadow-sm">
            <h1 className="text-xl font-bold text-primary flex items-center gap-2">
                <ShieldAlert className="w-6 h-6" />
                {t('pollution.title')}
            </h1>
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-danger text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 hover:bg-red-600 transition-colors disabled:opacity-50 text-xs shadow-sm"
            >
              <FileDown className="w-4 h-4 shrink-0" />
              <span className="hidden sm:inline">{isDownloading ? 'Generating...' : t('pollution.downloadPdf')}</span>
              <span className="sm:hidden">{isDownloading ? '...' : 'PDF'}</span>
            </button>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="col-span-2 lg:col-span-3">
              <RiskBadge level={data.insights.risk_level} />
            </div>
            
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">SO₂ Mean</span>
              <span className="text-2xl font-black text-gray-800">{Math.round(data.so2_stats?.mean || 0)} <span className="text-[10px] font-normal uppercase tracking-widest text-gray-400">µg</span></span>
            </div>
            
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">NO₂ Mean</span>
              <span className="text-2xl font-black text-gray-800">{Math.round(data.no2_stats?.mean || 0)} <span className="text-[10px] font-normal uppercase tracking-widest text-gray-400">µg</span></span>
            </div>

            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center col-span-2 lg:col-span-1">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Exposure Trend</span>
              {getTrendIcon(data.insights.trend)}
              <span className="text-xs font-black uppercase text-gray-800 mt-2">{data.insights.trend}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200 flex items-center justify-between shadow-sm">
              <span className="text-xs font-bold text-yellow-800 uppercase tracking-wider">Elevated<br/>Events</span>
              <span className="text-3xl font-black text-yellow-600">{data.total_elevated_days}</span>
            </div>
            <div className="bg-red-50 p-4 rounded-xl border border-red-200 flex items-center justify-between shadow-sm">
              <span className="text-xs font-bold text-red-800 uppercase tracking-wider">Severe<br/>Events</span>
              <span className="text-3xl font-black text-red-600">{data.total_severe_days}</span>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-warning" />
              SO₂ Event Trend (30 Days)
            </h3>
            <TrendChart events={data.events} />
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Recent Events Log</h3>
            <EventsTable events={data.events?.slice(0, 5)} />
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Pollution;
