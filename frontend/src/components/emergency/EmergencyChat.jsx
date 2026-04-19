import React, { useState, useEffect, useRef } from 'react';
import { Phone, MapPin, Navigation } from 'lucide-react';

const sessionId = 'emg_' + Math.random().toString(36).substr(2, 9);

const EmergencyChat = ({ isOpen, onToggle, manualMarker, isSelecting, onRequestMapSelect }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [emergencyScore, setEmergencyScore] = useState(0);
  const [isAlarm, setIsAlarm] = useState(false);
  const timerRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // When a manual marker is set from the map, auto-send the location
  const prevMarker = useRef(null);
  useEffect(() => {
    if (
      manualMarker &&
      (prevMarker.current?.lat !== manualMarker.lat || prevMarker.current?.lng !== manualMarker.lng)
    ) {
      prevMarker.current = manualMarker;
      sendToAssistant('Location selected', manualMarker.lat, manualMarker.lng);
    }
  }, [manualMarker]);

  const resetTimer = () => {
    clearTimeout(timerRef.current);
    setIsAlarm(false);
    timerRef.current = setTimeout(() => {
      if (isOpen) {
        setIsAlarm(true);
        addMessage("🚨 ALERTE : Aucune réponse détectée depuis 1 minute. Appel d'urgence automatique au 190 en cours...", 'ai');
      }
    }, 60000);
  };

  const addMessage = (text, sender) => {
    setMessages(prev => [...prev, { text, sender, id: Date.now() + Math.random() }]);
  };

  const sendToAssistant = async (message, lat = null, lng = null) => {
    resetTimer();
    if (message && message !== 'Location selected') addMessage(message, 'user');
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message,
          lat: lat ?? manualMarker?.lat ?? null,
          lng: lng ?? manualMarker?.lng ?? null,
        }),
      });
      const data = await res.json();
      if (data.error) { addMessage('Error connecting to assistant core.', 'ai'); return; }
      addMessage(data.response, 'ai');
      if (data.emergency_score != null) setEmergencyScore(data.emergency_score);
    } catch {
      addMessage('Failed to reach emergency server.', 'ai');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    onToggle();
    if (!isOpen && messages.length === 0) {
      sendToAssistant('');
      resetTimer();
    }
    if (isOpen) { clearTimeout(timerRef.current); setIsAlarm(false); }
  };

  const handleAutoLocate = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => sendToAssistant('Location selected', pos.coords.latitude, pos.coords.longitude),
        () => alert("Location access denied. Please click '📍 Select on Map'.")
      );
    }
  };

  const ringGlow = emergencyScore >= 80
    ? '0 0 35px #ef4444'
    : emergencyScore >= 40 ? '0 0 15px #f59e0b' : '0 0 15px rgba(239,68,68,.5)';

  return (
    <>
      {/* Floating button */}
      <button
        onClick={handleToggle}
        className="fixed bottom-8 right-8 w-14 h-14 rounded-full flex items-center justify-center text-2xl text-white z-[2000] transition-transform hover:scale-110"
        style={{
          background: 'linear-gradient(135deg,#ef4444,#f43f5e)',
          boxShadow: isAlarm ? '0 0 60px #ff0000' : ringGlow,
          animation: isAlarm ? 'alarmFlash 1s infinite' : undefined,
        }}
      >
        🚨
      </button>

      {/* Widget */}
      {isOpen && (
        <div
          className="fixed bottom-28 right-8 w-[360px] h-[520px] z-[2000] flex flex-col overflow-hidden rounded-2xl"
          style={{
            background: 'rgba(12,16,32,.92)',
            backdropFilter: 'blur(20px)',
            border: isAlarm ? '1px solid #ef4444' : '1px solid rgba(239,68,68,.4)',
            boxShadow: '0 10px 40px rgba(0,0,0,.6)',
            animation: isAlarm ? 'alarmFlash 1s infinite' : undefined,
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-red-500/30"
            style={{ background: 'rgba(239,68,68,.15)' }}>
            <div className="text-[13px] font-black text-red-400 tracking-wide uppercase">
              🚨 AI Emergency Decision System
            </div>
            <button onClick={handleToggle} className="text-gray-500 hover:text-gray-300 text-lg">✕</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3"
            style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(239,68,68,.3) transparent' }}>
            {messages.map(msg => (
              <div
                key={msg.id}
                className="max-w-[85%] px-3 py-2.5 rounded-[14px] text-xs leading-relaxed whitespace-pre-wrap"
                style={msg.sender === 'user'
                  ? { background: 'linear-gradient(135deg,#ef4444,#f43f5e)', color: 'white', alignSelf: 'flex-end', borderBottomRightRadius: 4 }
                  : { background: 'rgba(255,255,255,.05)', border: '1px solid #1e2548', color: '#eef0f8', alignSelf: 'flex-start', borderBottomLeftRadius: 4 }}
                dangerouslySetInnerHTML={{ __html: msg.text.replace(/(Step \d+:)/g, '<strong>$1</strong>') }}
              />
            ))}
            {loading && <div className="text-[10px] text-gray-500 ml-1">Assistant is analyzing...</div>}
            <div ref={chatEndRef} />
          </div>

          {/* Quick replies */}
          <div className="px-4 py-2 border-t border-[#1e2548] flex flex-wrap gap-2">
            <button onClick={handleAutoLocate}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-blue-400 transition-all hover:bg-blue-500 hover:text-white"
              style={{ background: 'rgba(59,130,246,.15)', border: '1px solid rgba(59,130,246,.4)' }}>
              <Navigation className="w-3 h-3" /> Use my location
            </button>
            <button onClick={onRequestMapSelect}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-blue-400 transition-all hover:bg-blue-500 hover:text-white"
              style={{ background: 'rgba(59,130,246,.15)', border: '1px solid rgba(59,130,246,.4)' }}>
              <MapPin className="w-3 h-3" /> Select on Map
            </button>
            {['Cannot breathe', 'Chest pain', 'Person unconscious', 'Asthma attack'].map(t => (
              <button key={t} onClick={() => sendToAssistant(t)}
                className="px-3 py-1 rounded-full text-[11px] text-gray-300 transition-all hover:bg-red-500 hover:text-white"
                style={{ background: 'rgba(255,255,255,.08)', border: '1px solid #1e2548' }}>
                {t}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-[#1e2548] flex gap-2"
            style={{ background: 'rgba(0,0,0,.2)' }}>
            <input
              className="flex-1 bg-[#111630] border border-[#1e2548] rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-red-500"
              placeholder="Type symptom..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && input.trim() && sendToAssistant(input.trim())}
            />
            <button
              onClick={() => input.trim() && sendToAssistant(input.trim())}
              className="bg-red-500 hover:bg-red-600 text-white px-3 rounded-lg text-xs font-bold transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes alarmFlash {
          0%   { border-color:#ef4444; box-shadow:0 0 30px rgba(239,68,68,.6); background:rgba(40,0,0,.9); }
          50%  { border-color:#ff0000; box-shadow:0 0 60px rgba(255,0,0,1);   background:rgba(80,0,0,.9); }
          100% { border-color:#ef4444; box-shadow:0 0 30px rgba(239,68,68,.6); background:rgba(40,0,0,.9); }
        }
      `}</style>
    </>
  );
};

export default EmergencyChat;
