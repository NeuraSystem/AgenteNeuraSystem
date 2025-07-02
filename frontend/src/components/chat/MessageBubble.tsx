import React, { useState, useEffect } from 'react';
import { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // Remove thinking effect since it's handled by the chat component

  const isUser = message.sender === 'user';

  return (
    <div className={`
      flex items-start space-x-3 transform transition-all duration-500
      ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      ${isUser ? 'flex-row-reverse space-x-reverse' : ''}
    `}>
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isUser 
          ? 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30' 
          : 'bg-gradient-to-br from-brain-processing via-brain-output to-brain-memory shadow-lg shadow-brain-processing/30'
        }
        ${isThinking ? 'animate-pulse' : ''}
      `}>
        {isUser ? (
          <span className="text-white text-sm font-semibold">U</span>
        ) : (
          <div className="w-4 h-4 rounded-full bg-white/90 animate-pulse" />
        )}
      </div>

      {/* Message Container */}
      <div className={`
        max-w-md relative group
        ${isUser ? 'ml-auto' : 'mr-auto'}
      `}>
        {/* Neural Activity Indicator (only for AI messages) */}
        {!isUser && (
          <div className="absolute -top-2 -right-2 flex space-x-1 z-10">
            <div className="w-2 h-2 rounded-full bg-brain-processing animate-pulse" />
          </div>
        )}

        {/* Message Bubble */}
        <div className={`
          px-4 py-3 rounded-2xl backdrop-blur-md border shadow-lg
          transition-all duration-300 hover:shadow-xl
          ${isUser 
            ? 'bg-gradient-to-br from-blue-600/90 to-blue-700/90 border-blue-500/30 text-white shadow-blue-500/20' 
            : 'bg-gradient-to-br from-gray-800/90 to-gray-900/90 border-gray-700/50 text-gray-100 shadow-gray-900/20'
          }
          ${isThinking ? 'animate-pulse' : ''}
        `}>
          {/* Thinking Animation */}
          {isThinking ? (
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
              <span className="text-sm opacity-70">Procesando respuesta neural...</span>
            </div>
          ) : (
            <>
              {/* Message Content */}
              <div className="prose prose-sm max-w-none">
                <p className="mb-0 leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>

              {/* Semantic Indicators */}
              {!isUser && message.content.includes('📄') && (
                <div className="mt-2 pt-2 border-t border-gray-600/30">
                  <div className="flex items-center space-x-2 text-xs">
                    <div className="w-2 h-2 bg-brain-memory rounded-full animate-pulse" />
                    <span className="text-brain-memory font-medium">Información documental utilizada</span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Timestamp */}
        <div className={`
          text-xs text-gray-500 mt-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity
          ${isUser ? 'text-right' : 'text-left'}
        `}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>

        {/* Message Actions (on hover) */}
        <div className={`
          absolute top-0 opacity-0 group-hover:opacity-100 transition-all duration-200
          ${isUser ? '-left-10' : '-right-10'}
        `}>
          <div className="flex flex-col space-y-1">
            <button 
              className="w-6 h-6 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-black/70 transition-colors"
              title="Copiar mensaje"
              onClick={() => navigator.clipboard.writeText(message.content)}
            >
              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            
            {!isUser && (
              <button 
                className="w-6 h-6 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-black/70 transition-colors"
                title="Regenerar respuesta"
              >
                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;