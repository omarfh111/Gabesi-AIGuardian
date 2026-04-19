import React, { useEffect, useState } from 'react';
import { AlertTriangle, CalendarClock, ShieldCheck } from 'lucide-react';
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import Sparkline from './Sparkline';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const CAT_COLORS = {
  industrial: '#ef4444',
  agriculture: '#10b981',
  coastal: '#06b6d4',
  urban: '#f59e0b',
};

const RISK_COLORS = { danger: '#ef4444', warning: '#f59e0b', safe: '#10b981' };

function createMarkerIcon(category) {
  const color = CAT_COLORS[category] || '#8b95b8';
  return L.divIcon({
    className: '',
    html: `<div style="width:16px;height:16px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 0 12px ${color},0 2px 5px rgba(0,0,0,.4)"></div>
           <div style="width:2px;height:10px;background:linear-gradient(to bottom,white,${color});margin:-2px auto 0;opacity:.8"></div>`,
    iconSize: [16, 24],
    iconAnchor: [8, 24],
    popupAnchor: [0, -26],
  });
}

function getCO2Radius(co2) {
  return 50 + Math.log2(Math.max(1, co2 / 100)) * 15 * 50;
}

function getRiskColor(co2) {
  if (co2 > 1800) return RISK_COLORS.danger;
  if (co2 > 1500) return RISK_COLORS.warning;
  return RISK_COLORS.safe;
}

function getRiskLabel(co2) {
  if (co2 > 1800) return 'DANGER';
  if (co2 > 1500) return 'WARNING';
  return 'SAFE';
}

function MapClickHandler({ isSelecting, onLocationSelected }) {
  useMapEvents({
    click(e) {
      if (isSelecting) onLocationSelected(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function FlyController({ flyTarget, onFlyComplete }) {
  const map = useMap();
  useEffect(() => {
    if (!flyTarget) return;
    map.flyTo([flyTarget.lat, flyTarget.lng], flyTarget.zoom || 14, { duration: 1.2 });
    onFlyComplete();
  }, [flyTarget, map, onFlyComplete]);
  return null;
}

const MONTHS_RAW = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

const EmergencyMap = ({
  isSelecting, onLocationSelected, manualMarker, circles, locations, onDeleteLocation, flyTarget, onFlyComplete, globalRisk, riskColor,
}) => {
  const [monthIndex, setMonthIndex] = useState(5);

  return (
    <div className="relative h-full w-full">
      <MapContainer center={[33.88, 10.08]} zoom={11} style={{ height: '100%', width: '100%' }} zoomControl>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; OpenStreetMap &copy; CARTO"
          maxZoom={19}
        />

        <MapClickHandler isSelecting={isSelecting} onLocationSelected={onLocationSelected} />
        <FlyController flyTarget={flyTarget} onFlyComplete={onFlyComplete || (() => {})} />

        {circles.map((circle) => {
          const monthData = circle.monthlyData?.[monthIndex];
          const currentCO2 = monthData ? monthData.co2 : circle.meanCO2;
          const currentDaily = Math.round(currentCO2 / 30);
          const color = getRiskColor(currentCO2);
          const riskLabel = getRiskLabel(currentCO2);
          const isDanger = currentCO2 > 1800;

          return (
            <Circle
              key={circle.key}
              center={[circle.lat, circle.lng]}
              radius={getCO2Radius(currentCO2)}
              pathOptions={{
                fillColor: color,
                fillOpacity: isDanger ? 0.6 : currentCO2 > 1500 ? 0.38 : 0.14,
                color,
                weight: isDanger ? 3 : 1.5,
                opacity: isDanger ? 0.85 : 0.5,
              }}
            >
              <Popup>
                <div className="min-w-[250px] space-y-2 p-1 text-gray-800">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{circle.label}</p>
                      <p className="text-[11px] text-gray-500">{circle.anchor}</p>
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
                      style={{ color, background: `${color}22` }}
                    >
                      {riskLabel}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <Metric value={currentDaily} label="t/day" color="#22d3ee" />
                    <Metric value={circle.maxCO2} label="Max" color={color} />
                    <Metric value={circle.threshold} label="Limit" color="#cbd5e1" />
                  </div>
                  {circle.monthlyData ? <Sparkline data={circle.monthlyData} color={color} height={30} /> : null}
                </div>
              </Popup>
            </Circle>
          );
        })}

        {locations.map((loc) => {
          const color = CAT_COLORS[loc.category] || '#8b95b8';
          return (
            <Marker key={loc.id} position={[loc.lat, loc.lng]} icon={createMarkerIcon(loc.category)}>
              <Popup>
                <div className="min-w-[220px] space-y-2 p-1 text-gray-800">
                  <p className="text-sm font-semibold text-gray-900">{loc.name}</p>
                  <div className="flex gap-2">
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" style={{ color, background: `${color}22` }}>
                      {loc.category}
                    </span>
                    <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-semibold text-violet-300">
                      {loc.zone || '?'}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    {loc.lat.toFixed(6)}, {loc.lng.toFixed(6)}
                  </p>
                  <button
                    type="button"
                    onClick={() => onDeleteLocation(loc.id)}
                    className="w-full rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1.5 text-xs font-medium text-red-300 transition hover:bg-red-500/20"
                  >
                    Delete location
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {manualMarker ? (
          <Marker position={[manualMarker.lat, manualMarker.lng]}>
            <Popup>
              <div className="p-1 text-sm font-semibold text-red-700">
                Emergency Location
                <p className="text-[11px] font-normal text-gray-500">
                  {manualMarker.lat.toFixed(5)}, {manualMarker.lng.toFixed(5)}
                </p>
              </div>
            </Popup>
          </Marker>
        ) : null}
      </MapContainer>

      <div className="pointer-events-none absolute left-4 top-4 z-[800] flex flex-wrap gap-2">
        {[
          { key: 'industrial', label: 'Industrial', color: '#ef4444' },
          { key: 'agriculture', label: 'Agriculture', color: '#10b981' },
          { key: 'coastal', label: 'Coastal', color: '#06b6d4' },
          { key: 'urban', label: 'Urban', color: '#f59e0b' },
        ].map(({ key, label, color }) => {
          const count = locations.filter((l) => l.category === key).length;
          return (
            <div key={key} className="flex items-center gap-1.5 rounded-full border border-white/90 bg-white/95 px-3 py-1 text-xs text-slate-700 shadow-sm backdrop-blur">
              <span className="h-2 w-2 rounded-full" style={{ background: color }} />
              {count} {label}
            </div>
          );
        })}
      </div>

      {globalRisk !== undefined ? (
        <div className="absolute right-4 top-4 z-[800] flex flex-col items-end gap-2">
          <div className="flex items-center gap-3 rounded-2xl border border-white/90 bg-white/95 px-4 py-2.5 text-slate-800 shadow-md backdrop-blur">
            <div className="rounded-lg p-2" style={{ background: `${riskColor}1f`, border: `1px solid ${riskColor}33` }}>
              <AlertTriangle className="h-4 w-4" style={{ color: riskColor }} />
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: riskColor }}>
                Global Risk: {globalRisk}/100
              </p>
              <p className="text-[10px] uppercase tracking-wide text-slate-500">Environmental advisory</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-white/95 px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-700 shadow-sm backdrop-blur">
            <ShieldCheck className="h-3.5 w-3.5" />
            System active
          </div>
        </div>
      ) : null}

      <div className="absolute bottom-[160px] right-4 z-[800] rounded-xl border border-white/90 bg-white/95 p-3 text-xs text-slate-700 shadow-sm backdrop-blur">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">CO2 Impact Level</p>
        {[
          { color: '#ef4444', label: 'Danger (>1800 t/day)' },
          { color: '#f59e0b', label: 'Warning (1500-1800)' },
          { color: '#10b981', label: 'Safe (<1500 t/day)' },
        ].map(({ color, label }) => (
          <div key={label} className="mb-1.5 flex items-center gap-2">
            <span className="h-3 w-3 rounded-full border border-white/20" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>

      <div className="absolute bottom-4 left-1/2 z-[800] flex min-w-[320px] -translate-x-1/2 items-center gap-3 rounded-full border border-white/90 bg-white/95 px-5 py-2 shadow-sm backdrop-blur">
        <div className="flex min-w-[90px] items-center gap-1 text-xs font-semibold text-slate-800">
          <CalendarClock className="h-3.5 w-3.5 text-sky-300" />
          {MONTHS_RAW[monthIndex]} 2026
        </div>
        <input
          type="range"
          min="0"
          max="5"
          value={monthIndex}
          step="1"
          onChange={(e) => setMonthIndex(Number(e.target.value))}
          className="h-1 w-full cursor-pointer accent-sky-400"
        />
      </div>

      {isSelecting ? (
        <div className="absolute left-1/2 top-4 z-[900] -translate-x-1/2 rounded-full border border-red-400/40 bg-red-500/85 px-4 py-2 text-xs font-semibold text-white shadow-md">
          Click on map to set emergency location
        </div>
      ) : null}
    </div>
  );
};

const Metric = ({ value, label, color }) => (
  <div className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-center">
    <p className="text-sm font-semibold" style={{ color }}>
      {value}
    </p>
    <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
  </div>
);

export default EmergencyMap;
