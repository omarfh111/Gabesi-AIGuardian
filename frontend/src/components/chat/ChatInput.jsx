import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, Zap } from 'lucide-react';

const ChatInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const { t } = useTranslation();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative group">
      <div className="absolute -inset-1 bg-gradient-to-r from-accent to-purple rounded-2xl blur opacity-10 group-focus-within:opacity-25 transition duration-500"></div>
      <div className="relative flex gap-3 items-center glass-card p-2">
        <div className="hidden sm:flex items-center justify-center w-10 h-10 rounded-xl bg-accent/10 text-accent">
          <Zap className="w-5 h-5" />
        </div>
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          disabled={disabled}
          className="flex-1 resize-none bg-transparent border-none py-3 px-2 text-sm text-text-primary placeholder:text-text-muted focus:ring-0 outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!text.trim() || disabled}
          className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent text-primary hover:bg-accent/90 transition-all disabled:opacity-30 disabled:grayscale cursor-pointer shadow-lg shadow-accent/20"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
