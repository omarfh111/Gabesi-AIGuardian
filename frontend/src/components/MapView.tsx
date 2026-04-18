import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useAppStore } from '../store';
import { LeafletMouseEvent } from 'leaflet';
import L from 'leaflet';
import ReportPopup from './ReportPopup';

// Fix Leaflet default icon issue in bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const ISSUE_COLORS: Record<string, string> = {
  smoke: '#ef4444',
  smell: '#a855f7',
  dust: '#eab308',
  water: '#3b82f6',
  waste: '#16a34a',
  symptoms: '#f97316',
};

function createColoredIcon(issueType: string): L.DivIcon {
  const color = ISSUE_COLORS[issueType] || '#6b7280';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 28px;
      height: 28px;
      background: ${color};
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
}

const MapEvents = () => {
  const setSelectedLocation = useAppStore((state) => state.setSelectedLocation);
  const isModalOpen = useAppStore((state) => state.isModalOpen);

  useMapEvents({
    click(e: LeafletMouseEvent) {
      if (!isModalOpen) {
        setSelectedLocation({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    },
  });
  return null;
};

export default function MapView() {
  const reports = useAppStore((state) => state.reports);
  const isModalOpen = useAppStore((state) => state.isModalOpen);

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={[33.8815, 10.0982]}
        zoom={12}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEvents />

        {reports.map((report: any) => (
          <Marker
            key={report.id}
            position={[report.rounded_lat, report.rounded_lng]}
            icon={createColoredIcon(report.issue_type)}
          >
            <Popup maxWidth={320} minWidth={260}>
              <ReportPopup
                reportId={report.id}
                issueType={report.issue_type}
                createdAt={report.created_at}
                severity={report.severity}
                description={report.description}
              />
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {!isModalOpen && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white/90 backdrop-blur-md px-6 py-3 rounded-full shadow-lg z-[1000] border border-gray-100 pointer-events-none">
          <p className="text-gray-700 font-medium tracking-wide text-sm">
            🌍 Click anywhere on the map to report an issue
          </p>
        </div>
      )}
    </div>
  );
}
