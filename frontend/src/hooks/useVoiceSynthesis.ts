import { useState, useCallback, useRef, useEffect } from 'react';
import { getElevenLabsService } from '../services/elevenlabs.service';

interface VoiceSynthesisState {
  isSpeaking: boolean;
  isLoading: boolean;
  error: string | null;
  currentText: string;
  queue: string[];
  progress: number;
}

interface VoiceSynthesisOptions {
  autoPlay?: boolean;
  queueMode?: boolean;
  voice?: string;
  emotionalContext?: 'helpful' | 'excited' | 'calm' | 'professional' | 'friendly';
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
  useStreaming?: boolean;
}

export const useVoiceSynthesis = (options: VoiceSynthesisOptions = {}) => {
  const {
    autoPlay = true,
    queueMode = true,
    emotionalContext = 'helpful',
    onStart,
    onEnd,
    onError,
    useStreaming = true, // Default to streaming
  } = options;

  const [state, setState] = useState<VoiceSynthesisState>({
    isSpeaking: false,
    isLoading: false,
    error: null,
    currentText: '',
    queue: [],
    progress: 0,
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaSourceRef = useRef<MediaSource | null>(null);
  const sourceBufferRef = useRef<SourceBuffer | null>(null);
  const audioQueue = useRef<ArrayBuffer[]>([]);
  const isAppending = useRef(false);

  const elevenLabsService = useRef(getElevenLabsService());
  const progressInterval = useRef<NodeJS.Timeout | null>(null);

  const cleanup = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }
    if (mediaSourceRef.current) {
      if (mediaSourceRef.current.readyState === 'open') {
        try {
          mediaSourceRef.current.endOfStream();
        } catch (e) {
          console.warn("Error ending MediaSource stream:", e);
        }
      }
      mediaSourceRef.current = null;
    }
    sourceBufferRef.current = null;
    audioQueue.current = [];
    isAppending.current = false;
    stopProgressTracking();
  }, []);

  const startProgressTracking = useCallback(() => {
    if (!audioRef.current) return;
    progressInterval.current = setInterval(() => {
      if (audioRef.current) {
        const progress = audioRef.current.duration > 0
          ? (audioRef.current.currentTime / audioRef.current.duration) * 100
          : 0;
        setState(prev => ({ ...prev, progress }));
      }
    }, 100);
  }, []);

  const stopProgressTracking = useCallback(() => {
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
      progressInterval.current = null;
    }
    setState(prev => ({ ...prev, progress: 0 }));
  }, []);

  const processAudioQueue = useCallback(() => {
    if (isAppending.current || !sourceBufferRef.current || sourceBufferRef.current.updating || audioQueue.current.length === 0) {
      return;
    }
    isAppending.current = true;
    const chunk = audioQueue.current.shift();
    if (chunk) {
      try {
        sourceBufferRef.current.appendBuffer(chunk);
      } catch (e) {
        console.error("Error appending buffer:", e);
        isAppending.current = false;
      }
    } else {
      isAppending.current = false;
    }
  }, []);

  const createStreamingAudio = useCallback(async (text: string) => {
    cleanup();
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    audioRef.current = new Audio();
    mediaSourceRef.current = new MediaSource();
    audioRef.current.src = URL.createObjectURL(mediaSourceRef.current);

    mediaSourceRef.current.addEventListener('sourceopen', () => {
      try {
        const mimeType = 'audio/mpeg';
        sourceBufferRef.current = mediaSourceRef.current!.addSourceBuffer(mimeType);
        sourceBufferRef.current.addEventListener('updateend', () => {
          isAppending.current = false;
          processAudioQueue();
        });

        elevenLabsService.current.textToSpeechStream(
          text,
          { emotionalContext },
          (chunk) => {
            audioQueue.current.push(chunk);
            processAudioQueue();
          },
          () => {
            const endStream = () => {
              if (mediaSourceRef.current?.readyState === 'open' && !sourceBufferRef.current?.updating) {
                mediaSourceRef.current.endOfStream();
              } else {
                setTimeout(endStream, 100);
              }
            };
            endStream();
          },
          (error) => {
            const errorMessage = error.message || 'Error en el streaming de audio';
            setState(prev => ({ ...prev, isLoading: false, isSpeaking: false, error: errorMessage }));
            onError?.(errorMessage);
          }
        );
      } catch (e) {
        console.error("Error setting up MediaSource:", e);
        const errorMessage = e instanceof Error ? e.message : 'Error al iniciar el reproductor de streaming';
        setState(prev => ({ ...prev, isLoading: false, isSpeaking: false, error: errorMessage }));
        onError?.(errorMessage);
      }
    });

    const audio = audioRef.current;
    const handlePlay = () => {
      setState(prev => ({ ...prev, isSpeaking: true, isLoading: false }));
      startProgressTracking();
      onStart?.();
    };
    const handleEnded = () => {
      setState(prev => ({ ...prev, isSpeaking: false, currentText: '' }));
      stopProgressTracking();
      cleanup();
      onEnd?.();
      if (queueMode) setTimeout(processQueue, 100);
    };
    const handleError = () => {
      const errorMessage = 'Error al reproducir audio';
      setState(prev => ({ ...prev, isSpeaking: false, isLoading: false, error: errorMessage }));
      stopProgressTracking();
      cleanup();
      onError?.(errorMessage);
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    if (autoPlay) {
      audio.play().catch(e => console.error("Playback failed:", e));
    }
  }, [cleanup, emotionalContext, onStart, onEnd, onError, autoPlay, queueMode, startProgressTracking, stopProgressTracking, processAudioQueue]);

  const createBlobAudio = useCallback(async (text: string) => {
    cleanup();
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const audioBlob = await elevenLabsService.current.textToSpeech(text, { emotionalContext });
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current = new Audio(audioUrl);

      const audio = audioRef.current;
      const handlePlay = () => {
        setState(prev => ({ ...prev, isSpeaking: true, isLoading: false }));
        startProgressTracking();
        onStart?.();
      };
      const handleEnded = () => {
        setState(prev => ({ ...prev, isSpeaking: false, currentText: '' }));
        stopProgressTracking();
        URL.revokeObjectURL(audioUrl);
        onEnd?.();
        if (queueMode) setTimeout(processQueue, 100);
      };
      const handleError = () => {
        const errorMessage = 'Error al reproducir audio';
        setState(prev => ({ ...prev, isSpeaking: false, isLoading: false, error: errorMessage }));
        stopProgressTracking();
        URL.revokeObjectURL(audioUrl);
        onError?.(errorMessage);
      };

      audio.addEventListener('play', handlePlay);
      audio.addEventListener('ended', handleEnded);
      audio.addEventListener('error', handleError);

      if (autoPlay) {
        audio.play().catch(e => console.error("Playback failed:", e));
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido al generar voz';
      setState(prev => ({ ...prev, isLoading: false, error: errorMessage }));
      onError?.(errorMessage);
    }
  }, [cleanup, emotionalContext, onStart, onEnd, onError, autoPlay, queueMode, startProgressTracking, stopProgressTracking]);

  const processQueue = useCallback(() => {
    setState(prev => {
      if (prev.queue.length === 0 || prev.isSpeaking || prev.isLoading) {
        return prev;
      }
      const [nextText, ...remainingQueue] = prev.queue;
      return { ...prev, queue: remainingQueue, currentText: nextText };
    });
  }, []);

  useEffect(() => {
    if (state.currentText && !state.isSpeaking && !state.isLoading) {
      if (useStreaming) {
        createStreamingAudio(state.currentText);
      } else {
        createBlobAudio(state.currentText);
      }
    }
  }, [state.currentText, state.isSpeaking, state.isLoading, useStreaming, createStreamingAudio, createBlobAudio]);

  useEffect(() => {
    if (!state.isSpeaking && !state.isLoading && state.queue.length > 0 && !state.currentText) {
      processQueue();
    }
  }, [state.isSpeaking, state.isLoading, state.queue.length, state.currentText, processQueue]);

  const speak = useCallback((text: string, skipQueue = false) => {
    if (!text.trim()) return;
    if (skipQueue || !queueMode) {
      stop();
      setState(prev => ({ ...prev, queue: [], currentText: text, error: null }));
    } else {
      setState(prev => ({ ...prev, queue: [...prev.queue, text], error: null }));
    }
  }, [queueMode]);

  const stop = useCallback(() => {
    cleanup();
    setState(prev => ({ ...prev, isSpeaking: false, isLoading: false, currentText: '', progress: 0 }));
  }, [cleanup]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    ...state,
    speak,
    stop,
    isActive: state.isSpeaking || state.isLoading,
  };
};