import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Send } from 'lucide-react';
import { Button } from '../ui';

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
    <form onSubmit={handleSubmit}>
      <div className="relative flex gap-3 items-center rounded-xl border border-gray-200 bg-white p-2 shadow-sm">
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          disabled={disabled}
          className="flex-1 resize-none bg-transparent border-none px-2 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:ring-0 outline-none disabled:opacity-50"
        />
        <Button
          type="submit"
          disabled={!text.trim() || disabled}
          size="sm"
          className="h-10 min-w-10 px-3"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
};

export default ChatInput;
