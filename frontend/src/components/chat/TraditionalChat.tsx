import React, { useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { api } from '../../utils/api';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

const TraditionalChat: React.FC = () => {
  const { messages, isTyping, sendMessage, updateNeuralActivity } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Simulate neural activity
    updateNeuralActivity({
      input_intensity: 0.8,
      thinking_state: 'processing'
    });

    // Use the store's sendMessage function which connects to the real backend
    try {
      await sendMessage(content.trim());
      
      // Reset neural activity after message is sent
      updateNeuralActivity({
        output_intensity: 0.6,
        thinking_state: 'idle',
        processing_intensity: 0.1
      });
    } catch (error) {
      console.error('Error enviando mensaje:', error);
      
      // Reset neural activity on error
      updateNeuralActivity({
        thinking_state: 'idle',
        processing_intensity: 0.1,
        output_intensity: 0.2
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <div className="glass-panel m-4 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brain-input via-brain-processing to-brain-output animate-pulse" />
          <div>
            <h1 className="text-lg font-semibold text-white">ChatIng</h1>
            <p className="text-sm text-gray-400">IA Conversacional con Análisis Neural</p>
          </div>
        </div>
        
      </div>


      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-brain-input via-brain-processing to-brain-output mb-4 animate-pulse" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Bienvenido a ChatIng
            </h2>
            <p className="text-gray-400 max-w-md">
              Inicia una conversación y observa cómo mi cerebro neural procesa la información en tiempo real.
              Puedes alternar a la vista inmersiva para una experiencia completa.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="chat-bubble assistant">
                  <div className="flex items-center space-x-1">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-brain-processing rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                    <span className="text-sm text-gray-400 ml-2">Procesando...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4">
        <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
};

export default TraditionalChat;