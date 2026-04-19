import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Leaf, MapPin, Send, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Badge, Button, Input } from '../ui';

const sessionId = `agri_${Math.random().toString(36).slice(2, 11)}`;

const QUICK_CROPS = ['Apples', 'Pomegranates', 'Dates', 'Olives'];

const AgricultureChat = ({ isOpen, onToggle, manualMarker, onRequestMapSelect }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const prevMarker = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (text, sender) => {
    setMessages((prev) => [...prev, { text, sender, id: Date.now() + Math.random() }]);
  };

  const sendToAssistant = useCallback(async (message, lat = null, lng = null) => {
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
      if (data.error) {
        addMessage('Error connecting to agriculture core.', 'ai');
        return;
      }
      addMessage(data.response, 'ai');
    } catch {
      addMessage('Failed to reach agriculture server.', 'ai');
    } finally {
      setLoading(false);
    }
  }, [manualMarker]);

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
    if (!isOpen && messages.length === 0) {
      sendToAssistant('hello');
    }
  };

  const sendFromInput = () => {
    if (input.trim()) sendToAssistant(input.trim());
  };

  return (
    <>
      <button
        onClick={handleToggle}
        className="fixed bottom-[88px] right-8 z-[2000] flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-md transition-transform hover:scale-105 hover:bg-emerald-500"
      >
        <Leaf className="h-6 w-6" />
      </button>

      {isOpen ? (
        <div className="fixed bottom-[150px] right-8 z-[2000] flex h-[520px] w-[360px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-md">
          <div className="flex items-center justify-between border-b border-gray-100 bg-emerald-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <Leaf className="h-4 w-4 text-emerald-700" />
              <div>
                <p className="text-sm font-semibold text-emerald-700">Agriculture Assistant</p>
                <p className="text-xs text-emerald-600">Crop and planting guidance</p>
              </div>
            </div>
            <button onClick={handleToggle} className="rounded p-1 text-gray-500 hover:bg-white hover:text-gray-700">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto bg-gray-50 p-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`max-w-[88%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'ml-auto bg-emerald-600 text-white'
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
              <Button size="sm" variant="secondary" onClick={onRequestMapSelect}>
                <MapPin className="h-3.5 w-3.5" />
                Select on map
              </Button>
              {QUICK_CROPS.map((crop) => (
                <Button key={crop} size="sm" variant="secondary" onClick={() => sendToAssistant(`I want to plant ${crop}`)}>
                  {crop}
                </Button>
              ))}
              <Badge variant="waste">AI agronomy</Badge>
            </div>

            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendFromInput()}
                placeholder="Ask about crop planning..."
              />
              <Button onClick={sendFromInput}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
};

export default AgricultureChat;
