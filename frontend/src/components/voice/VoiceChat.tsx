import React, { useState, useEffect, useCallback } from 'react';
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';
import { useVoiceSynthesis } from '../../hooks/useVoiceSynthesis';
import { useAppStore } from '../../stores/appStore';

// Visualizer component for audio waves
const AudioVisualizer = ({ state }: { state: string }) => {
  const barCount = 20;
  const baseHeight = 4;
  const maxHeight = 20;

  const getHeight = () => {
    switch (state) {
      case 'listening':
        return Math.random() * (maxHeight - baseHeight) + baseHeight;
      case 'speaking':
        return Math.random() * (maxHeight - baseHeight) + baseHeight;
      default:
        return baseHeight;
    }
  };

  return (
    <div className="flex items-center justify-center space-x-1 h-8">
      {Array.from({ length: barCount }).map((_, i) => (
        <div
          key={i}
          className="w-1 bg-green-400 rounded-full transition-all duration-150"
          style={{ height: `${getHeight()}px` }}
        />
      ))}
    </div>
  );
};

export const VoiceChat: React.FC<{ isEnabled: boolean; onToggle: (enabled: boolean) => void; }> = ({ isEnabled, onToggle }) => {
  const { sendMessage, isTyping, messages } = useAppStore();
  const [conversationState, setConversationState] = useState<'idle' | 'listening' | 'processing' | 'speaking'>('idle');
  const [autoMode, setAutoMode] = useState(true);

  const {
    isListening,
    isSupported: speechSupported,
    transcript,
    interimTranscript,
    error: speechError,
    start: startListening,
    stop: stopListening,
    resetTranscript,
    hasContent,
  } = useVoiceRecognition({
    continuous: true,
    interimResults: true,
    language: 'es-ES',
    silenceThreshold: 2500,
    autoStop: true,
  });

  const {
    isSpeaking,
    isLoading: ttsLoading,
    speak,
    stop: stopSpeaking,
  } = useVoiceSynthesis({
    autoPlay: true,
    queueMode: false,
    useStreaming: true,
    onStart: () => setConversationState('speaking'),
    onEnd: () => {
      setConversationState('idle');
      if (autoMode && isEnabled) {
        setTimeout(() => {
          resetTranscript();
          startListening();
        }, 300);
      }
    },
  });

  useEffect(() => {
    if (isSpeaking) setConversationState('speaking');
    else if (isTyping || ttsLoading) setConversationState('processing');
    else if (isListening) setConversationState('listening');
    else setConversationState('idle');
  }, [isSpeaking, isTyping, ttsLoading, isListening]);

  useEffect(() => {
    if (isEnabled && !isListening && hasContent && transcript.trim().length > 2) {
      handleSendVoiceMessage(transcript);
    }
  }, [isListening, hasContent, transcript, isEnabled]);

  useEffect(() => {
    if (isEnabled && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.sender === 'ai' && !isSpeaking && !ttsLoading) {
        speak(lastMessage.content);
      }
    }
  }, [messages, isEnabled, speak, isSpeaking, ttsLoading]);

  const handleSendVoiceMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim()) return;
    setConversationState('processing');
    resetTranscript();
    await sendMessage(messageText.trim());
  }, [sendMessage, resetTranscript]);

  const handleToggleVoiceChat = useCallback(() => {
    const newEnabled = !isEnabled;
    onToggle(newEnabled);
    if (newEnabled) {
      setTimeout(startListening, 100);
    } else {
      stopListening();
      stopSpeaking();
      resetTranscript();
      setAutoMode(false);
      setConversationState('idle');
    }
  }, [isEnabled, onToggle, startListening, stopListening, stopSpeaking, resetTranscript]);

  const getStatusInfo = () => {
    switch (conversationState) {
      case 'listening': return { text: 'Escuchando...', color: 'text-green-400', icon: 'mic' };
      case 'processing': return { text: 'Procesando...', color: 'text-yellow-400', icon: 'spinner' };
      case 'speaking': return { text: 'Hablando...', color: 'text-blue-400', icon: 'speaker' };
      default: return { text: 'Inactivo', color: 'text-gray-400', icon: 'mic_off' };
    }
  };

  const { text: statusText, color: statusColor, icon: statusIcon } = getStatusInfo();

  if (!speechSupported) {
    return (
      <div className="glass-panel p-4 text-center text-red-400">
        Reconocimiento de voz no soportado. Prueba con Chrome o Edge.
      </div>
    );
  }

  return (
    <div className="glass-panel p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Chat de Voz</h3>
        <button
          onClick={handleToggleVoiceChat}
          className={`px-4 py-2 rounded-lg transition-all ${isEnabled ? 'bg-green-600' : 'bg-gray-600'}`}
        >
          {isEnabled ? 'Desactivar' : 'Activar'}
        </button>
      </div>

      {isEnabled && (
        <>
          <div className="bg-black/30 rounded-lg p-3 text-center">
            <div className={`font-medium ${statusColor} mb-2`}>{statusText}</div>
            <AudioVisualizer state={conversationState} />
            <div className="min-h-[40px] text-white mt-2">
              <span className="text-green-300">{transcript}</span>
              <span className="text-gray-400 italic">{interimTranscript}</span>
            </div>
          </div>

          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => isListening ? stopListening() : startListening()}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-all transform hover:scale-105 ${
                isListening ? 'bg-red-500 animate-pulse' : 'bg-brain-input'
              }`}
            >
              {/* Icons for mic/stop */}
            </button>
            <button
              onClick={() => setAutoMode(!autoMode)}
              className={`px-4 py-2 rounded-lg text-sm ${autoMode ? 'bg-purple-600' : 'bg-gray-600'}`}
            >
              {autoMode ? 'Auto' : 'Manual'}
            </button>
          </div>
          {speechError && <div className="text-red-400 text-sm text-center">Error: {speechError}</div>}
        </>
      )}
    </div>
  );
};