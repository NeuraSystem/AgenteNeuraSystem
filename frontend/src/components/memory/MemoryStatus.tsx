/**
 * MemoryStatus - Componente para mostrar el estado del sistema de memoria
 * Proporciona información sobre el procesamiento, buffer y rendimiento
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface MemoryStats {
  critical_thinking_enabled: boolean;
  buffer_status: {
    total_items: number;
    unprocessed_items: number;
    pending_review_items: number;
    buffer_age_hours: number;
  };
  category_stats: {
    [key: string]: {
      total_items: number;
      documentos: number;
      conversaciones: number;
    };
  };
  active_alerts_count: number;
  pending_review_count: number;
}

interface MemoryStatusProps {
  className?: string;
}

export const MemoryStatus: React.FC<MemoryStatusProps> = ({
  className = ''
}) => {
  // Datos mock - en producción vendrían del hook useMemorySystem
  const [stats] = useState<MemoryStats>({
    critical_thinking_enabled: true,
    buffer_status: {
      total_items: 127,
      unprocessed_items: 3,
      pending_review_items: 2,
      buffer_age_hours: 2.5
    },
    category_stats: {
      personal: { total_items: 45, documentos: 12, conversaciones: 33 },
      familiar: { total_items: 23, documentos: 8, conversaciones: 15 },
      social: { total_items: 18, documentos: 3, conversaciones: 15 }
    },
    active_alerts_count: 3,
    pending_review_count: 2
  });

  const [isProcessing, setIsProcessing] = useState(false);

  // Simular procesamiento periódico
  useEffect(() => {
    const interval = setInterval(() => {
      setIsProcessing(true);
      setTimeout(() => setIsProcessing(false), 2000);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getHealthStatus = () => {
    const { buffer_status } = stats;
    
    if (buffer_status.unprocessed_items > 10) {
      return { status: 'warning', text: 'Procesando...', color: 'text-yellow-400' };
    }
    
    if (buffer_status.pending_review_items > 5) {
      return { status: 'attention', text: 'Revisión pendiente', color: 'text-orange-400' };
    }
    
    return { status: 'healthy', text: 'Funcionando bien', color: 'text-green-400' };
  };

  const health = getHealthStatus();
  const totalItems = Object.values(stats.category_stats).reduce(
    (total, cat) => total + cat.total_items, 0
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Estado General */}
      <div className="bg-gray-700 rounded-lg p-3">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-white flex items-center gap-2">
            🧠 Sistema Neural
          </h4>
          <StatusIndicator 
            isActive={stats.critical_thinking_enabled} 
            isProcessing={isProcessing}
          />
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Estado:</span>
            <span className={health.color}>{health.text}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Total guardado:</span>
            <span className="text-white font-medium">{totalItems} items</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">En procesamiento:</span>
            <span className="text-blue-400">{stats.buffer_status.unprocessed_items}</span>
          </div>
        </div>
      </div>

      {/* Buffer de Pensamiento Crítico */}
      <div className="bg-gray-700 rounded-lg p-3">
        <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
          ⚡ Buffer Temporal
        </h4>

        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Items en buffer:</span>
            <span className="text-white">{stats.buffer_status.total_items}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Sin procesar:</span>
            <span className={stats.buffer_status.unprocessed_items > 0 ? 'text-yellow-400' : 'text-gray-400'}>
              {stats.buffer_status.unprocessed_items}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Revisión manual:</span>
            <span className={stats.buffer_status.pending_review_items > 0 ? 'text-orange-400' : 'text-gray-400'}>
              {stats.buffer_status.pending_review_items}
            </span>
          </div>

          {/* Barra de progreso */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Procesamiento</span>
              <span>
                {Math.round(
                  ((stats.buffer_status.total_items - stats.buffer_status.unprocessed_items) / 
                   stats.buffer_status.total_items) * 100
                )}%
              </span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-1.5">
              <motion.div
                className="bg-blue-500 h-1.5 rounded-full"
                initial={{ width: 0 }}
                animate={{ 
                  width: `${((stats.buffer_status.total_items - stats.buffer_status.unprocessed_items) / 
                           stats.buffer_status.total_items) * 100}%` 
                }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Distribución por Categorías */}
      <div className="bg-gray-700 rounded-lg p-3">
        <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
          📊 Distribución
        </h4>

        <div className="space-y-2">
          {Object.entries(stats.category_stats).map(([category, data]) => (
            <CategoryStatsRow 
              key={category}
              category={category}
              data={data}
              total={totalItems}
            />
          ))}
        </div>
      </div>

      {/* Acciones Rápidas */}
      <div className="space-y-2">
        <QuickActionButton
          icon="🔄"
          text="Procesar Buffer"
          variant="primary"
          disabled={stats.buffer_status.unprocessed_items === 0}
          onClick={() => {/* TODO: Implementar */}}
        />
        
        <QuickActionButton
          icon="👁️"
          text="Revisar Pendientes"
          variant="secondary"
          badge={stats.pending_review_count > 0 ? stats.pending_review_count : undefined}
          onClick={() => {/* TODO: Implementar */}}
        />
        
        <QuickActionButton
          icon="🧹"
          text="Limpiar Cache"
          variant="tertiary"
          onClick={() => {/* TODO: Implementar */}}
        />
      </div>
    </div>
  );
};

// Componente para indicador de estado
interface StatusIndicatorProps {
  isActive: boolean;
  isProcessing: boolean;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ isActive, isProcessing }) => {
  return (
    <div className="flex items-center gap-2">
      <motion.div
        className={`w-2 h-2 rounded-full ${
          isActive ? 'bg-green-400' : 'bg-red-400'
        }`}
        animate={isProcessing ? { scale: [1, 1.3, 1] } : {}}
        transition={{ duration: 1, repeat: isProcessing ? Infinity : 0 }}
      />
      <span className="text-xs text-gray-400">
        {isProcessing ? 'Procesando...' : isActive ? 'Activo' : 'Inactivo'}
      </span>
    </div>
  );
};

// Componente para estadísticas por categoría
interface CategoryStatsRowProps {
  category: string;
  data: {
    total_items: number;
    documentos: number;
    conversaciones: number;
  };
  total: number;
}

const CategoryStatsRow: React.FC<CategoryStatsRowProps> = ({ category, data, total }) => {
  const percentage = total > 0 ? (data.total_items / total) * 100 : 0;
  
  const categoryIcons: Record<string, string> = {
    personal: '👤',
    familiar: '👨‍👩‍👧‍👦',
    social: '👥',
    laboral: '💼',
    escolar: '🎓',
    deportiva: '🏃‍♂️',
    religion: '⛪'
  };

  return (
    <div className="text-xs">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span>{categoryIcons[category] || '📁'}</span>
          <span className="text-gray-300 capitalize">{category}</span>
        </div>
        <span className="text-white font-medium">{data.total_items}</span>
      </div>
      
      <div className="w-full bg-gray-600 rounded-full h-1 mb-1">
        <motion.div
          className="bg-blue-400 h-1 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, delay: 0.2 }}
        />
      </div>
      
      <div className="flex justify-between text-gray-500">
        <span>{data.documentos} docs</span>
        <span>{data.conversaciones} conv</span>
      </div>
    </div>
  );
};

// Componente para botones de acción rápida
interface QuickActionButtonProps {
  icon: string;
  text: string;
  variant: 'primary' | 'secondary' | 'tertiary';
  badge?: number;
  disabled?: boolean;
  onClick: () => void;
}

const QuickActionButton: React.FC<QuickActionButtonProps> = ({
  icon,
  text,
  variant,
  badge,
  disabled = false,
  onClick
}) => {
  const getVariantClasses = () => {
    const base = 'w-full p-2 rounded text-xs font-medium transition-colors relative';
    
    switch (variant) {
      case 'primary':
        return `${base} bg-blue-600 hover:bg-blue-500 text-white disabled:bg-gray-600 disabled:text-gray-400`;
      case 'secondary':
        return `${base} bg-gray-600 hover:bg-gray-500 text-white disabled:bg-gray-700 disabled:text-gray-500`;
      case 'tertiary':
        return `${base} border border-gray-600 hover:bg-gray-600 text-gray-300 disabled:border-gray-700 disabled:text-gray-500`;
      default:
        return `${base} bg-gray-600 hover:bg-gray-500 text-white`;
    }
  };

  return (
    <button
      className={getVariantClasses()}
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center justify-center gap-2">
        <span>{icon}</span>
        <span>{text}</span>
      </div>
      
      {badge && badge > 0 && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {badge > 9 ? '9+' : badge}
        </div>
      )}
    </button>
  );
};