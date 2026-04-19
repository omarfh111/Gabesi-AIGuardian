import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const StrategicChat = () => {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      text: 'Greetings. I am **Gabesi**, your strategic environmental analyst. I have synchronized the latest industrial audits, marine weather, and fishery data. How can I assist your mission today?' 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e, customOveride=null) => {
    e?.preventDefault();
    const finalInput = customOveride || input.trim();
    if (!finalInput) return;

    const historyPayload = messages.map(m => ({ role: m.role, content: m.text }));
    historyPayload.push({ role: 'user', content: finalInput });

    setMessages(prev => [...prev, { role: 'user', text: finalInput }]);
    if(!customOveride) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/strategic/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: historyPayload, message: finalInput })
      });
      
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: data.response || "No response generated.",
        source_id: data.analysis_id,
        sources: data.sources,
        chart_title: data.chart_title,
        chart_data: data.chart_data
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: "System communication failure. Please verify backend status." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] animate-in fade-in duration-500">
      <div className="p-6 border-b border-border bg-secondary/30 backdrop-blur-md">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Sparkles className="text-accent" size={24} />
          Strategic Agentic Chat
        </h1>
        <p className="text-text-secondary text-sm">Real-time interaction with the Gabesi Expert System</p>
      </div>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 bg-primary/20"
      >
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ${
              msg.role === 'user' ? 'bg-accent/20 border border-accent/40' : 'bg-secondary border border-border'
            }`}>
              {msg.role === 'user' ? <User size={20} className="text-accent" /> : <Bot size={20} className="text-white" />}
            </div>
            
            <div className={`max-w-[85%] rounded-2xl p-4 border transition-all ${
              msg.role === 'user' 
                ? 'bg-secondary/50 border-accent/20 rounded-tr-none' 
                : 'glass-card border-border/50 rounded-tl-none'
            }`}>
              <div className="text-sm text-text-primary leading-relaxed">
                 {msg.role === 'assistant' ? (
                     <div className="prose prose-invert prose-sm max-w-none">
                       <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                     </div>
                 ) : (
                     msg.text
                 )}
              </div>
              
              {/* Chart Integration */}
              {msg.chart_data && msg.chart_data.length > 0 && (
                <div className="mt-6 p-4 bg-black/40 rounded-xl border border-white/5 h-64 shadow-inner">
                  <p className="text-[10px] uppercase tracking-widest text-text-muted mb-4 font-bold flex items-center gap-2">
                    <TrendingUp size={12}/> {msg.chart_title || 'Trend Analysis'}
                  </p>
                  <ResponsiveContainer width="100%" height="90%">
                    <AreaChart data={msg.chart_data}>
                      <defs>
                        <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="name" stroke="#4d567a" fontSize={10} axisLine={false} tickLine={false} />
                      <YAxis stroke="#4d567a" fontSize={10} axisLine={false} tickLine={false} width={30} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#111630', border: '1px solid #1e2548', borderRadius: '8px', fontSize: '12px' }}
                        itemStyle={{ color: '#06b6d4' }}
                      />
                      <Area type="monotone" dataKey="value" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#colorVal)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50 space-y-2">
                  <p className="text-[10px] font-bold text-accent uppercase tracking-wider flex items-center gap-1">
                    <AlertCircle size={10}/> Authenticated Sources
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((s, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-1 bg-white/5 rounded text-text-muted border border-white/5 italic">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex gap-4 items-center animate-pulse">
            <div className="w-10 h-10 rounded-full bg-secondary border border-border flex items-center justify-center">
              <Bot size={20} className="text-text-muted" />
            </div>
            <div className="flex gap-2">
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
            </div>
          </div>
        )}
      </div>

      <div className="p-6 bg-secondary/50 border-t border-border backdrop-blur-lg">
        <form onSubmit={handleSend} className="flex gap-4 max-w-5xl mx-auto">
          <input 
            type="text" 
            className="flex-1 bg-primary/50 border border-border rounded-xl px-4 py-3 text-white placeholder:text-text-muted focus:outline-none focus:border-accent transition-all shadow-inner" 
            placeholder="Ask Gabesi about pollution audits, fishing projections, or tourism..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button 
            type="submit" 
            className="bg-accent hover:bg-white text-primary px-6 rounded-xl font-bold flex items-center gap-2 transition-all disabled:opacity-50 shadow-lg shadow-accent/20"
            disabled={loading}
          >
            <Send size={18} />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
        <div className="flex gap-2 mt-4 max-w-5xl mx-auto overflow-x-auto pb-2 scrollbar-none">
          <button 
            className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-[10px] text-text-secondary whitespace-nowrap transition-all"
            onClick={(e) => handleSend(e, "Show me the historic fishing evolution and explain the decline.")}
          >
            📊 Fishing Trend Curves
          </button>
          <button 
            className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-[10px] text-text-secondary whitespace-nowrap transition-all"
            onClick={(e) => handleSend(e, "Detailed factory audit values (mg/Nm3)?")}
          >
            🏭 Factory Audit Values
          </button>
          <button 
            className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-[10px] text-text-secondary whitespace-nowrap transition-all"
            onClick={(e) => handleSend(e, "What are the 2030 industrial projects for Gabès?")}
          >
            🚀 2030 Projects
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategicChat;
