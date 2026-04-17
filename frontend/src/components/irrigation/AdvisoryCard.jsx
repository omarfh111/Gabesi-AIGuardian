import React from 'react';
import { useTranslation } from 'react-i18next';
import { Droplets, Wind, Thermometer, Droplet, AlertCircle, Sun } from 'lucide-react';

const AdvisoryCard = ({ data }) => {
  const { t } = useTranslation();
  if (!data) return null;

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full">
      <div className="text-center space-y-1 mb-6">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">{t('irrigation.applyWater', { mm: '' }).replace('  ', ' ').trim() || 'Water needed today'}</h3>
        <div className="text-5xl font-black text-primary flex items-end justify-center gap-2">
          {data.irrigation_depth_mm}
          <span className="text-lg font-bold uppercase mb-1 text-gray-500">mm</span>
        </div>
      </div>

      <div className="bg-accent/10 border border-accent/20 p-5 rounded-xl text-sm font-medium leading-relaxed text-gray-800 text-center mb-6">
        {data.advisory_text}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 flex flex-col items-center justify-center">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1 text-center">ET₀ (Reference)</span>
          <span className="text-2xl font-black text-gray-800">{data.et0_mm_day} <span className="text-[10px] font-normal tracking-widest text-gray-400">MM</span></span>
        </div>
        <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 flex flex-col items-center justify-center">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1 text-center">Kc (Factor)</span>
          <span className="text-2xl font-black text-gray-800">{data.kc}</span>
        </div>
      </div>

      {data.rs_estimated && (
        <div className="flex items-center justify-center gap-2 text-xs font-bold text-orange-700 bg-orange-50 p-3 rounded-xl border border-orange-200 mb-6 shadow-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>⚠️ Solar radiation estimated (cloud cover assumed)</span>
        </div>
      )}

      <div className="border-t pt-5 mt-auto">
        <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center justify-center gap-2 shadow-sm rounded-full bg-gray-50 w-fit mx-auto px-3 py-1 border border-gray-100">
          Current Weather
        </h4>
        <div className="grid grid-cols-4 gap-2">
          <div className="flex flex-col items-center justify-center bg-gray-50 py-3 rounded-xl">
            <Thermometer className="w-5 h-5 text-red-500 mb-1" />
            <span className="text-xs font-bold text-gray-700">{Math.round(data.weather.tmax_c)}° / {Math.round(data.weather.tmin_c)}°</span>
          </div>
          <div className="flex flex-col items-center justify-center bg-gray-50 py-3 rounded-xl">
            <Droplet className="w-5 h-5 text-blue-500 mb-1" />
            <span className="text-xs font-bold text-gray-700">{Math.round(data.weather.rh2m_pct)}%</span>
          </div>
          <div className="flex flex-col items-center justify-center bg-gray-50 py-3 rounded-xl">
            <Wind className="w-5 h-5 text-gray-500 mb-1" />
            <span className="text-xs font-bold text-gray-700">{data.weather.ws2m_ms.toFixed(1)} <span className="text-[10px] font-normal">m/s</span></span>
          </div>
          <div className="flex flex-col items-center justify-center bg-gray-50 py-3 rounded-xl">
            <Sun className="w-5 h-5 text-yellow-500 mb-1" />
            <span className="text-xs font-bold text-gray-700">{Math.round(data.weather.rs_mj_m2_day)} <span className="text-[10px] font-normal text-gray-400">MJ</span></span>
          </div>
        </div>
      </div>
      
      <div className="flex justify-center mt-5">
        <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1">
            Data Source • <span className="text-primary bg-primary/10 px-1.5 py-0.5 rounded">NASA POWER + FAO-56</span>
        </span>
      </div>
    </div>
  );
};

export default AdvisoryCard;
