import React from 'react';
import { useTranslation } from 'react-i18next';
import { Droplets, Wind, Thermometer, Droplet, AlertCircle } from 'lucide-react';

const IrrigationCard = ({ data }) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b pb-3">
        <div className="flex items-center gap-2 text-primary">
          <Droplets className="w-6 h-6" />
          <h3 className="font-bold text-lg">{t('irrigation.title')}</h3>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-primary leading-none">
            {data.irrigation_depth_mm}
            <span className="text-sm font-bold ml-1 uppercase">mm</span>
          </div>
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
            Water needed today
          </span>
        </div>
      </div>

      <div className="bg-gray-50 rounded-xl p-3 grid grid-cols-2 gap-4">
        <div className="text-center border-r border-gray-200">
          <span className="text-[10px] block text-gray-500 font-bold uppercase">ET₀ (Reference)</span>
          <span className="font-mono font-bold text-gray-700">{data.et0_mm_day} mm</span>
        </div>
        <div className="text-center">
          <span className="text-[10px] block text-gray-500 font-bold uppercase">Kc (Crop factor)</span>
          <span className="font-mono font-bold text-gray-700">{data.kc}</span>
        </div>
      </div>

      <div className="text-sm leading-relaxed font-medium">
        {data.advisory_text}
      </div>

      {data.rs_estimated && (
        <div className="flex items-center gap-2 text-[10px] font-bold text-orange-600 bg-orange-50 px-2 py-1 rounded w-fit">
          <AlertCircle className="w-3 h-3" />
          SOLAR RADIATION DATA ESTIMATED
        </div>
      )}

      <div className="grid grid-cols-4 gap-2 pt-3 border-t">
        <div className="flex flex-col items-center gap-1">
          <Thermometer className="w-3 h-3 text-red-500" />
          <span className="text-[10px] font-bold text-gray-600 italic">
            {data.weather.tmax_c}°/{data.weather.tmin_c}°
          </span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <Droplet className="w-3 h-3 text-blue-500" />
          <span className="text-[10px] font-bold text-gray-600 italic">
            {Math.round(data.weather.rh2m_pct)}%
          </span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <Wind className="w-3 h-3 text-gray-500" />
          <span className="text-[10px] font-bold text-gray-600 italic">
            {data.weather.ws2m_ms.toFixed(1)}m/s
          </span>
        </div>
        <div className="flex flex-col items-center gap-1 opacity-50">
          <span className="text-[8px] font-bold text-gray-400 uppercase">NASA POWER</span>
        </div>
      </div>
    </div>
  );
};

export default IrrigationCard;
