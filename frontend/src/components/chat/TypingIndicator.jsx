import React from 'react';

const TypingIndicator = () => {
  return (
    <div className="flex w-fit gap-1.5 rounded-2xl rounded-bl-none border border-gray-200 bg-white px-4 py-3.5 shadow-sm">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-600"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
};

export default TypingIndicator;
