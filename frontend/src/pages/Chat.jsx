import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useChat } from '../hooks/useChat';
import MessageBubble from '../components/chat/MessageBubble';
import ChatInput from '../components/chat/ChatInput';
import TypingIndicator from '../components/chat/TypingIndicator';
import { Leaf, AlertCircle, Sparkles, MessageSquare } from 'lucide-react';

const Chat = () => {
  const { t } = useTranslation();
  const { messages, isLoading, error, sendMessage } = useChat();
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-primary relative">
      {/* Background Decorative Elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8 md:px-0">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in slide-in-from-bottom-4 duration-1000">
              <div className="w-20 h-20 glass-card flex items-center justify-center text-accent mb-6 shadow-accent/10">
                <Sparkles className="w-10 h-10" />
              </div>
              <h2 className="text-3xl font-black text-text-primary tracking-tighter uppercase mb-2">
                {t('chat.title')}
              </h2>
              <p className="text-text-secondary font-medium max-w-sm mx-auto mb-8">
                {t('chat.placeholder')}
              </p>
              
              <div className="flex flex-wrap gap-2 justify-center">
                {['My palms are yellow', 'Irrigation help', 'Pollution report'].map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="px-4 py-2 glass-card hover:bg-accent/10 hover:border-accent text-xs font-bold text-text-secondary hover:text-accent transition-all cursor-pointer"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>

          {isLoading && (
            <div className="flex justify-start">
              <div className="glass px-4 py-3 rounded-2xl rounded-tl-none">
                <TypingIndicator />
              </div>
            </div>
          )}

          {error && (
            <div className="mx-auto max-w-sm glass border-danger/30 text-danger px-4 py-3 rounded-xl text-xs font-black uppercase tracking-wider flex items-center gap-3 animate-bounce">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}
          
          <div ref={scrollRef} className="h-4" />
        </div>
      </div>

      {/* Footer Area */}
      <div className="p-4 md:pb-8 relative z-10">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={sendMessage} disabled={isLoading} />
          <p className="text-[10px] text-center text-text-muted font-bold uppercase tracking-widest mt-4">
            Gabès AI Assistant · Experimental Intelligence · 2026
          </p>
        </div>
      </div>
    </div>
  );
};

export default Chat;
