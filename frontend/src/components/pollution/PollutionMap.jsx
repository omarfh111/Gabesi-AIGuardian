import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';

// Fix for default marker icon in leaflet
import 'leaflet/dist/leaflet.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const GCT_COORDS = [33.9089, 10.1256];

const zones = [
  { radius: 2000, color: 'red', opacity: 0.3 },
  { radius: 5000, color: 'orange', opacity: 0.2 },
  { radius: 10000, color: 'yellow', opacity: 0.15 },
  { radius: 15000, color: 'green', opacity: 0.1 },
];

const PollutionMap = () => {
  return (
    <MapContainer center={GCT_COORDS} zoom={11} scrollWheelZoom={false} className="h-full w-full z-0">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={GCT_COORDS}>
        <Popup className="font-bold">
          Groupe Chimique Tunisien<br />
          <span className="font-normal text-xs text-gray-500">Primary pollution source</span>
        </Popup>
      </Marker>
      {zones.map((zone, idx) => (
        <Circle
          key={idx}
          center={GCT_COORDS}
          radius={zone.radius}
          pathOptions={{ color: zone.color, fillColor: zone.color, fillOpacity: zone.opacity, weight: 1 }}
        />
      ))}
    </MapContainer>
  );
};

export default PollutionMap;
