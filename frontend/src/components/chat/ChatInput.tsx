import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';
import { useVoiceSynthesis } from '../../hooks/useVoiceSynthesis';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  voiceMode?: boolean;
  onVoiceModeChange?: (enabled: boolean) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  disabled = false, 
  voiceMode = false,
  onVoiceModeChange 
}) => {
  const [message, setMessage] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { setCurrentInput, updateNeuralActivity, addInteraction, removeInteraction } = useAppStore();

  // Voice Recognition Setup
  const {
    isListening,
    isSupported: voiceSupported,
    transcript,
    interimTranscript,
    error: voiceError,
    start: startListening,
    stop: stopListening,
    resetTranscript,
    hasContent: hasVoiceContent,
    fullTranscript
  } = useVoiceRecognition({
    continuous: true,
    interimResults: true,
    language: 'es-ES',
    silenceThreshold: 2000,
    autoStop: true
  });

  // Voice Synthesis Setup (for voice mode feedback)
  const {
    isSpeaking,
    speak,
    stop: stopSpeaking
  } = useVoiceSynthesis({
    autoPlay: true,
    emotionalContext: 'friendly'
  });

  useEffect(() => {
    const currentText = voiceMode ? fullTranscript : message;
    setCurrentInput(currentText);
    // Simulate input neural activity
    if (currentText.length > 0) {
      updateNeuralActivity({
        input_intensity: Math.min(currentText.length / 100, 1),
        thinking_state: currentText.length > 10 ? 'processing' : 'idle'
      });
    }
  }, [message, fullTranscript, voiceMode, setCurrentInput, updateNeuralActivity]);

  // Auto-sync voice transcript to text input when not in voice mode
  useEffect(() => {
    if (!voiceMode && transcript && transcript.trim()) {
      setMessage(transcript.trim());
      resetTranscript();
    }
  }, [transcript, voiceMode, resetTranscript]);

  // Auto-send voice messages when speech stops
  useEffect(() => {
    if (voiceMode && !isListening && hasVoiceContent && transcript.trim().length > 3) {
      handleSendMessage(transcript.trim());
      resetTranscript();
    }
  }, [voiceMode, isListening, hasVoiceContent, transcript, resetTranscript]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message, fullTranscript]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Simulate neural activity
    updateNeuralActivity({
      input_intensity: 0.8,
      thinking_state: 'processing'
    });

    try {
      await onSendMessage(content.trim());
      
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const textToSend = voiceMode ? fullTranscript.trim() : message.trim();
    
    if (textToSend && !disabled) {
      handleSendMessage(textToSend);
      setMessage('');
      if (voiceMode) {
        resetTranscript();
      }
      setIsExpanded(false);
      updateNeuralActivity({
        input_intensity: 0,
        thinking_state: 'idle'
      });
    }
  };

  const handleKeyDown = (e: React.KeyEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleVoiceToggle = () => {
    if (voiceMode) {
      // Toggle listening in voice mode
      if (isListening) {
        stopListening();
        removeInteraction('voice');
        updateNeuralActivity({
          input_intensity: 0.2,
          thinking_state: 'idle'
        });
      } else {
        startListening();
        addInteraction('voice');
        updateNeuralActivity({
          input_intensity: 0.8,
          thinking_state: 'processing'
        });
      }
    } else {
      // Quick voice input in text mode
      if (isListening) {
        stopListening();
      } else {
        resetTranscript();
        startListening();
      }
    }
  };

  const handleVoiceModeToggle = () => {
    const newVoiceMode = !voiceMode;
    onVoiceModeChange?.(newVoiceMode);
    
    if (newVoiceMode) {
      // Entering voice mode
      setMessage('');
      resetTranscript();
    } else {
      // Exiting voice mode
      stopListening();
      stopSpeaking();
      if (transcript.trim()) {
        setMessage(transcript.trim());
      }
      resetTranscript();
    }
  };

  const quickPrompts = [
    "Hola, ¿cómo puedes ayudarme?",
    "Explícame qué puedes hacer",
    "¿Cómo funciona tu memoria?",
    "¿Qué tipo de archivos puedo subir?"
  ];

  return (
    <div className="space-y-3">
      {/* Quick Prompts */}
      {!voiceMode && message.length === 0 && !fullTranscript && (
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => setMessage(prompt)}
              className="px-3 py-1 text-xs bg-gray-800/50 hover:bg-gray-700/50 rounded-full border border-gray-600/30 text-gray-300 hover:text-white transition-all duration-200 hover:scale-105"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Main Input Container */}
      <form onSubmit={handleSubmit} className="relative">
        <div className={`
          glass-panel transition-all duration-300 overflow-hidden
          ${isExpanded || message.length > 0 || fullTranscript.length > 0 ? 'shadow-lg shadow-brain-processing/20' : ''}
          ${disabled ? 'opacity-50 pointer-events-none' : ''}
          ${voiceMode ? 'ring-2 ring-green-400/30' : ''}
        `}>
          {/* Neural Activity Indicator */}
          {(message.length > 0 || fullTranscript.length > 0) && (
            <div className="absolute top-2 right-2 flex space-x-1 z-10">
              <div className="w-2 h-2 bg-brain-input rounded-full animate-pulse" />
              <div className="w-2 h-2 bg-brain-processing rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              {voiceMode && <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />}
            </div>
          )}

          {/* Input Area */}
          <div className="flex items-end space-x-3 p-4">
            {/* Voice Button */}
            <button
              type="button"
              onClick={handleVoiceToggle}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 flex-shrink-0
                ${isListening 
                  ? 'bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30 animate-pulse' 
                  : 'bg-brain-input/20 hover:bg-brain-input/30 text-brain-input'
                }
                ${voiceMode ? 'ring-2 ring-green-400' : ''}
                ${!voiceSupported ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              title={
                !voiceSupported 
                  ? 'Reconocimiento de voz no soportado'
                  : voiceMode
                    ? (isListening ? 'Detener escucha' : 'Comenzar escucha')
                    : (isListening ? 'Detener grabación' : 'Grabar mensaje de voz')
              }
              disabled={!voiceSupported}
            >
              {isListening ? (
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              )}
            </button>

            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={voiceMode ? fullTranscript : message}
                onChange={(e) => {
                  if (!voiceMode) {
                    setMessage(e.target.value);
                  }
                }}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsExpanded(true)}
                onBlur={() => setIsExpanded(false)}
                placeholder={
                  voiceMode 
                    ? (isListening ? "🎤 Escuchando... Habla ahora" : "Modo voz activado - Presiona el micrófono")
                    : (isListening ? "🎤 Grabando... Habla ahora" : "Escribe tu mensaje aquí...")
                }
                className={`w-full bg-transparent resize-none outline-none text-white placeholder-gray-400 min-h-[24px] max-h-32 leading-6 ${
                  voiceMode && fullTranscript && !transcript ? 'text-gray-300' : ''
                }`}
                rows={1}
                disabled={disabled || (voiceMode && isListening)}
              />
              
              {/* Character Counter */}
              {(message.length > 0 || fullTranscript.length > 0) && (
                <div className="absolute bottom-0 right-0 text-xs text-gray-500">
                  {(voiceMode ? fullTranscript : message).length}/1000
                </div>
              )}

              {/* Voice transcript indicator */}
              {voiceMode && interimTranscript && (
                <div className="absolute bottom-6 left-0 text-xs text-yellow-400 italic">
                  Transcribiendo...
                </div>
              )}
            </div>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!(voiceMode ? fullTranscript.trim() : message.trim()) || disabled}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 flex-shrink-0
                ${(voiceMode ? fullTranscript.trim() : message.trim()) && !disabled
                  ? 'bg-gradient-to-r from-brain-processing to-brain-output hover:from-brain-output hover:to-brain-processing shadow-lg shadow-brain-processing/30 transform hover:scale-105'
                  : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
                }
              `}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>

          {/* Advanced Options */}
          {isExpanded && (
            <div className="border-t border-gray-700/50 px-4 py-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    type="button"
                    onClick={handleVoiceModeToggle}
                    className={`
                      flex items-center space-x-1 text-xs transition-colors px-2 py-1 rounded
                      ${voiceMode 
                        ? 'text-green-400 bg-green-400/10 hover:bg-green-400/20'
                        : 'text-gray-400 hover:text-brain-processing'
                      }
                      ${!voiceSupported ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                    title={voiceMode ? 'Desactivar modo voz' : 'Activar modo voz'}
                    disabled={!voiceSupported}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <span>{voiceMode ? '🔊 Activo' : 'Voz'}</span>
                  </button>
                  
                  <button
                    type="button"
                    className="flex items-center space-x-1 text-xs text-gray-400 hover:text-brain-memory transition-colors"
                    title="Adjuntar archivo"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                    <span>Archivo</span>
                  </button>
                  
                  <button
                    type="button"
                    className="flex items-center space-x-1 text-xs text-gray-400 hover:text-brain-processing transition-colors"
                    title="Análisis semántico"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span>Análisis</span>
                  </button>
                </div>
                
                <div className="text-xs text-gray-500">
                  {voiceMode 
                    ? (isListening ? '🔴 Escuchando...' : '🎤 Modo voz activo')
                    : (isListening ? '🔴 Grabando...' : 'Shift+Enter para nueva línea')
                  }
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Voice Status Indicator */}
        {(isListening || voiceMode) && (
          <div className="absolute -top-12 left-1/2 transform -translate-x-1/2">
            <div className="glass-panel px-3 py-1 flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full animate-pulse ${
                isListening ? 'bg-red-500' : 'bg-green-500'
              }`} />
              <span className={`text-xs ${
                isListening ? 'text-red-400' : 'text-green-400'
              }`}>
                {isListening 
                  ? (voiceMode ? 'Escuchando...' : 'Grabando audio...') 
                  : 'Modo voz activo'
                }
              </span>
              {voiceError && (
                <span className="text-xs text-red-400 ml-2">Error: {voiceError}</span>
              )}
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default ChatInput;