import React, { useEffect, useRef, useState } from 'react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AlertCircle, Bot, Send, Sparkles, TrendingUp, User } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui';

const QUICK_PROMPTS = [
  'Show me the historic fishing evolution and explain the decline.',
  'Detailed factory audit values (mg/Nm3)?',
  'What are the 2030 industrial projects for Gabes?',
];

const markdownComponents = {
  table: ({ children }) => <table className="w-full table-fixed border-collapse" style={{ color: '#111827' }}>{children}</table>,
  thead: ({ children }) => <thead className="border-b border-gray-300" style={{ color: '#0369a1' }}>{children}</thead>,
  tr: ({ children }) => <tr className="border-b border-gray-100" style={{ color: '#111827' }}>{children}</tr>,
  th: ({ children }) => (
    <th className="px-4 py-2 text-left text-sm font-semibold uppercase tracking-wide" style={{ color: '#0369a1' }}>
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2 text-base font-medium" style={{ color: '#111827', opacity: 1 }}>
      {children}
    </td>
  ),
};

const StrategicChat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Greetings. I am **Gabesi**, your strategic environmental analyst. I have synchronized the latest industrial audits, marine weather, and fishery data. How can I assist your mission today?',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e, customOverride = null) => {
    e?.preventDefault();
    const finalInput = customOverride || input.trim();
    if (!finalInput) return;

    const historyPayload = messages.map((m) => ({ role: m.role, content: m.text }));
    historyPayload.push({ role: 'user', content: finalInput });

    setMessages((prev) => [...prev, { role: 'user', text: finalInput }]);
    if (!customOverride) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/strategic/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: historyPayload, message: finalInput }),
      });

      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.response || 'No response generated.',
          source_id: data.analysis_id,
          sources: data.sources,
          chart_title: data.chart_title,
          chart_data: data.chart_data,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'System communication failure. Please verify backend status.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-gradient-to-br from-slate-50 via-white to-sky-50">
      <Card className="m-4 mb-3 rounded-xl">
        <CardHeader className="p-5">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Sparkles className="h-5 w-5 text-sky-600" />
            Strategic Agentic Chat
          </CardTitle>
          <p className="text-sm text-gray-600">Real-time interaction with the Gabesi expert system</p>
        </CardHeader>
      </Card>

      <div ref={scrollRef} className="mx-4 min-h-0 flex-1 space-y-4 overflow-y-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`mt-1 flex h-8 w-8 items-center justify-center rounded-lg ${msg.role === 'user' ? 'bg-sky-100 text-sky-700' : 'bg-gray-100 text-gray-700'}`}>
              {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div className={`max-w-[86%] rounded-xl border px-4 py-3 text-sm ${msg.role === 'user' ? 'border-sky-200 bg-sky-50 text-gray-800' : 'border-gray-200 bg-white text-gray-700'}`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-li:text-gray-700 prose-table:w-full prose-table:table-fixed prose-thead:border-b prose-thead:border-gray-300 prose-th:text-left prose-th:text-sky-600 prose-th:font-semibold prose-th:uppercase prose-td:text-gray-900 prose-td:font-medium prose-tr:border-b prose-tr:border-gray-100">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {msg.text}
                  </ReactMarkdown>
                </div>
              ) : (
                msg.text
              )}

              {msg.chart_data && msg.chart_data.length > 0 ? (
                <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                    <TrendingUp className="h-3.5 w-3.5" />
                    {msg.chart_title || 'Trend analysis'}
                  </p>
                  <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={msg.chart_data}>
                        <defs>
                          <linearGradient id="strategicChartFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#0284c7" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="name" stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} />
                        <YAxis stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} width={34} />
                        <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e5e7eb', backgroundColor: '#fff' }} />
                        <Area type="monotone" dataKey="value" stroke="#0284c7" strokeWidth={2} fill="url(#strategicChartFill)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : null}

              {msg.sources && msg.sources.length > 0 ? (
                <div className="mt-3 border-t border-gray-100 pt-3">
                  <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Authenticated sources
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((s, idx) => (
                      <Badge key={idx} variant="neutral">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        ))}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Bot className="h-4 w-4" />
            Assistant is analyzing...
          </div>
        ) : null}
      </div>

      <Card className="m-4 mt-3 rounded-xl">
        <CardContent className="space-y-3 p-4">
          <form onSubmit={handleSend} className="flex gap-2">
            <Input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="Ask about pollution audits, fishing projections, or tourism..."
            />
            <Button type="submit" disabled={loading}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <Button key={prompt} size="sm" variant="secondary" onClick={(e) => handleSend(e, prompt)} disabled={loading}>
                {prompt}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StrategicChat;
