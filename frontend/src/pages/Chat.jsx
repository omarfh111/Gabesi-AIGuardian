import React, { useState } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Chat = () => {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      text: 'Bonjour. Je suis Gabesi, votre analyste environnemental. J\'ai intégré les dernières données (Pollution, Météo Marine, Pêche, Tourisme). Que souhaitez-vous savoir aujourd\'hui ?' 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e, customOveride=null) => {
    e?.preventDefault();
    const finalInput = customOveride || input.trim();
    if (!finalInput) return;

    // Build History (Don't include charts/sources in what we send to the backend, just text)
    const historyPayload = messages.map(m => ({ role: m.role, content: m.text }));
    historyPayload.push({ role: 'user', content: finalInput });

    setMessages(prev => [...prev, { role: 'user', text: finalInput }]);
    if(!customOveride) setInput('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:3000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: historyPayload, message: finalInput })
      });
      
      const data = await res.json();
      
      if (data.error) throw new Error(data.error);

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: data.response || "Aucune réponse générée.",
        source_id: data.analysis_id,
        sources: data.sources,
        chart_title: data.chart_title,
        chart_data: data.chart_data
      }]);
    } catch (err) {
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: "Impossible de contacter le backend. Le serveur sur le port 3000 est-il allumé ?" 
        }]);
      }, 1000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 4rem)' }}>
      <div className="header-container" style={{ marginBottom: '1rem' }}>
        <div>
          <h1 className="title-gradient">Dialogue Agentique (Expert)</h1>
          <p className="subtitle">Posez des questions directes sur les données. Je mémorise notre conversation.</p>
        </div>
      </div>

      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        
        {/* Chat History */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {messages.map((msg, i) => (
            <div key={i} style={{ 
              display: 'flex', 
              gap: '1rem', 
              alignItems: 'flex-start',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
            }}>
              <div style={{ 
                background: msg.role === 'user' ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                padding: '0.75rem',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                {msg.role === 'user' ? <User size={20} color="var(--accent-cyan)" /> : <Bot size={20} color="var(--text-primary)" />}
              </div>
              
              <div style={{
                background: msg.role === 'user' ? 'var(--bg-tertiary)' : 'rgba(255,255,255,0.03)',
                padding: '1rem 1.25rem',
                borderRadius: '16px',
                borderTopRightRadius: msg.role === 'user' ? 0 : '16px',
                borderTopLeftRadius: msg.role === 'assistant' ? 0 : '16px',
                maxWidth: msg.chart_data && msg.chart_data.length > 0 ? '90%' : '75%',
                border: '1px solid var(--glass-border)',
                lineHeight: '1.6'
              }}>
                <div style={{ color: msg.role === 'user' ? '#fff' : 'var(--text-primary)', whiteSpace: 'pre-wrap', fontSize: '0.95rem' }}>
                   {msg.role === 'assistant' ? (
                       <div className="markdown-container">
                         <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                       </div>
                   ) : (
                       msg.text
                   )}
                </div>
                
                {/* Optional Chart Injection */}
                {msg.chart_data && msg.chart_data.length > 0 && (
                  <div style={{ marginTop: '1.5rem', height: '200px', width: '100%', background: 'rgba(0,0,0,0.2)', padding:'1rem', borderRadius: '12px' }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textAlign: 'center', fontWeight: 'bold' }}>{msg.chart_title || '📉 Évolution'}</p>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={msg.chart_data}>
                        <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                        <YAxis stroke="var(--text-muted)" fontSize={12} width={40} />
                        <Tooltip contentStyle={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--glass-border)', borderRadius: '8px' }} />
                        <Area type="monotone" dataKey="value" stroke="var(--accent-cyan)" fill="rgba(0, 240, 255, 0.2)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Sources Display */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ marginTop: '1rem', borderTop: '1px solid var(--glass-border)', paddingTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontWeight: '600', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertCircle size={12}/> Sources :</span>
                    {msg.sources.map((s, idx) => <span key={idx}>- {s}</span>)}
                  </div>
                )}
                
                {msg.source_id && (
                   <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', opacity: 0.5 }}>
                     <Sparkles size={12} color="var(--text-muted)"/>
                     ID: {msg.source_id}
                   </div>
                 )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem', borderRadius: '50%' }}>
                <Bot size={20} color="var(--text-primary)" />
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span className="status-dot"></span>
                <span className="status-dot delay-1"></span>
                <span className="status-dot delay-2"></span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ padding: '1.5rem', borderTop: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)' }}>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '1rem' }}>
            <input 
              type="text" 
              className="glass-input" 
              placeholder="ex: Quelles usines polluent exactement et quelles sont les valeurs rejetées ?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button type="submit" className="glass-button" disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Send size={18} />
              Envoyer
            </button>
          </form>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button className="glass-button" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={(e) => { e.preventDefault(); handleSend(e, "Affiche moi l'évolution historique de la pêche en courbes et explique les baisses."); }}>💡 Courbes de Pêche</button>
            <button className="glass-button" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={(e) => { e.preventDefault(); handleSend(e, "Les détails pour chaque usine ?"); }}>💡 Détail Usines</button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Chat;
