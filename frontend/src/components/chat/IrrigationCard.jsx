import React from 'react';
import { useTranslation } from 'react-i18next';
import { Droplets, Wind, Thermometer, Droplet, AlertCircle, CloudRain } from 'lucide-react';

const IrrigationCard = ({ data }) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-accent">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <Droplets className="w-6 h-6" />
          </div>
          <h3 className="font-black text-lg uppercase tracking-tighter leading-none">{t('irrigation.title')}</h3>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-accent leading-none">
            {data.irrigation_depth_mm}
            <span className="text-sm font-bold ml-1 uppercase">mm</span>
          </div>
          <span className="text-[9px] text-text-muted font-black uppercase tracking-widest block mt-1">
            24H Water Budget
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="glass p-3 rounded-xl flex flex-col items-center">
          <span className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">ET₀ (Reference)</span>
          <span className="text-sm font-black text-text-primary">{data.et0_mm_day} <span className="text-[10px] text-text-muted">mm</span></span>
        </div>
        <div className="glass p-3 rounded-xl flex flex-col items-center">
          <span className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Kc (Crop factor)</span>
          <span className="text-sm font-black text-text-primary">{data.kc}</span>
        </div>
      </div>

      <div className="text-sm leading-relaxed text-text-primary font-medium p-4 glass-card bg-accent/5 border-accent/10">
        {data.advisory_text}
      </div>

      {data.rs_estimated && (
        <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-warning bg-warning/10 px-3 py-1.5 rounded-lg border border-warning/20 w-fit">
          <AlertCircle className="w-3.5 h-3.5" />
          Solar data estimated (Cloud cover detected)
        </div>
      )}

      <div className="grid grid-cols-4 gap-4 pt-4 border-t border-white/10">
        <div className="flex flex-col items-center gap-1.5">
          <Thermometer className="w-4 h-4 text-danger" />
          <span className="text-[10px] font-black text-text-primary">
            {data.weather.tmax_c}°/{data.weather.tmin_c}°
          </span>
        </div>
        <div className="flex flex-col items-center gap-1.5">
          <Droplet className="w-4 h-4 text-accent" />
          <span className="text-[10px] font-black text-text-primary">
            {Math.round(data.weather.rh2m_pct)}%
          </span>
        </div>
        <div className="flex flex-col items-center gap-1.5">
          <Wind className="w-4 h-4 text-purple" />
          <span className="text-[10px] font-black text-text-primary">
            {data.weather.ws2m_ms.toFixed(1)}m/s
          </span>
        </div>
        <div className="flex flex-col items-center gap-1.5 group">
          <CloudRain className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors" />
          <span className="text-[8px] font-black text-text-muted uppercase tracking-tighter">NASA SAT</span>
        </div>
      </div>
    </div>
  );
};

export default IrrigationCard;
