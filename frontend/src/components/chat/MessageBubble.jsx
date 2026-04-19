import React from 'react';
import { Bot } from 'lucide-react';
import DiagnosisCard from './DiagnosisCard';
import IrrigationCard from './IrrigationCard';
import PollutionQACard from './PollutionQACard';
import PollutionReportCard from './PollutionReportCard';

const MessageBubble = ({ message }) => {
  const isAI = message.role === 'ai';

  const renderContent = () => {
    if (!isAI) {
      return <div className="text-sm font-medium leading-relaxed">{message.content}</div>;
    }

    const { intent, response } = message;

    switch (intent) {
      case 'diagnosis':
        return <DiagnosisCard data={response} />;
      case 'irrigation':
        return <IrrigationCard data={response} />;
      case 'pollution_qa':
        return <PollutionQACard data={response} />;
      case 'pollution_report':
        return <PollutionReportCard data={response} />;
      case 'unknown':
        return (
          <div className="flex items-start gap-3">
            <span className="rounded-lg bg-gray-100 p-2 text-gray-700">
              <Bot className="h-4 w-4" />
            </span>
            <div className="text-sm leading-relaxed text-gray-700">{response.message || response}</div>
          </div>
        );
      default:
        return (
          <div className="text-sm leading-relaxed text-gray-700">
            {message.content || response.message || (typeof response === 'string' ? response : JSON.stringify(response))}
          </div>
        );
    }
  };

  return (
    <div className={`flex w-full ${isAI ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm transition-all duration-200 md:max-w-[70%] ${
          isAI
            ? 'rounded-bl-none border border-gray-200 bg-white text-gray-800'
            : 'rounded-br-none bg-sky-600 text-white'
        }`}
      >
        {renderContent()}
      </div>
    </div>
  );
};

export default MessageBubble;
