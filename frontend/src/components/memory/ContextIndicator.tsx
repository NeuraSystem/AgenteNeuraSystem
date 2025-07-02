/**
 * ContextIndicator - Componente para mostrar cuando se están consultando memorias
 * Aparece durante las consultas al sistema de memoria para dar contexto al usuario
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MemoryQuery {
  id: string;
  type: 'search' | 'retrieve' | 'analyze' | 'categorize';
  query: string;
  categories?: string[];
  timestamp: Date;
  status: 'searching' | 'found' | 'not_found' | 'error';
  results?: number;
}

interface ContextIndicatorProps {
  isActive: boolean;
  currentQuery?: MemoryQuery;
  className?: string;
}

export const ContextIndicator: React.FC<ContextIndicatorProps> = ({
  isActive,
  currentQuery,
  className = ''
}) => {
  const [displayText, setDisplayText] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (!currentQuery) return;

    const texts = {
      search: 'Buscando en memoria...',
      retrieve: 'Recuperando información...',
      analyze: 'Analizando contexto...',
      categorize: 'Organizando información...'
    };

    setDisplayText(texts[currentQuery.type] || 'Consultando memoria...');
  }, [currentQuery]);

  const getQueryTypeConfig = (type: string) => {
    const configs = {
      search: {
        icon: '🔍',
        color: 'from-blue-500 to-blue-600',
        description: 'Buscando información relevante'
      },
      retrieve: {
        icon: '📖',
        color: 'from-green-500 to-green-600',
        description: 'Recuperando datos guardados'
      },
      analyze: {
        icon: '🧠',
        color: 'from-purple-500 to-purple-600',
        description: 'Analizando contexto y relaciones'
      },
      categorize: {
        icon: '🏷️',
        color: 'from-orange-500 to-orange-600',
        description: 'Categorizando nueva información'
      }
    };

    return configs[type] || configs.search;
  };

  const getStatusConfig = (status: string) => {
    const configs = {
      searching: {
        animation: 'animate-pulse',
        textColor: 'text-blue-300'
      },
      found: {
        animation: '',
        textColor: 'text-green-300'
      },
      not_found: {
        animation: '',
        textColor: 'text-yellow-300'
      },
      error: {
        animation: 'animate-bounce',
        textColor: 'text-red-300'
      }
    };

    return configs[status] || configs.searching;
  };

  const indicatorVariants = {
    hidden: { 
      opacity: 0, 
      y: 20, 
      scale: 0.8 
    },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 400
      }
    },
    exit: { 
      opacity: 0, 
      y: -20, 
      scale: 0.8,
      transition: { duration: 0.2 }
    }
  };

  const detailsVariants = {
    hidden: { height: 0, opacity: 0 },
    visible: { 
      height: 'auto', 
      opacity: 1,
      transition: { duration: 0.3, ease: 'easeInOut' }
    }
  };

  if (!currentQuery) return null;

  const typeConfig = getQueryTypeConfig(currentQuery.type);
  const statusConfig = getStatusConfig(currentQuery.status);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          className={`fixed top-4 right-4 z-40 ${className}`}
          variants={indicatorVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          <div className={`bg-gradient-to-r ${typeConfig.color} rounded-lg shadow-lg border border-white/20 backdrop-blur-sm`}>
            {/* Main Indicator */}
            <div 
              className="p-3 cursor-pointer"
              onClick={() => setShowDetails(!showDetails)}
            >
              <div className="flex items-center gap-3">
                <motion.span 
                  className={`text-xl ${statusConfig.animation}`}
                  animate={currentQuery.status === 'searching' ? { rotate: [0, 360] } : {}}
                  transition={{ duration: 2, repeat: currentQuery.status === 'searching' ? Infinity : 0, ease: 'linear' }}
                >
                  {typeConfig.icon}
                </motion.span>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium text-sm">
                      {displayText}
                    </span>
                    {currentQuery.results !== undefined && (
                      <span className="text-xs bg-white/20 text-white px-2 py-1 rounded-full">
                        {currentQuery.results} items
                      </span>
                    )}
                  </div>
                  
                  <p className={`text-xs ${statusConfig.textColor} mt-1`}>
                    {typeConfig.description}
                  </p>
                </div>

                <motion.button
                  className="text-white/70 hover:text-white transition-colors"
                  animate={{ rotate: showDetails ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <span className="text-sm">▼</span>
                </motion.button>
              </div>
            </div>

            {/* Expandable Details */}
            <AnimatePresence>
              {showDetails && (
                <motion.div
                  className="overflow-hidden"
                  variants={detailsVariants}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                >
                  <div className="px-3 pb-3 border-t border-white/20">
                    <QueryDetails query={currentQuery} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Progress Bar */}
            {currentQuery.status === 'searching' && (
              <div className="h-1 bg-white/20 rounded-b-lg overflow-hidden">
                <motion.div
                  className="h-full bg-white/60"
                  animate={{ 
                    x: ['-100%', '100%'] 
                  }}
                  transition={{ 
                    duration: 2, 
                    repeat: Infinity, 
                    ease: 'easeInOut' 
                  }}
                />
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Componente para mostrar detalles de la consulta
interface QueryDetailsProps {
  query: MemoryQuery;
}

const QueryDetails: React.FC<QueryDetailsProps> = ({ query }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getStatusMessage = () => {
    switch (query.status) {
      case 'searching':
        return 'Procesando consulta...';
      case 'found':
        return `Encontrado${query.results ? ` (${query.results} resultados)` : ''}`;
      case 'not_found':
        return 'No se encontró información relacionada';
      case 'error':
        return 'Error en la búsqueda';
      default:
        return 'Estado desconocido';
    }
  };

  return (
    <div className="space-y-2 mt-2">
      {/* Query Text */}
      <div>
        <span className="text-xs text-white/70">Consulta:</span>
        <p className="text-sm text-white bg-white/10 rounded px-2 py-1 mt-1">
          "{query.query}"
        </p>
      </div>

      {/* Categories */}
      {query.categories && query.categories.length > 0 && (
        <div>
          <span className="text-xs text-white/70">Categorías:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {query.categories.map((category, index) => (
              <span 
                key={index}
                className="text-xs bg-white/20 text-white px-2 py-1 rounded-full"
              >
                {category}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Status and Timestamp */}
      <div className="flex justify-between items-center text-xs">
        <span className="text-white/70">
          {getStatusMessage()}
        </span>
        <span className="text-white/50">
          {formatTime(query.timestamp)}
        </span>
      </div>
    </div>
  );
};

// Hook para manejar consultas de memoria
export const useMemoryQueries = () => {
  const [currentQuery, setCurrentQuery] = useState<MemoryQuery | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [queryHistory, setQueryHistory] = useState<MemoryQuery[]>([]);

  const startQuery = (
    type: MemoryQuery['type'], 
    query: string, 
    categories?: string[]
  ) => {
    const newQuery: MemoryQuery = {
      id: Math.random().toString(36).substr(2, 9),
      type,
      query,
      categories,
      timestamp: new Date(),
      status: 'searching'
    };

    setCurrentQuery(newQuery);
    setIsActive(true);
    
    // Agregar al historial
    setQueryHistory(prev => [newQuery, ...prev.slice(0, 9)]);
  };

  const updateQueryStatus = (
    status: MemoryQuery['status'], 
    results?: number
  ) => {
    if (currentQuery) {
      const updatedQuery = { ...currentQuery, status, results };
      setCurrentQuery(updatedQuery);
      
      // Actualizar en historial
      setQueryHistory(prev => 
        prev.map(q => q.id === currentQuery.id ? updatedQuery : q)
      );
    }
  };

  const completeQuery = (results?: number) => {
    updateQueryStatus(results !== undefined && results > 0 ? 'found' : 'not_found', results);
    
    // Auto-hide después de 3 segundos
    setTimeout(() => {
      setIsActive(false);
      setTimeout(() => setCurrentQuery(null), 300);
    }, 3000);
  };

  const errorQuery = () => {
    updateQueryStatus('error');
    
    // Auto-hide después de 5 segundos en caso de error
    setTimeout(() => {
      setIsActive(false);
      setTimeout(() => setCurrentQuery(null), 300);
    }, 5000);
  };

  const dismissQuery = () => {
    setIsActive(false);
    setTimeout(() => setCurrentQuery(null), 300);
  };

  return {
    currentQuery,
    isActive,
    queryHistory,
    startQuery,
    updateQueryStatus,
    completeQuery,
    errorQuery,
    dismissQuery
  };
};