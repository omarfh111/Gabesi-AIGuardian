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
      return <div>{message.content}</div>;
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
          <div className="flex items-start gap-2">
            <span className="text-xl">ℹ️</span>
            <div>{response.message || response}</div>
          </div>
        );
      default:
        // Default text content for unknown intent or basic strings
        return <div>{message.content || response.message || JSON.stringify(response)}</div>;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex w-full mb-4 ${isAI ? 'justify-start' : 'justify-end'}`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] px-4 py-3 shadow-sm ${
          isAI
            ? 'bg-white text-text rounded-2xl rounded-bl-none border'
            : 'bg-primary text-white rounded-2xl rounded-br-none'
        }`}
      >
        {renderContent()}
      </div>
    </motion.div>
  );
};

export default MessageBubble;
