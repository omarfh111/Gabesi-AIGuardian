import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FileDown, Activity, AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../../config';

const PollutionReportCard = ({ data }) => {
  const { t } = useTranslation();
  const [isDownloading, setIsDownloading] = useState(false);

  const riskColors = {
    low: 'bg-green-500',
    moderate: 'bg-yellow-500',
    high: 'bg-red-500',
    critical: 'bg-red-700',
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (trend === 'decreasing') return <TrendingDown className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const handleDownload = async () => {
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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2 text-danger">
          <AlertCircle className="w-5 h-5" />
          <h3 className="font-bold text-base uppercase tracking-tight">Pollution Exposure Summary</h3>
        </div>
        <div className={`px-2 py-1 rounded text-[10px] font-black text-white uppercase ${riskColors[data.insights.risk_level] || 'bg-gray-500'}`}>
          {data.insights.risk_level} Risk
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
          <span className="text-[10px] font-bold text-gray-400 uppercase block mb-1">Elevated Days</span>
          <div className="text-xl font-black text-warning">
            {data.total_elevated_days}
          </div>
        </div>
        <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
          <span className="text-[10px] font-bold text-gray-400 uppercase block mb-1">Severe Days</span>
          <div className="text-xl font-black text-danger">
            {data.total_severe_days}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm px-1 font-medium">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-400" />
          <span>Dominant: <strong className="uppercase">{data.insights.dominant_pollutant}</strong></span>
        </div>
        <div className="flex items-center gap-2 capitalize">
          Trend: {getTrendIcon(data.insights.trend)}
          <span>{data.insights.trend}</span>
        </div>
      </div>

      <button
        onClick={handleDownload}
        disabled={isDownloading}
        className="w-full bg-danger text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-red-600 transition-colors disabled:opacity-50"
      >
        <FileDown className="w-5 h-5" />
        {isDownloading ? 'Generating PDF...' : t('pollution.downloadPdf')}
      </button>

      <div className="text-[10px] text-gray-400 text-center italic">
        Report Generated: {new Date(data.generated_at).toLocaleDateString()}
      </div>
    </div>
  );
};

export default PollutionReportCard;
