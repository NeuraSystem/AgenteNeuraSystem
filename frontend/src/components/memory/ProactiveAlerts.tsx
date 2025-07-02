/**
 * ProactiveAlerts - Componente para mostrar alertas y recordatorios proactivos
 * Muestra notificaciones inteligentes del asistente de manera elegante
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ProactiveAlert {
  id: string;
  type: 'reminder' | 'suggestion' | 'warning' | 'opportunity';
  category: string;
  priority: 1 | 2 | 3; // 1=alta, 2=media, 3=baja
  title: string;
  message: string;
  created_at: string;
  expires_at?: string;
  shown: boolean;
}

interface ProactiveAlertsProps {
  onAlertAction?: (alertId: string, action: 'dismiss' | 'mark_shown') => void;
}

export const ProactiveAlerts: React.FC<ProactiveAlertsProps> = ({
  onAlertAction
}) => {
  // Datos mock - en producción vendrían del hook useProactiveAlerts
  const [alerts] = useState<ProactiveAlert[]>([
    {
      id: '1',
      type: 'reminder',
      category: 'familiar',
      priority: 1,
      title: '¡Mañana es importante!',
      message: 'Mañana es tu aniversario. ¿Has pensado en algo especial?',
      created_at: '2025-06-29T10:00:00Z',
      shown: false
    },
    {
      id: '2', 
      type: 'suggestion',
      category: 'personal',
      priority: 2,
      title: '💡 Sugerencia contextual',
      message: 'Noto que estás cansado pero necesitas trabajar. ¿Te ayudo a redactar algo más conciso?',
      created_at: '2025-06-29T09:30:00Z',
      shown: false
    },
    {
      id: '3',
      type: 'opportunity',
      category: 'deportiva', 
      priority: 3,
      title: '🏃‍♂️ Recordatorio de ejercicio',
      message: 'Han pasado 4 días desde tu último ejercicio. ¿Qué tal una sesión hoy?',
      created_at: '2025-06-29T08:00:00Z',
      shown: true
    }
  ]);

  const handleAlertAction = (alertId: string, action: 'dismiss' | 'mark_shown') => {
    onAlertAction?.(alertId, action);
  };

  const getAlertTypeConfig = (type: string) => {
    const configs = {
      reminder: {
        icon: '⏰',
        bgColor: 'bg-blue-900',
        borderColor: 'border-blue-500',
        textColor: 'text-blue-100'
      },
      suggestion: {
        icon: '💡', 
        bgColor: 'bg-yellow-900',
        borderColor: 'border-yellow-500',
        textColor: 'text-yellow-100'
      },
      warning: {
        icon: '⚠️',
        bgColor: 'bg-red-900', 
        borderColor: 'border-red-500',
        textColor: 'text-red-100'
      },
      opportunity: {
        icon: '🎯',
        bgColor: 'bg-green-900',
        borderColor: 'border-green-500', 
        textColor: 'text-green-100'
      }
    };
    
    return configs[type as keyof typeof configs] || configs.suggestion;
  };

  const getPriorityConfig = (priority: number) => {
    const configs = {
      1: { label: 'Alta', color: 'bg-red-500', pulse: true },
      2: { label: 'Media', color: 'bg-yellow-500', pulse: false },
      3: { label: 'Baja', color: 'bg-gray-500', pulse: false }
    };
    
    return configs[priority as keyof typeof configs] || configs[2];
  };

  const sortedAlerts = alerts.sort((a, b) => {
    // Ordenar por prioridad (1 es más importante) y luego por fecha
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-2">😌</div>
        <p className="text-sm text-gray-400">
          Todo tranquilo por aquí
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Te avisaré si hay algo importante
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <AnimatePresence mode="popLayout">
        {sortedAlerts.map((alert, index) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            index={index}
            onAction={handleAlertAction}
            typeConfig={getAlertTypeConfig(alert.type)}
            priorityConfig={getPriorityConfig(alert.priority)}
          />
        ))}
      </AnimatePresence>

      {/* Resumen */}
      <div className="pt-2 border-t border-gray-700">
        <div className="text-xs text-gray-500 flex justify-between">
          <span>Total de alertas:</span>
          <span className="text-gray-400">{alerts.length}</span>
        </div>
        <div className="text-xs text-gray-500 flex justify-between mt-1">
          <span>Sin revisar:</span>
          <span className="text-yellow-400">
            {alerts.filter(a => !a.shown).length}
          </span>
        </div>
      </div>
    </div>
  );
};

// Componente para cada tarjeta de alerta
interface AlertCardProps {
  alert: ProactiveAlert;
  index: number;
  onAction: (alertId: string, action: 'dismiss' | 'mark_shown') => void;
  typeConfig: {
    icon: string;
    bgColor: string;
    borderColor: string;
    textColor: string;
  };
  priorityConfig: {
    label: string;
    color: string;
    pulse: boolean;
  };
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  index,
  onAction,
  typeConfig,
  priorityConfig
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const cardVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { delay: index * 0.1, duration: 0.3 }
    },
    exit: { 
      opacity: 0, 
      x: -300, 
      scale: 0.95,
      transition: { duration: 0.2 }
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Hace unos minutos';
    if (diffInHours < 24) return `Hace ${diffInHours}h`;
    return `Hace ${Math.floor(diffInHours / 24)}d`;
  };

  return (
    <motion.div
      className={`border rounded-lg ${typeConfig.bgColor} ${typeConfig.borderColor} ${typeConfig.textColor}`}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      layout
    >
      {/* Header */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2 flex-1">
            <span className="text-lg">{typeConfig.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-medium text-sm truncate">
                  {alert.title}
                </h4>
                <div 
                  className={`w-2 h-2 rounded-full ${priorityConfig.color} ${
                    priorityConfig.pulse ? 'animate-pulse' : ''
                  }`}
                  title={`Prioridad ${priorityConfig.label}`}
                />
              </div>
              
              <p className={`text-xs opacity-90 ${isExpanded ? '' : 'line-clamp-2'}`}>
                {alert.message}
              </p>
              
              {alert.message.length > 80 && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="text-xs opacity-70 hover:opacity-90 mt-1"
                >
                  {isExpanded ? 'Ver menos' : 'Ver más...'}
                </button>
              )}
            </div>
          </div>

          {/* Acciones */}
          <div className="flex gap-1">
            {!alert.shown && (
              <button
                onClick={() => onAction(alert.id, 'mark_shown')}
                className="p-1 hover:bg-white/10 rounded text-xs opacity-70 hover:opacity-100"
                title="Marcar como visto"
              >
                👁️
              </button>
            )}
            
            <button
              onClick={() => onAction(alert.id, 'dismiss')}
              className="p-1 hover:bg-white/10 rounded text-xs opacity-70 hover:opacity-100"
              title="Descartar"
            >
              ❌
            </button>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center justify-between mt-2 text-xs opacity-60">
          <span className="capitalize">{alert.category}</span>
          <span>{formatTimeAgo(alert.created_at)}</span>
        </div>
      </div>

      {/* Estado visual */}
      {!alert.shown && (
        <div className="h-1 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
      )}
    </motion.div>
  );
};