import React from 'react';
import { motion } from 'framer-motion';
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
            <span className="text-lg bg-accent/20 p-2 rounded-lg">🤖</span>
            <div className="text-sm leading-relaxed">{response.message || response}</div>
          </div>
        );
      default:
        return (
          <div className="text-sm leading-relaxed">
            {message.content || response.message || (typeof response === 'string' ? response : JSON.stringify(response))}
          </div>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex w-full ${isAI ? 'justify-start' : 'justify-end'}`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] px-4 py-3 shadow-2xl ${
          isAI
            ? 'glass-card text-text-primary rounded-bl-none'
            : 'bg-accent text-primary font-bold rounded-2xl rounded-br-none shadow-accent/20'
        }`}
      >
        {renderContent()}
      </div>
    </motion.div>
  );
};

export default MessageBubble;
