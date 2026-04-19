import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, MapPin, Navigation, Send, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Badge, Button, Input } from '../ui';

const sessionId = `emg_${Math.random().toString(36).slice(2, 11)}`;

const QUICK_ALERTS = ['Cannot breathe', 'Chest pain', 'Person unconscious', 'Asthma attack'];

const EmergencyChat = ({ isOpen, onToggle, manualMarker, onRequestMapSelect }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [emergencyScore, setEmergencyScore] = useState(0);
  const [isAlarm, setIsAlarm] = useState(false);
  const [inactivityProgress, setInactivityProgress] = useState(0);
  const timerRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const timerStartedAtRef = useRef(null);
  const chatEndRef = useRef(null);
  const prevMarker = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = useCallback((text, sender) => {
    setMessages((prev) => [...prev, { text, sender, id: Date.now() + Math.random() }]);
  }, []);

  const resetTimer = useCallback(() => {
    clearTimeout(timerRef.current);
    clearInterval(progressIntervalRef.current);
    timerStartedAtRef.current = Date.now();
    setInactivityProgress(0);
    setIsAlarm(false);

    progressIntervalRef.current = setInterval(() => {
      if (!timerStartedAtRef.current) return;
      const elapsed = Date.now() - timerStartedAtRef.current;
      const progress = Math.min(1, elapsed / 60000);
      setInactivityProgress(progress);
    }, 1000);

    timerRef.current = setTimeout(() => {
      if (isOpen) {
        setIsAlarm(true);
        setInactivityProgress(1);
        clearInterval(progressIntervalRef.current);
        addMessage('ALERT: No response detected for 1 minute. Automatic emergency call sequence started.', 'ai');
      }
    }, 60000);
  }, [addMessage, isOpen]);

  useEffect(() => () => {
    clearTimeout(timerRef.current);
    clearInterval(progressIntervalRef.current);
  }, []);

  const sendToAssistant = useCallback(async (message, lat = null, lng = null) => {
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
      if (data.error) {
        addMessage('Error connecting to assistant core.', 'ai');
        return;
      }
      addMessage(data.response, 'ai');
      if (data.emergency_score != null) setEmergencyScore(data.emergency_score);
    } catch {
      addMessage('Failed to reach emergency server.', 'ai');
    } finally {
      setLoading(false);
    }
  }, [addMessage, manualMarker, resetTimer]);

  useEffect(() => {
    if (
      manualMarker &&
      (prevMarker.current?.lat !== manualMarker.lat || prevMarker.current?.lng !== manualMarker.lng)
    ) {
      prevMarker.current = manualMarker;
      sendToAssistant('Location selected', manualMarker.lat, manualMarker.lng);
    }
  }, [manualMarker, sendToAssistant]);

  const handleToggle = () => {
    onToggle();
    if (!isOpen) {
      if (messages.length === 0) {
        sendToAssistant('');
      } else {
        resetTimer();
      }
    }
    if (isOpen) {
      clearTimeout(timerRef.current);
      clearInterval(progressIntervalRef.current);
      timerStartedAtRef.current = null;
      setInactivityProgress(0);
      setIsAlarm(false);
    }
  };

  const handleAutoLocate = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => sendToAssistant('Location selected', pos.coords.latitude, pos.coords.longitude),
        () => alert("Location access denied. Please click 'Select on map'.")
      );
    }
  };

  const sendFromInput = () => {
    if (input.trim()) sendToAssistant(input.trim());
  };

  const warningOpacity = Math.max(0, inactivityProgress - 0.15);
  const warningBorder = 0.15 + warningOpacity * 0.75;
  const shouldPulseChat = inactivityProgress > 0.5 && !isAlarm;

  return (
    <>
      <button
        onClick={handleToggle}
        className="fixed bottom-8 right-8 z-[2000] flex h-14 w-14 items-center justify-center rounded-full bg-red-600 text-white shadow-md transition-transform hover:scale-105 hover:bg-red-500"
      >
        <AlertTriangle className="h-6 w-6" />
      </button>

      {isOpen ? (
        <div
          className={`fixed bottom-28 right-8 z-[2000] flex h-[520px] w-[360px] flex-col overflow-hidden rounded-xl border bg-white shadow-md transition-all duration-500 ${
            shouldPulseChat ? 'animate-pulse' : ''
          }`}
          style={{
            borderColor: `rgba(239,68,68,${warningBorder})`,
            boxShadow: `0 12px 28px rgba(15,23,42,0.16), 0 0 0 2px rgba(239,68,68,${warningOpacity * 0.55})`,
            backgroundImage: `linear-gradient(180deg, rgba(254,242,242,${warningOpacity * 0.35}) 0%, rgba(255,255,255,1) 38%)`,
          }}
        >
          <div className="h-1 w-full bg-gray-100">
            <div
              className="h-full bg-gradient-to-r from-amber-400 via-red-500 to-red-700 transition-all duration-1000"
              style={{ width: `${Math.round(inactivityProgress * 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between border-b border-gray-100 bg-red-50 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-red-700">Emergency Assistant</p>
              <p className="text-xs text-red-600">Real-time triage guidance</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={emergencyScore >= 80 ? 'high' : emergencyScore >= 40 ? 'medium' : 'low'}>
                score {emergencyScore}
              </Badge>
              <button onClick={handleToggle} className="rounded p-1 text-gray-500 hover:bg-white hover:text-gray-700">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto bg-gray-50 p-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`max-w-[88%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'ml-auto bg-red-600 text-white'
                    : 'border border-gray-200 bg-white text-gray-700'
                }`}
              >
                {msg.sender === 'user' ? (
                  msg.text
                ) : (
                  <div className="prose prose-sm max-w-none text-gray-800 prose-p:my-1 prose-p:text-gray-800 prose-strong:text-gray-900 prose-li:text-gray-800 prose-ul:my-1 prose-ol:my-1">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                  </div>
                )}
              </div>
            ))}
            {loading ? <div className="text-xs text-gray-500">Assistant is analyzing...</div> : null}
            <div ref={chatEndRef} />
          </div>

          <div className="border-t border-gray-100 px-3 py-2">
            <div className="mb-2 flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={handleAutoLocate}>
                <Navigation className="h-3.5 w-3.5" />
                Use my location
              </Button>
              <Button size="sm" variant="secondary" onClick={onRequestMapSelect}>
                <MapPin className="h-3.5 w-3.5" />
                Select on map
              </Button>
              {QUICK_ALERTS.map((text) => (
                <Button key={text} size="sm" variant="secondary" onClick={() => sendToAssistant(text)}>
                  {text}
                </Button>
              ))}
            </div>

            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendFromInput()}
                placeholder="Describe symptoms..."
              />
              <Button onClick={sendFromInput}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {isAlarm ? (
        <div className="fixed inset-0 z-[3000] flex items-center justify-center bg-red-950/55 backdrop-blur-sm">
          <div className="animate-pulse rounded-2xl border border-red-300 bg-red-600 p-6 text-white shadow-2xl">
            <div className="mb-3 flex items-center gap-3">
              <AlertTriangle className="h-6 w-6" />
              <p className="text-lg font-semibold">Emergency Warning</p>
            </div>
            <p className="max-w-md text-sm leading-relaxed">
              ALERT: No response detected for 1 minute. Automatic emergency call sequence started.
            </p>
            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  setIsAlarm(false);
                  resetTimer();
                }}
                className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
};

export default EmergencyChat;
