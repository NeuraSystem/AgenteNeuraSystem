import { useState, useEffect, useRef, useCallback } from 'react';

interface UseVoiceRecognitionOptions {
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  language?: string;
  silenceThreshold?: number; // milliseconds
  autoStop?: boolean;
}

interface VoiceRecognitionState {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
  confidence: number;
}

export const useVoiceRecognition = (options: UseVoiceRecognitionOptions = {}) => {
  const {
    continuous = true,
    interimResults = true,
    maxAlternatives = 1,
    language = 'es-ES',
    silenceThreshold = 2000,
    autoStop = true
  } = options;

  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    error: null,
    confidence: 0
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSpeechTimeRef = useRef<number>(0);

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: true }));
      
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.maxAlternatives = maxAlternatives;
      recognition.lang = language;

      recognitionRef.current = recognition;

      // Handle results
      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        let maxConfidence = 0;

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0].transcript;
          const confidence = result[0].confidence || 0;

          if (result.isFinal) {
            finalTranscript += transcript;
            maxConfidence = Math.max(maxConfidence, confidence);
          } else {
            interimTranscript += transcript;
          }
        }

        setState(prev => ({
          ...prev,
          transcript: prev.transcript + finalTranscript,
          interimTranscript,
          confidence: maxConfidence,
          error: null
        }));

        // Update last speech time for silence detection
        if (finalTranscript || interimTranscript) {
          lastSpeechTimeRef.current = Date.now();
          resetSilenceTimer();
        }
      };

      // Handle errors
      recognition.onerror = (event) => {
        let errorMessage = 'Error de reconocimiento de voz';
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No se detectó habla';
            break;
          case 'audio-capture':
            errorMessage = 'No se pudo acceder al micrófono';
            break;
          case 'not-allowed':
            errorMessage = 'Permisos de micrófono denegados';
            break;
          case 'network':
            errorMessage = 'Error de red';
            break;
          case 'service-not-allowed':
            errorMessage = 'Servicio de reconocimiento no disponible';
            break;
        }

        setState(prev => ({
          ...prev,
          error: errorMessage,
          isListening: false
        }));
      };

      // Handle start
      recognition.onstart = () => {
        setState(prev => ({ ...prev, isListening: true, error: null }));
        lastSpeechTimeRef.current = Date.now();
        if (autoStop) {
          startSilenceTimer();
        }
      };

      // Handle end
      recognition.onend = () => {
        setState(prev => ({ ...prev, isListening: false }));
        clearSilenceTimer();
      };

    } else {
      setState(prev => ({ 
        ...prev, 
        isSupported: false, 
        error: 'Reconocimiento de voz no soportado en este navegador' 
      }));
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      clearSilenceTimer();
    };
  }, [continuous, interimResults, maxAlternatives, language, autoStop]);

  // Silence detection timer
  const startSilenceTimer = useCallback(() => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      if (state.isListening && Date.now() - lastSpeechTimeRef.current >= silenceThreshold) {
        stop();
      }
    }, silenceThreshold);
  }, [silenceThreshold, state.isListening]);

  const resetSilenceTimer = useCallback(() => {
    if (autoStop) {
      startSilenceTimer();
    }
  }, [autoStop, startSilenceTimer]);

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  // Start recognition
  const start = useCallback(() => {
    if (!recognitionRef.current || state.isListening) return;

    try {
      // Clear previous transcript
      setState(prev => ({ 
        ...prev, 
        transcript: '', 
        interimTranscript: '', 
        error: null,
        confidence: 0
      }));
      
      recognitionRef.current.start();
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Error al iniciar reconocimiento de voz' 
      }));
    }
  }, [state.isListening]);

  // Stop recognition
  const stop = useCallback(() => {
    if (!recognitionRef.current || !state.isListening) return;

    try {
      recognitionRef.current.stop();
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Error al detener reconocimiento de voz' 
      }));
    }
  }, [state.isListening]);

  // Abort recognition
  const abort = useCallback(() => {
    if (!recognitionRef.current) return;

    try {
      recognitionRef.current.abort();
      setState(prev => ({ 
        ...prev, 
        isListening: false, 
        transcript: '', 
        interimTranscript: '',
        error: null
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Error al abortar reconocimiento de voz' 
      }));
    }
  }, []);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      transcript: '', 
      interimTranscript: '',
      confidence: 0
    }));
  }, []);

  // Check if there's meaningful content
  const hasContent = state.transcript.trim().length > 0;
  const isActive = state.isListening || state.interimTranscript.length > 0;

  return {
    ...state,
    start,
    stop,
    abort,
    resetTranscript,
    hasContent,
    isActive,
    // Computed values
    fullTranscript: state.transcript + state.interimTranscript,
    isSilent: state.isListening && Date.now() - lastSpeechTimeRef.current >= silenceThreshold / 2
  };
};

// Type declarations for older browsers
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}