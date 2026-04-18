import React from 'react';
import { motion } from 'framer-motion';

const TypingIndicator = () => {
  return (
    <div className="flex glass-card px-4 py-3.5 rounded-2xl rounded-bl-none gap-1.5 w-fit border-accent/20 shadow-lg shadow-accent/5">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 bg-accent rounded-full shadow-[0_0_8px_#06b6d4]"
          animate={{ 
            opacity: [0.3, 1, 0.3],
            scale: [0.8, 1.1, 0.8]
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.2,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
};

export default TypingIndicator;
