/**
 * ThinkingIndicator - Componente para mostrar procesamiento en tiempo real
 * Indica cuando el asistente está "pensando" o procesando información
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ThinkingState {
  isThinking: boolean;
  process?: 'analyzing' | 'remembering' | 'connecting' | 'generating' | 'organizing';
  intensity?: 'low' | 'medium' | 'high';
  context?: string;
  duration?: number; // en segundos
}

interface ThinkingIndicatorProps {
  state: ThinkingState;
  position?: 'top-right' | 'bottom-right' | 'center' | 'inline';
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  state,
  position = 'bottom-right',
  size = 'medium',
  className = ''
}) => {
  const [dots, setDots] = useState('');
  const [currentPhase, setCurrentPhase] = useState(0);

  // Animación de puntos pensando
  useEffect(() => {
    if (!state.isThinking) return;

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(interval);
  }, [state.isThinking]);

  // Rotación de fases de pensamiento
  useEffect(() => {
    if (!state.isThinking) return;

    const phases = [
      'Analizando contexto',
      'Conectando ideas', 
      'Organizando respuesta',
      'Reflexionando'
    ];

    const interval = setInterval(() => {
      setCurrentPhase(prev => (prev + 1) % phases.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [state.isThinking]);

  const getProcessConfig = () => {
    const configs = {
      analyzing: {
        icon: '🧠',
        color: 'from-blue-500 to-purple-600',
        label: 'Analizando',
        description: 'Procesando información'
      },
      remembering: {
        icon: '💭',
        color: 'from-green-500 to-blue-500',
        label: 'Recordando',
        description: 'Consultando memoria'
      },
      connecting: {
        icon: '🔗',
        color: 'from-yellow-500 to-orange-500',
        label: 'Conectando',
        description: 'Relacionando conceptos'
      },
      generating: {
        icon: '✨',
        color: 'from-purple-500 to-pink-500',
        label: 'Generando',
        description: 'Creando respuesta'
      },
      organizing: {
        icon: '📝',
        color: 'from-orange-500 to-red-500',
        label: 'Organizando',
        description: 'Estructurando ideas'
      }
    };

    return configs[state.process || 'analyzing'];
  };

  const getSizeConfig = () => {
    const configs = {
      small: {
        container: 'w-8 h-8',
        icon: 'text-sm',
        text: 'text-xs',
        padding: 'p-1'
      },
      medium: {
        container: 'w-12 h-12',
        icon: 'text-lg',
        text: 'text-sm',
        padding: 'p-2'
      },
      large: {
        container: 'w-16 h-16',
        icon: 'text-2xl',
        text: 'text-base',
        padding: 'p-3'
      }
    };

    return configs[size];
  };

  const getPositionClasses = () => {
    const positions = {
      'top-right': 'fixed top-4 right-4 z-50',
      'bottom-right': 'fixed bottom-4 right-4 z-50',
      'center': 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50',
      'inline': 'relative'
    };

    return positions[position];
  };

  const getIntensityAnimation = () => {
    switch (state.intensity) {
      case 'low':
        return { scale: [1, 1.05, 1], duration: 2 };
      case 'medium':
        return { scale: [1, 1.1, 1], duration: 1.5 };
      case 'high':
        return { scale: [1, 1.15, 1], duration: 1 };
      default:
        return { scale: [1, 1.1, 1], duration: 1.5 };
    }
  };

  const processConfig = getProcessConfig();
  const sizeConfig = getSizeConfig();
  const animation = getIntensityAnimation();

  const containerVariants = {
    hidden: { 
      opacity: 0, 
      scale: 0.8,
      y: position.includes('bottom') ? 20 : -20
    },
    visible: { 
      opacity: 1, 
      scale: 1,
      y: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 400
      }
    },
    exit: { 
      opacity: 0, 
      scale: 0.8,
      y: position.includes('bottom') ? 20 : -20,
      transition: { duration: 0.2 }
    }
  };

  const thoughtBubbleVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 10 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      transition: { delay: 0.2, duration: 0.3 }
    },
    exit: { opacity: 0, scale: 0.8, y: 10 }
  };

  if (!state.isThinking) return null;

  return (
    <div className={`${getPositionClasses()} ${className}`}>
      <AnimatePresence mode="wait">
        <motion.div
          key="thinking-indicator"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          {/* Indicador principal */}
          <motion.div
            className={`bg-gradient-to-br ${processConfig.color} rounded-full ${sizeConfig.container} ${sizeConfig.padding} flex items-center justify-center shadow-lg border border-white/20 backdrop-blur-sm`}
            animate={animation}
            transition={{ 
              repeat: Infinity, 
              duration: animation.duration,
              ease: 'easeInOut'
            }}
          >
            <motion.span 
              className={`${sizeConfig.icon} text-white`}
              animate={{ rotate: [0, 360] }}
              transition={{ 
                duration: 3, 
                repeat: Infinity, 
                ease: 'linear' 
              }}
            >
              {processConfig.icon}
            </motion.span>
          </motion.div>

          {/* Burbuja de pensamiento */}
          {(size === 'medium' || size === 'large') && (
            <motion.div
              className="absolute -top-2 -left-2"
              variants={thoughtBubbleVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <ThoughtBubble 
                size={size === 'large' ? 'large' : 'small'}
                intensity={state.intensity || 'medium'}
              />
            </motion.div>
          )}

          {/* Texto contextual */}
          {state.context && size !== 'small' && (
            <motion.div
              className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-3 py-1 rounded-lg shadow-lg border border-gray-600 whitespace-nowrap"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <span className={sizeConfig.text}>
                {state.context}{dots}
              </span>
            </motion.div>
          )}

          {/* Ondas de pensamiento */}
          <ThinkingWaves 
            intensity={state.intensity || 'medium'}
            color={processConfig.color}
          />
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

// Componente para burbuja de pensamiento
interface ThoughtBubbleProps {
  size: 'small' | 'large';
  intensity: 'low' | 'medium' | 'high';
}

const ThoughtBubble: React.FC<ThoughtBubbleProps> = ({ size, intensity }) => {
  const bubbleSize = size === 'large' ? 'w-3 h-3' : 'w-2 h-2';
  
  const getAnimationDelay = () => {
    switch (intensity) {
      case 'low': return [0, 0.3, 0.6];
      case 'medium': return [0, 0.2, 0.4];
      case 'high': return [0, 0.1, 0.2];
      default: return [0, 0.2, 0.4];
    }
  };

  const delays = getAnimationDelay();

  return (
    <div className="flex items-end gap-1">
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className={`${bubbleSize} bg-white/60 rounded-full`}
          animate={{ 
            scale: [0.8, 1.2, 0.8],
            opacity: [0.4, 1, 0.4]
          }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity,
            delay: delays[index],
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  );
};

// Componente para ondas de pensamiento
interface ThinkingWavesProps {
  intensity: 'low' | 'medium' | 'high';
  color: string;
}

const ThinkingWaves: React.FC<ThinkingWavesProps> = ({ intensity, color }) => {
  const getWaveCount = () => {
    switch (intensity) {
      case 'low': return 2;
      case 'medium': return 3;
      case 'high': return 4;
      default: return 3;
    }
  };

  const waveCount = getWaveCount();
  const waves = Array.from({ length: waveCount }, (_, i) => i);

  return (
    <div className="absolute inset-0 pointer-events-none">
      {waves.map((wave) => (
        <motion.div
          key={wave}
          className={`absolute inset-0 rounded-full border-2 border-white/20`}
          initial={{ scale: 1, opacity: 0.8 }}
          animate={{ 
            scale: [1, 2, 2.5],
            opacity: [0.8, 0.3, 0]
          }}
          transition={{ 
            duration: 2,
            repeat: Infinity,
            delay: wave * 0.5,
            ease: 'easeOut'
          }}
        />
      ))}
    </div>
  );
};

// Hook para manejar el estado de pensamiento
export const useThinkingState = () => {
  const [state, setState] = useState<ThinkingState>({ isThinking: false });

  const startThinking = (
    process?: ThinkingState['process'],
    intensity?: ThinkingState['intensity'],
    context?: string,
    duration?: number
  ) => {
    setState({
      isThinking: true,
      process: process || 'analyzing',
      intensity: intensity || 'medium',
      context,
      duration
    });

    // Auto-stop si se especifica duración
    if (duration) {
      setTimeout(() => {
        stopThinking();
      }, duration * 1000);
    }
  };

  const updateThinking = (updates: Partial<ThinkingState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  const stopThinking = () => {
    setState(prev => ({ ...prev, isThinking: false }));
  };

  const toggleThinking = () => {
    setState(prev => ({ ...prev, isThinking: !prev.isThinking }));
  };

  return {
    state,
    startThinking,
    updateThinking,
    stopThinking,
    toggleThinking,
    isThinking: state.isThinking
  };
};