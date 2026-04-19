import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import AgricultureChat from '../components/emergency/AgricultureChat';
import EmergencyChat from '../components/emergency/EmergencyChat';
import EmergencyMap from '../components/emergency/EmergencyMap';
import EmergencySidebar from '../components/emergency/EmergencySidebar';

const Emergency = () => {
  const [circles, setCircles] = useState([]);
  const [locations, setLocations] = useState([]);
  const [logs, setLogs] = useState([]);
  const [overview, setOverview] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [agriChatOpen, setAgriChatOpen] = useState(false);
  const [isSelecting, setIsSelecting] = useState(false);
  const [manualMarker, setManualMarker] = useState(null);
  const [flyTarget, setFlyTarget] = useState(null);

  const loadAll = useCallback(async () => {
    try {
      const [riskRes, locRes, logRes, ovRes] = await Promise.all([
        fetch('/risk-map'),
        fetch('/locations'),
        fetch('/logs'),
        fetch('/overview'),
      ]);
      const [riskData, locData, logData, ovData] = await Promise.all([
        riskRes.json(),
        locRes.json(),
        logRes.json(),
        ovRes.json(),
      ]);
      setCircles(riskData.circles || []);
      setLocations(locData.locations || []);
      setLogs((logData.logs || []).reverse());
      setOverview(ovData);
    } catch (err) {
      console.error('Failed to load emergency data', err);
    }
  }, []);

  useEffect(() => {
    const initialLoad = setTimeout(() => {
      loadAll();
    }, 0);
    return () => clearTimeout(initialLoad);
  }, [loadAll]);

  const handleDeleteLocation = async (id) => {
    try {
      await fetch(`/locations/${id}`, { method: 'DELETE' });
      loadAll();
    } catch {
      // noop
    }
  };

  const handleLocationSelected = (lat, lng) => {
    setManualMarker({ lat, lng });
    setIsSelecting(false);
    if (!chatOpen) setChatOpen(true);
  };

  const handleFlyTo = (lat, lng) => setFlyTarget({ lat, lng, zoom: 15 });
  const handleFlyToCircle = (lat, lng) => setFlyTarget({ lat, lng, zoom: 13 });

  const globalRisk = overview?.globalRisk ?? 0;
  const riskLevel = overview?.globalRiskLevel?.level ?? 'safe';
  const riskColor = riskLevel === 'danger' ? '#ef4444' : riskLevel === 'warning' ? '#f59e0b' : '#10b981';

  return (
    <div className="h-[calc(100vh-64px)] overflow-hidden bg-gradient-to-br from-slate-50 via-white to-red-50">
      <div className="flex items-center justify-between border-b border-gray-200 bg-white/80 px-4 py-2 backdrop-blur">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-red-100 p-1.5 text-red-700">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Emergency Operations</p>
            <p className="text-xs text-gray-500">Live map, risk monitoring, and assisted response</p>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100%-53px)] min-h-0">
        <div className="w-[400px] shrink-0 border-r border-gray-200 bg-slate-950/95">
          <EmergencySidebar
            overview={overview}
            circles={circles}
            locations={locations}
            logs={logs}
            onSearch={loadAll}
            onDeleteLocation={handleDeleteLocation}
            onFlyTo={handleFlyTo}
            onFlyToCircle={handleFlyToCircle}
          />
        </div>

        <div className="min-w-0 flex-1">
          <EmergencyMap
            circles={circles}
            locations={locations}
            isSelecting={isSelecting}
            onLocationSelected={handleLocationSelected}
            manualMarker={manualMarker}
            onDeleteLocation={handleDeleteLocation}
            flyTarget={flyTarget}
            onFlyComplete={() => setFlyTarget(null)}
            globalRisk={globalRisk}
            riskColor={riskColor}
          />
        </div>
      </div>

      <EmergencyChat
        isOpen={chatOpen}
        onToggle={() => {
          setChatOpen((v) => !v);
          if (!chatOpen) setAgriChatOpen(false);
        }}
        manualMarker={manualMarker}
        isSelecting={isSelecting}
        onRequestMapSelect={() => {
          setIsSelecting(true);
          if (!chatOpen) setChatOpen(true);
          setAgriChatOpen(false);
        }}
      />

      <AgricultureChat
        isOpen={agriChatOpen}
        onToggle={() => {
          setAgriChatOpen((v) => !v);
          if (!agriChatOpen) setChatOpen(false);
        }}
        manualMarker={manualMarker}
        isSelecting={isSelecting}
        onRequestMapSelect={() => {
          setIsSelecting(true);
          if (!agriChatOpen) setAgriChatOpen(true);
          setChatOpen(false);
        }}
      />
    </div>
  );
};

export default Emergency;
