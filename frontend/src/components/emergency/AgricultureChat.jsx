import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Navigation, Leaf } from 'lucide-react';

const sessionId = 'agri_' + Math.random().toString(36).substr(2, 9);

const AgricultureChat = ({ isOpen, onToggle, manualMarker, isSelecting, onRequestMapSelect }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
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

  const addMessage = (text, sender) => {
    setMessages(prev => [...prev, { text, sender, id: Date.now() + Math.random() }]);
  };

  const sendToAssistant = async (message, lat = null, lng = null) => {
    if (message && message !== 'Location selected') addMessage(message, 'user');
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/agriculture/chat', {
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
      if (data.error) { addMessage('Error connecting to agriculture core.', 'ai'); return; }
      addMessage(data.response, 'ai');
    } catch {
      addMessage('Failed to reach agriculture server.', 'ai');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    onToggle();
    if (!isOpen && messages.length === 0) {
      sendToAssistant('hello');
    }
  };

  const handleAutoLocate = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => sendToAssistant('Location selected', pos.coords.latitude, pos.coords.longitude),
        () => alert("Location access denied. Please click '📍 Select on Map'.")
      );
    }
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={handleToggle}
        className="fixed bottom-[88px] right-8 w-14 h-14 rounded-full flex items-center justify-center text-white z-[2000] transition-transform hover:scale-110"
        style={{
          background: 'linear-gradient(135deg,#10b981,#34d399)',
          boxShadow: '0 0 15px rgba(16,185,129,.5)',
        }}
      >
        <Leaf size={24} />
      </button>

      {/* Widget */}
      {isOpen && (
        <div
          className="fixed bottom-[150px] right-8 w-[360px] h-[520px] z-[2000] flex flex-col overflow-hidden rounded-2xl"
          style={{
            background: 'rgba(12,16,32,.92)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(16,185,129,.4)',
            boxShadow: '0 10px 40px rgba(0,0,0,.6)',
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-emerald-500/30"
            style={{ background: 'rgba(16,185,129,.15)' }}>
            <div className="flex items-center gap-2">
              <Leaf size={14} className="text-emerald-400" />
              <div className="text-[13px] font-black text-emerald-400 tracking-wide uppercase">
                GABES AI AGRICULTURE SYSTEM
              </div>
            </div>
            <button onClick={handleToggle} className="text-gray-500 hover:text-gray-300 text-lg">✕</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3"
            style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(16,185,129,.3) transparent' }}>
            {messages.map(msg => (
              <div
                key={msg.id}
                className="max-w-[85%] px-3 py-2.5 rounded-[14px] text-xs leading-relaxed whitespace-pre-wrap"
                style={msg.sender === 'user'
                  ? { background: 'linear-gradient(135deg,#ef4444,#f43f5e)', color: 'white', alignSelf: 'flex-end', borderBottomRightRadius: 4 }
                  : { background: 'rgba(255,255,255,.05)', border: '1px solid #1e2548', color: '#eef0f8', alignSelf: 'flex-start', borderBottomLeftRadius: 4 }}
                dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
              />
            ))}
            {loading && <div className="text-[10px] text-gray-500 ml-1">Assistant is analyzing...</div>}
            <div ref={chatEndRef} />
          </div>

          {/* Quick replies */}
          <div className="px-4 py-2 border-t border-[#1e2548] flex flex-wrap gap-2">
            <button onClick={onRequestMapSelect}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-blue-400 transition-all hover:bg-blue-500 hover:text-white"
              style={{ background: 'rgba(59,130,246,.15)', border: '1px solid rgba(59,130,246,.4)' }}>
              <MapPin className="w-3 h-3" /> Select on Map
            </button>
            {['Apples', 'Pomegranates', 'Dates', 'Olives'].map(t => (
              <button key={t} onClick={() => sendToAssistant(`I want to plant ${t}`)}
                className="px-3 py-1 rounded-full text-[11px] text-gray-300 transition-all hover:bg-emerald-500 hover:text-white"
                style={{ background: 'rgba(255,255,255,.08)', border: '1px solid #1e2548' }}>
                {t}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-[#1e2548] flex gap-2"
            style={{ background: 'rgba(0,0,0,.2)' }}>
            <input
              className="flex-1 bg-[#111630] border border-[#1e2548] rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-emerald-500"
              placeholder="Type crop name..."
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
    </>
  );
};

export default AgricultureChat;
