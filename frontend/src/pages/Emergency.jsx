import React, { useState, useEffect, useCallback, useRef } from 'react';
import EmergencyMap from '../components/emergency/EmergencyMap';
import EmergencyChat from '../components/emergency/EmergencyChat';
import AgricultureChat from '../components/emergency/AgricultureChat';
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

  // Map ref so sidebar can call flyTo
  const mapRef = useRef(null);

  const loadAll = useCallback(async () => {
    try {
      const [riskRes, locRes, logRes, ovRes] = await Promise.all([
        fetch('/risk-map'),
        fetch('/locations'),
        fetch('/logs'),
        fetch('/overview'),
      ]);
      const [riskData, locData, logData, ovData] = await Promise.all([
        riskRes.json(), locRes.json(), logRes.json(), ovRes.json(),
      ]);
      setCircles(riskData.circles || []);
      setLocations(locData.locations || []);
      setLogs((logData.logs || []).reverse());
      setOverview(ovData);
    } catch (err) {
      console.error('Failed to load emergency data', err);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleDeleteLocation = async (id) => {
    try {
      await fetch(`/locations/${id}`, { method: 'DELETE' });
      loadAll();
    } catch { /* ignore */ }
  };

  const handleLocationSelected = (lat, lng) => {
    setManualMarker({ lat, lng });
    setIsSelecting(false);
    if (!chatOpen) setChatOpen(true);
  };

  // flyTo: we use a simple event approach since the map is in a child component
  const [flyTarget, setFlyTarget] = useState(null);
  const handleFlyTo = (lat, lng) => setFlyTarget({ lat, lng, zoom: 15 });
  const handleFlyToCircle = (lat, lng) => setFlyTarget({ lat, lng, zoom: 13 });

  const globalRisk = overview?.globalRisk ?? 0;
  const riskLevel = overview?.globalRiskLevel?.level ?? 'safe';
  const riskColor = riskLevel === 'danger' ? '#ef4444' : riskLevel === 'warning' ? '#f59e0b' : '#10b981';

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-[#06080f] text-white overflow-hidden">
      {/* Main 2-column layout */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar (400px) */}
        <div className="w-[400px] flex-shrink-0">
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

        {/* Map */}
        <div className="flex-1 relative min-w-0">
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

      {/* Floating Emergency Chat */}
      <EmergencyChat
        isOpen={chatOpen}
        onToggle={() => {
          setChatOpen(v => !v);
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

      {/* Floating Agriculture Chat */}
      <AgricultureChat
        isOpen={agriChatOpen}
        onToggle={() => {
          setAgriChatOpen(v => !v);
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
