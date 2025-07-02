/**
 * ProcessingOverlay - Componente para notificaciones elegantes de procesamiento de archivos
 * Muestra animaciones suaves durante carga y análisis de contenido
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ProcessingState {
  phase: 'idle' | 'received' | 'analyzing' | 'categorizing' | 'completed' | 'error';
  fileName?: string;
  progress?: number;
  message?: string;
  category?: string;
}

interface ProcessingOverlayProps {
  isVisible: boolean;
  state: ProcessingState;
  onComplete?: () => void;
  onDismiss?: () => void;
}

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({
  isVisible,
  state,
  onComplete,
  onDismiss
}) => {
  const [displayMessage, setDisplayMessage] = useState('');

  useEffect(() => {
    const messages = {
      received: 'Archivo recibido',
      analyzing: 'Analizando contenido...',
      categorizing: 'Organizando en memoria...',
      completed: '¡Listo! Guardado en memoria',
      error: 'Error al procesar archivo'
    };

    setDisplayMessage(state.message || messages[state.phase] || '');
  }, [state.phase, state.message]);

  // Auto-dismiss después de completar
  useEffect(() => {
    if (state.phase === 'completed') {
      const timer = setTimeout(() => {
        onComplete?.();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state.phase, onComplete]);

  const getPhaseConfig = () => {
    const configs = {
      received: {
        icon: '📄',
        color: 'from-blue-600 to-blue-700',
        borderColor: 'border-blue-500',
        animation: 'bounce'
      },
      analyzing: {
        icon: '🔍',
        color: 'from-yellow-600 to-orange-600',
        borderColor: 'border-yellow-500',
        animation: 'pulse'
      },
      categorizing: {
        icon: '🧠',
        color: 'from-purple-600 to-purple-700',
        borderColor: 'border-purple-500',
        animation: 'spin'
      },
      completed: {
        icon: '✅',
        color: 'from-green-600 to-green-700',
        borderColor: 'border-green-500',
        animation: 'none'
      },
      error: {
        icon: '❌',
        color: 'from-red-600 to-red-700',
        borderColor: 'border-red-500',
        animation: 'shake'
      }
    };

    return configs[state.phase] || configs.received;
  };

  const overlayVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 50 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      transition: { 
        type: 'spring', 
        damping: 25, 
        stiffness: 300 
      }
    },
    exit: { 
      opacity: 0, 
      scale: 0.8, 
      y: -50,
      transition: { duration: 0.2 }
    }
  };

  const progressVariants = {
    hidden: { width: 0 },
    visible: { 
      width: `${state.progress || 0}%`,
      transition: { duration: 0.5, ease: 'easeOut' }
    }
  };

  const config = getPhaseConfig();

  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={state.phase === 'completed' || state.phase === 'error' ? onDismiss : undefined}
          >
            {/* Overlay Card */}
            <motion.div
              className={`bg-gradient-to-br ${config.color} rounded-2xl border ${config.borderColor} shadow-2xl max-w-md w-full p-6 text-white`}
              variants={overlayVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <AnimatedIcon 
                    icon={config.icon} 
                    animation={config.animation}
                    phase={state.phase}
                  />
                  <div>
                    <h3 className="font-semibold text-lg">
                      {state.fileName || 'Procesando archivo'}
                    </h3>
                    <p className="text-sm opacity-90">
                      {displayMessage}
                    </p>
                  </div>
                </div>

                {(state.phase === 'completed' || state.phase === 'error') && (
                  <button
                    onClick={onDismiss}
                    className="p-1 hover:bg-white/20 rounded-full transition-colors"
                  >
                    <span className="text-lg">×</span>
                  </button>
                )}
              </div>

              {/* Progress Bar */}
              {state.phase !== 'idle' && state.phase !== 'completed' && state.phase !== 'error' && (
                <div className="mb-4">
                  <div className="flex justify-between text-xs mb-2 opacity-80">
                    <span>Progreso</span>
                    <span>{Math.round(state.progress || 0)}%</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className="bg-white h-2 rounded-full"
                      variants={progressVariants}
                      initial="hidden"
                      animate="visible"
                    />
                  </div>
                </div>
              )}

              {/* Category Info */}
              {state.category && state.phase === 'completed' && (
                <div className="bg-white/10 rounded-lg p-3 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">📁</span>
                    <span className="text-sm">
                      Guardado en: <span className="font-medium capitalize">{state.category}</span>
                    </span>
                  </div>
                </div>
              )}

              {/* Processing Steps */}
              {(state.phase === 'analyzing' || state.phase === 'categorizing') && (
                <ProcessingSteps currentPhase={state.phase} />
              )}

              {/* Action Buttons */}
              {state.phase === 'error' && (
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={onDismiss}
                    className="flex-1 bg-white/20 hover:bg-white/30 py-2 px-4 rounded-lg transition-colors text-sm font-medium"
                  >
                    Cerrar
                  </button>
                  <button
                    onClick={() => {/* TODO: Implementar retry */}}
                    className="flex-1 bg-white hover:bg-white/90 text-red-600 py-2 px-4 rounded-lg transition-colors text-sm font-medium"
                  >
                    Reintentar
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

// Componente para íconos animados
interface AnimatedIconProps {
  icon: string;
  animation: string;
  phase: string;
}

const AnimatedIcon: React.FC<AnimatedIconProps> = ({ icon, animation, phase }) => {
  const getAnimationClass = () => {
    switch (animation) {
      case 'bounce':
        return 'animate-bounce';
      case 'pulse':
        return 'animate-pulse';
      case 'spin':
        return 'animate-spin';
      case 'shake':
        return 'animate-bounce'; // Simula shake con bounce
      default:
        return '';
    }
  };

  return (
    <motion.div
      className={`text-3xl ${getAnimationClass()}`}
      animate={phase === 'completed' ? { scale: [1, 1.2, 1] } : {}}
      transition={{ duration: 0.5 }}
    >
      {icon}
    </motion.div>
  );
};

// Componente para mostrar pasos del procesamiento
interface ProcessingStepsProps {
  currentPhase: string;
}

const ProcessingSteps: React.FC<ProcessingStepsProps> = ({ currentPhase }) => {
  const steps = [
    { id: 'analyzing', label: 'Leyendo contenido', icon: '📖' },
    { id: 'categorizing', label: 'Categorizando información', icon: '🏷️' },
    { id: 'saving', label: 'Guardando en memoria', icon: '💾' }
  ];

  const getCurrentStepIndex = () => {
    switch (currentPhase) {
      case 'analyzing': return 0;
      case 'categorizing': return 1;
      default: return 2;
    }
  };

  const currentIndex = getCurrentStepIndex();

  return (
    <div className="space-y-2">
      {steps.map((step, index) => {
        const isActive = index === currentIndex;
        const isCompleted = index < currentIndex;
        
        return (
          <motion.div
            key={step.id}
            className={`flex items-center gap-3 p-2 rounded ${
              isActive ? 'bg-white/20' : isCompleted ? 'bg-white/10' : 'opacity-50'
            }`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <span className={`text-lg ${isActive ? 'animate-pulse' : ''}`}>
              {isCompleted ? '✅' : step.icon}
            </span>
            <span className="text-sm">
              {step.label}
            </span>
            {isActive && (
              <motion.div
                className="ml-auto w-4 h-4 border-2 border-white/50 border-t-white rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

// Hook para manejar el estado del procesamiento
export const useProcessingOverlay = () => {
  const [state, setState] = useState<ProcessingState>({ phase: 'idle' });
  const [isVisible, setIsVisible] = useState(false);

  const startProcessing = (fileName: string) => {
    setState({ phase: 'received', fileName, progress: 0 });
    setIsVisible(true);
    
    // Simular progreso
    setTimeout(() => {
      setState(prev => ({ ...prev, phase: 'analyzing', progress: 30 }));
    }, 1000);
    
    setTimeout(() => {
      setState(prev => ({ ...prev, phase: 'categorizing', progress: 70 }));
    }, 3000);
  };

  const completeProcessing = (category: string) => {
    setState(prev => ({ 
      ...prev, 
      phase: 'completed', 
      progress: 100, 
      category 
    }));
  };

  const errorProcessing = (message: string) => {
    setState(prev => ({ ...prev, phase: 'error', message }));
  };

  const dismiss = () => {
    setIsVisible(false);
    setTimeout(() => {
      setState({ phase: 'idle' });
    }, 300);
  };

  return {
    state,
    isVisible,
    startProcessing,
    completeProcessing,
    errorProcessing,
    dismiss
  };
};