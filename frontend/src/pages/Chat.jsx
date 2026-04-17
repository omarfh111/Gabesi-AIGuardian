import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useChat } from '../hooks/useChat';
import MessageBubble from '../components/chat/MessageBubble';
import ChatInput from '../components/chat/ChatInput';
import TypingIndicator from '../components/chat/TypingIndicator';
import { Leaf, AlertCircle } from 'lucide-react';

const Chat = () => {
  const { t } = useTranslation();
  const { messages, isLoading, error, sendMessage } = useChat();
  const scrollRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-gray-50">
      {/* Scrollable area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 max-w-sm mx-auto opacity-60">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary">
              <Leaf className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">{t('chat.title')}</h2>
              <p className="text-sm mt-1">{t('chat.placeholder')}</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {['My palms are yellow', 'Irrigation help', 'Pollution report'].map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="px-3 py-1 bg-white border rounded-full text-xs hover:border-primary transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <TypingIndicator />
          </div>
        )}

        {error && (
          <div className="mx-auto max-w-sm bg-red-50 text-red-600 px-4 py-2 rounded-lg text-xs font-bold border border-red-100 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input area */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};

export default Chat;
