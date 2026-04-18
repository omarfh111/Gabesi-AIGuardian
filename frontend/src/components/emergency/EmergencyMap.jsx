import React, { useState, useEffect } from 'react';
import {
  MapContainer, TileLayer, Circle, Marker, Popup, useMapEvents, useMap
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import Sparkline from './Sparkline';

// Fix default marker icons
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
    html: `<div style="width:16px;height:16px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 0 15px ${color},0 2px 5px rgba(0,0,0,.4)"></div>
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

// Sub-component: captures map clicks when in selection mode
function MapClickHandler({ isSelecting, onLocationSelected }) {
  useMapEvents({
    click(e) {
      if (isSelecting) onLocationSelected(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Sub-component: handles programmatic flyTo from sidebar
function FlyController({ flyTarget, onFlyComplete }) {
  const map = useMap();
  useEffect(() => {
    if (flyTarget) {
      map.flyTo([flyTarget.lat, flyTarget.lng], flyTarget.zoom || 14, { duration: 1.2 });
      onFlyComplete();
    }
  }, [flyTarget]);
  return null;
}

const MONTHS_RAW = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

const EmergencyMap = ({
  isSelecting, onLocationSelected, manualMarker,
  circles, locations, onDeleteLocation,
  flyTarget, onFlyComplete,
  globalRisk, riskColor,
}) => {
  const [monthIndex, setMonthIndex] = useState(5);

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[33.88, 10.08]}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        zoomControl
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; OpenStreetMap &copy; CARTO"
          maxZoom={19}
        />

        <MapClickHandler isSelecting={isSelecting} onLocationSelected={onLocationSelected} />
        <FlyController flyTarget={flyTarget} onFlyComplete={onFlyComplete || (() => {})} />

        {/* Pollution circles */}
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
                fillOpacity: isDanger ? 0.65 : currentCO2 > 1500 ? 0.4 : 0.15,
                color,
                weight: isDanger ? 3 : 1.5,
                opacity: isDanger ? 0.8 : 0.5,
              }}
            >
              <Popup>
                <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 240, padding: 4, color: '#eef0f8' }}>
                  <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 2, color }}>
                    {isDanger ? 'CRITICAL POLLUTION ZONE' : circle.label}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
                    {circle.label} — {currentDaily} t/day
                  </div>
                  <div style={{ fontSize: 10, color: '#8b95b8', marginBottom: 8 }}>{circle.anchor}</div>
                  <span style={{
                    background: `${color}1a`, color, padding: '3px 10px',
                    borderRadius: 12, fontSize: 10, fontWeight: 700, textTransform: 'uppercase'
                  }}>
                    Risk: {riskLabel}
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 6, marginTop: 10, marginBottom: 8 }}>
                    {[
                      { val: currentDaily, label: 't/day', color: '#06b6d4' },
                      { val: circle.maxCO2, label: 'Max (m)', color },
                      { val: circle.threshold, label: 'Threshold', color: '#eef0f8' },
                    ].map(({ val, label, color: c }) => (
                      <div key={label} style={{ textAlign: 'center', padding: 4, background: 'rgba(255,255,255,.04)', borderRadius: 6 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: c }}>{val}</div>
                        <div style={{ fontSize: 8, textTransform: 'uppercase', color: '#4d567a' }}>{label}</div>
                      </div>
                    ))}
                  </div>
                  {circle.monthlyData && (
                    <div>
                      <div style={{ fontSize: 9, textTransform: 'uppercase', color: '#4d567a', marginBottom: 2 }}>Trend (6 Months)</div>
                      <Sparkline data={circle.monthlyData} color={color} height={30} />
                    </div>
                  )}
                </div>
              </Popup>
            </Circle>
          );
        })}

        {/* Location markers */}
        {locations.map((loc) => {
          const color = CAT_COLORS[loc.category] || '#8b95b8';
          return (
            <Marker key={loc.id} position={[loc.lat, loc.lng]} icon={createMarkerIcon(loc.category)}>
              <Popup>
                <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 200, padding: 4, color: '#eef0f8' }}>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6 }}>{loc.name}</div>
                  <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                    <span style={{ background: `${color}18`, color, padding: '2px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600, textTransform: 'uppercase' }}>{loc.category}</span>
                    <span style={{ background: '#8b5cf618', color: '#8b5cf6', padding: '2px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600 }}>{loc.zone || '?'}</span>
                  </div>
                  <div style={{ fontSize: 11, color: '#8b95b8', marginBottom: 8 }}>
                    <div>Lat: {loc.lat.toFixed(6)}</div>
                    <div>Lng: {loc.lng.toFixed(6)}</div>
                  </div>
                  <button
                    onClick={() => onDeleteLocation(loc.id)}
                    style={{ background: 'rgba(239,68,68,.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,.3)', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', width: '100%' }}
                  >
                    Delete location
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Manual emergency marker */}
        {manualMarker && (
          <Marker position={[manualMarker.lat, manualMarker.lng]}>
            <Popup>
              <div style={{ fontFamily: 'Inter, sans-serif', color: '#ef4444', fontWeight: 700 }}>
                Emergency Location<br />
                <span style={{ fontSize: 10, color: '#8b95b8', fontWeight: 400 }}>
                  {manualMarker.lat.toFixed(5)}, {manualMarker.lng.toFixed(5)}
                </span>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Category chips overlay */}
      <div className="absolute top-4 left-4 z-[800] flex gap-2 flex-wrap">
        {[
          { key: 'industrial', label: 'Industrial', color: '#ef4444' },
          { key: 'agriculture', label: 'Agriculture', color: '#10b981' },
          { key: 'coastal', label: 'Coastal', color: '#06b6d4' },
          { key: 'urban', label: 'Urban', color: '#f59e0b' },
        ].map(({ key, label, color }) => {
          const count = locations.filter(l => l.category === key).length;
          return (
            <div key={key} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold"
              style={{ background: 'rgba(12,16,32,.88)', backdropFilter: 'blur(16px)', border: '1px solid #1e2548' }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
              <span className="text-gray-300">{count} {label}</span>
            </div>
          );
        })}
      </div>
      
      {/* Global Risk Overlay (Top Right) */}
      {globalRisk !== undefined && (
        <div className="absolute top-4 right-4 z-[800] flex flex-col items-end gap-1.5 animate-in fade-in slide-in-from-right-4 duration-1000">
          <div className="flex items-center gap-3 px-4 py-2.5 rounded-2xl glass-card border-white/5 shadow-2xl">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
              style={{ background: `${riskColor}15`, border: `1px solid ${riskColor}30`, color: riskColor }}>
              ⚠️
            </div>
            <div>
              <div className="text-[14px] font-black tracking-tight" style={{ color: riskColor }}>
                GLOBAL RISK: {globalRisk}/100
              </div>
              <div className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">
                ENVIRONMENTAL ADVISORY
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full glass border-white/5">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#10b981]" />
            <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">System Active</span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-20 right-4 z-[800] p-4 rounded-xl text-xs"
        style={{ background: 'rgba(12,16,32,.88)', backdropFilter: 'blur(16px)', border: '1px solid #1e2548' }}>
        <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">CO₂ Impact Level</div>
        {[
          { color: '#ef4444', label: 'Danger (>1800 t/day)' },
          { color: '#f59e0b', label: 'Warning (1500–1800)' },
          { color: '#10b981', label: 'Safe (<1500 t/day)' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-2 mb-1 text-gray-300">
            <div className="w-3 h-3 rounded-full border border-white/20" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>

      {/* Timeline slider */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[800] flex items-center gap-3 px-5 py-2 rounded-[30px] min-w-[320px]"
        style={{ background: 'rgba(12,16,32,.88)', backdropFilter: 'blur(16px)', border: '1px solid #1e2548' }}>
        <div className="text-[11px] font-bold text-white min-w-[80px] text-center">
          {MONTHS_RAW[monthIndex]} 2026
        </div>
        <input
          type="range" min="0" max="5" value={monthIndex} step="1"
          onChange={e => setMonthIndex(Number(e.target.value))}
          className="flex-1 h-1 cursor-pointer accent-cyan-400"
        />
      </div>

      {isSelecting && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[900] px-4 py-2 rounded-full text-white text-xs font-black uppercase animate-bounce"
          style={{ background: '#ef4444', boxShadow: '0 0 20px rgba(239,68,68,.6)' }}>
          Click anywhere on the map to select emergency location
        </div>
      )}
    </div>
  );
};

export default EmergencyMap;
