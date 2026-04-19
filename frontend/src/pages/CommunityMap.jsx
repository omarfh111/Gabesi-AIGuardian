import React, { useCallback, useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import L from 'leaflet';
import 'leaflet.markercluster';
import { MousePointerClick, SearchX } from 'lucide-react';
import { API_BASE_URL } from '../config';
import FiltersPanel from '../components/community/FiltersPanel';
import MapHeader from '../components/community/MapHeader';
import MarkerPopup from '../components/community/MarkerPopup';
import ReportModal from '../components/community/ReportModal';
import { getIssueMeta, ISSUE_TYPES } from '../components/community/issueMeta';
import { Card, CardContent } from '../components/ui';

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function createIcon(type) {
  const color = getIssueMeta(type).color;
  return L.divIcon({
    className: '',
    html: `<div class="w-6 h-6 rounded-full border-2 border-white shadow-md" style="background:${color}"></div>`,
    iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -14],
  });
}

// API points to the unified backend (FastAPI)
const API = `${API_BASE_URL}/api/v1/community`;

function MapClick({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function ClusterLayer({ reports, onSelectReport }) {
  const map = useMap();
  const clusterRef = useRef(null);

  useEffect(() => {
    if (!map) return undefined;
    if (clusterRef.current) map.removeLayer(clusterRef.current);

    const cluster = L.markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 60,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      iconCreateFunction: (c) => {
        const count = c.getChildCount();
        const children = c.getAllChildMarkers();
        const typeCounts = {};
        children.forEach((m) => {
          const type = m.options._issueType || 'waste';
          typeCounts[type] = (typeCounts[type] || 0) + 1;
        });
        const dominant = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'waste';
        const color = getIssueMeta(dominant).color;
        const size = count < 10 ? 40 : count < 30 ? 55 : 70;

        return L.divIcon({
          className: '',
          html: `<div class="relative flex items-center justify-center rounded-full shadow-lg border-2 border-white/90 text-white font-bold" style="width:${size}px;height:${size}px;background:${color}">
            <div class="absolute inset-0 rounded-full animate-ping opacity-20" style="background:${color}"></div>
            <span class="relative z-10 ${count < 10 ? 'text-xs' : 'text-sm'}">${count}</span>
          </div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        });
      },
    });

    reports.forEach((r) => {
      const marker = L.marker([r.rounded_lat, r.rounded_lng], {
        icon: createIcon(r.issue_type),
        _issueType: r.issue_type,
      });
      marker.on('click', () => onSelectReport(r));
      cluster.addLayer(marker);
    });

    map.addLayer(cluster);
    clusterRef.current = cluster;
    return () => {
      if (clusterRef.current) map.removeLayer(clusterRef.current);
    };
  }, [map, reports, onSelectReport]);

  return null;
}

export default function CommunityMap() {
  const [reports, setReports] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [clickPos, setClickPos] = useState(null);
  const [form, setForm] = useState({ issue_type: 'waste', severity: 'medium', description: '', symptoms: '' });
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  const loadReports = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const params = new URLSearchParams();
      if (filterType) params.set('issue_type', filterType);
      if (filterSeverity) params.set('severity', filterSeverity);
      const res = await fetch(`${API}/reports?${params}`);
      if (res.ok) setReports(await res.json());
    } catch (e) {
      console.error('fetch error', e);
    } finally {
      setIsRefreshing(false);
    }
  }, [filterType, filterSeverity]);

  useEffect(() => {
    const firstLoad = setTimeout(() => {
      loadReports();
    }, 0);
    const i = setInterval(() => {
      loadReports();
    }, 30000);
    return () => {
      clearInterval(i);
      clearTimeout(firstLoad);
    };
  }, [loadReports]);

  const handleMapClick = (lat, lng) => {
    if (!modalOpen) {
      setClickPos({ lat, lng });
      setModalOpen(true);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!clickPos) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: clickPos.lat,
          lng: clickPos.lng,
          issue_type: form.issue_type,
          severity: form.severity,
          description: form.description || null,
          symptom_tags: form.symptoms ? form.symptoms.split(',').map((s) => s.trim()) : [],
        }),
      });
      if (res.ok) {
        setModalOpen(false);
        loadReports();
        setForm({ issue_type: 'waste', severity: 'medium', description: '', symptoms: '' });
      } else alert('Submit failed');
    } catch {
      alert('Network error - is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-[calc(100vh-4rem)] w-full min-h-[680px] bg-gray-100">
      <MapContainer center={[33.8815, 10.0982]} zoom={12} scrollWheelZoom className="z-0 h-full w-full">
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapClick onMapClick={handleMapClick} />
        <ClusterLayer reports={reports} onSelectReport={setSelectedReport} />
      </MapContainer>

      <MapHeader reportCount={reports.length} isModalOpen={modalOpen} isRefreshing={isRefreshing} />

      {!modalOpen && (
        <Card className="pointer-events-none absolute left-1/2 top-20 z-10 -translate-x-1/2 rounded-xl bg-white/90 backdrop-blur">
          <CardContent className="flex items-center gap-2 p-3">
            <MousePointerClick className="h-4 w-4 text-sky-700" />
            <p className="text-sm text-gray-700">Click anywhere on the map to report an issue</p>
          </CardContent>
        </Card>
      )}

      {!isRefreshing && reports.length === 0 && (
        <Card className="pointer-events-none absolute left-1/2 top-36 z-10 -translate-x-1/2 rounded-xl bg-white/95 backdrop-blur">
          <CardContent className="flex items-center gap-2 p-3">
            <SearchX className="h-4 w-4 text-gray-500" />
            <p className="text-sm text-gray-700">No reports match the current filters</p>
          </CardContent>
        </Card>
      )}

      <FiltersPanel
        types={ISSUE_TYPES}
        filterType={filterType}
        setFilterType={setFilterType}
        filterSeverity={filterSeverity}
        setFilterSeverity={setFilterSeverity}
        reportCount={reports.length}
        isRefreshing={isRefreshing}
      />

      <ReportModal
        isOpen={modalOpen && !!clickPos}
        onClose={() => setModalOpen(false)}
        clickPos={clickPos}
        form={form}
        setForm={setForm}
        onSubmit={handleSubmit}
        loading={loading}
      />

      {selectedReport && !modalOpen && (
        <MarkerPopup
          key={selectedReport.id}
          report={selectedReport}
          apiBase={API}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}
