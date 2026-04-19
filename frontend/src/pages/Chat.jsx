import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { AlertCircle, MessageSquareText, Sparkles } from 'lucide-react';
import MessageBubble from '../components/chat/MessageBubble';
import ChatInput from '../components/chat/ChatInput';
import TypingIndicator from '../components/chat/TypingIndicator';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { useChat } from '../hooks/useChat';

const SUGGESTIONS = ['My palms are yellow', 'Irrigation help', 'Pollution report'];

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
    <div className="relative h-[calc(100vh-64px)] overflow-hidden bg-gradient-to-br from-gray-50 via-white to-sky-50">
      <div className="mx-auto flex h-full max-w-5xl flex-col px-4 py-6 md:px-6">
        <Card className="mb-4 rounded-xl bg-white/95 backdrop-blur">
          <CardHeader className="flex-row items-center justify-between p-4">
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">{t('chat.title')}</CardTitle>
              <p className="mt-1 text-sm text-gray-600">Assistant for environment, agriculture, and public health.</p>
            </div>
            <Badge variant="neutral" className="text-xs">
              <MessageSquareText className="mr-1 h-3.5 w-3.5" />
              Live chat
            </Badge>
          </CardHeader>
        </Card>

        <div className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white/80 p-4 shadow-sm">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-5 rounded-xl bg-sky-100 p-4 text-sky-700">
                  <Sparkles className="h-8 w-8" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900">{t('chat.title')}</h2>
                <p className="mt-2 max-w-md text-sm text-gray-600">{t('chat.placeholder')}</p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <Button key={s} size="sm" variant="secondary" onClick={() => sendMessage(s)}>
                      {s}
                    </Button>
                  ))}
                </div>
              </div>
            ) : null}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {isLoading ? (
              <div className="flex justify-start">
                <TypingIndicator />
              </div>
            ) : null}

            {error ? (
              <div className="mx-auto max-w-sm rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <p className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </p>
              </div>
            ) : null}

            <div ref={scrollRef} className="h-2" />
          </div>
        </div>

        <div className="mt-4">
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default Chat;
