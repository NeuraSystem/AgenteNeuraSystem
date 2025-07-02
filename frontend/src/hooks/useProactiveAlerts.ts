/**
 * useProactiveAlerts - Hook para gestionar alertas y recordatorios proactivos
 * Maneja la comunicación con el sistema de asistente proactivo del backend
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Interfaces
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
  metadata?: Record<string, any>;
}

interface AlertsStats {
  total: number;
  unread: number;
  by_type: {
    reminder: number;
    suggestion: number;
    warning: number;
    opportunity: number;
  };
  by_priority: {
    high: number;
    medium: number;
    low: number;
  };
}

interface CreateAlertRequest {
  type: ProactiveAlert['type'];
  category: string;
  priority: ProactiveAlert['priority'];
  title: string;
  message: string;
  expires_at?: string;
  metadata?: Record<string, any>;
}

// Hook principal
export const useProactiveAlerts = () => {
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([]);
  const [stats, setStats] = useState<AlertsStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/agente';

  // Obtener alertas
  const fetchAlerts = useCallback(async (includeShown: boolean = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`${API_BASE}/alerts`, {
        params: { include_shown: includeShown }
      });

      setAlerts(response.data.alerts || []);
      setStats(response.data.stats || null);
    } catch (err) {
      setError('Error al cargar alertas');
      console.error('Error fetching alerts:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Marcar alerta como vista
  const markAlertAsShown = useCallback(async (alertId: string): Promise<boolean> => {
    try {
      setError(null);

      await axios.post(`${API_BASE}/alerts/${alertId}/mark-shown`);

      // Actualizar estado local
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, shown: true } : alert
      ));

      // Actualizar estadísticas
      if (stats) {
        setStats(prev => prev ? {
          ...prev,
          unread: Math.max(0, prev.unread - 1)
        } : null);
      }

      return true;
    } catch (err) {
      setError('Error al marcar alerta como vista');
      console.error('Error marking alert as shown:', err);
      return false;
    }
  }, [stats]);

  // Descartar alerta
  const dismissAlert = useCallback(async (alertId: string): Promise<boolean> => {
    try {
      setError(null);

      await axios.delete(`${API_BASE}/alerts/${alertId}`);

      // Remover del estado local
      setAlerts(prev => prev.filter(alert => alert.id !== alertId));

      // Actualizar estadísticas
      if (stats) {
        setStats(prev => {
          if (!prev) return null;
          
          const dismissedAlert = alerts.find(a => a.id === alertId);
          if (!dismissedAlert) return prev;

          return {
            ...prev,
            total: prev.total - 1,
            unread: dismissedAlert.shown ? prev.unread : Math.max(0, prev.unread - 1),
            by_type: {
              ...prev.by_type,
              [dismissedAlert.type]: Math.max(0, prev.by_type[dismissedAlert.type] - 1)
            },
            by_priority: {
              ...prev.by_priority,
              [getPriorityName(dismissedAlert.priority)]: Math.max(0, prev.by_priority[getPriorityName(dismissedAlert.priority)] - 1)
            }
          };
        });
      }

      return true;
    } catch (err) {
      setError('Error al descartar alerta');
      console.error('Error dismissing alert:', err);
      return false;
    }
  }, [alerts, stats]);

  // Crear alerta manual
  const createAlert = useCallback(async (alertData: CreateAlertRequest): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(`${API_BASE}/alerts`, alertData);

      // Agregar al estado local
      if (response.data.alert) {
        setAlerts(prev => [response.data.alert, ...prev]);
        
        // Actualizar estadísticas
        if (stats) {
          setStats(prev => prev ? {
            ...prev,
            total: prev.total + 1,
            unread: prev.unread + 1,
            by_type: {
              ...prev.by_type,
              [alertData.type]: prev.by_type[alertData.type] + 1
            },
            by_priority: {
              ...prev.by_priority,
              [getPriorityName(alertData.priority)]: prev.by_priority[getPriorityName(alertData.priority)] + 1
            }
          } : null);
        }
      }

      return true;
    } catch (err) {
      setError('Error al crear alerta');
      console.error('Error creating alert:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [stats]);

  // Obtener alertas por categoría
  const getAlertsByCategory = useCallback(async (category: string): Promise<ProactiveAlert[]> => {
    try {
      const response = await axios.get(`${API_BASE}/alerts/category/${category}`);
      return response.data.alerts || [];
    } catch (err) {
      console.error('Error fetching alerts by category:', err);
      return [];
    }
  }, []);

  // Obtener alertas por tipo
  const getAlertsByType = useCallback(async (type: ProactiveAlert['type']): Promise<ProactiveAlert[]> => {
    try {
      const response = await axios.get(`${API_BASE}/alerts/type/${type}`);
      return response.data.alerts || [];
    } catch (err) {
      console.error('Error fetching alerts by type:', err);
      return [];
    }
  }, []);

  // Marcar todas las alertas como vistas
  const markAllAsShown = useCallback(async (): Promise<boolean> => {
    try {
      setError(null);

      await axios.post(`${API_BASE}/alerts/mark-all-shown`);

      // Actualizar estado local
      setAlerts(prev => prev.map(alert => ({ ...alert, shown: true })));
      
      // Actualizar estadísticas
      if (stats) {
        setStats(prev => prev ? { ...prev, unread: 0 } : null);
      }

      return true;
    } catch (err) {
      setError('Error al marcar todas como vistas');
      console.error('Error marking all as shown:', err);
      return false;
    }
  }, [stats]);

  // Limpiar alertas expiradas
  const clearExpiredAlerts = useCallback(async (): Promise<boolean> => {
    try {
      setError(null);

      const response = await axios.delete(`${API_BASE}/alerts/expired`);
      const removedCount = response.data.removed_count || 0;

      if (removedCount > 0) {
        // Refrescar alertas
        await fetchAlerts();
      }

      return true;
    } catch (err) {
      setError('Error al limpiar alertas expiradas');
      console.error('Error clearing expired alerts:', err);
      return false;
    }
  }, [fetchAlerts]);

  // Obtener alertas de alta prioridad
  const getHighPriorityAlerts = useCallback((): ProactiveAlert[] => {
    return alerts.filter(alert => alert.priority === 1 && !alert.shown);
  }, [alerts]);

  // Obtener alertas no leídas
  const getUnreadAlerts = useCallback((): ProactiveAlert[] => {
    return alerts.filter(alert => !alert.shown);
  }, [alerts]);

  // Obtener alertas por prioridad
  const getAlertsByPriority = useCallback((priority: 1 | 2 | 3): ProactiveAlert[] => {
    return alerts.filter(alert => alert.priority === priority);
  }, [alerts]);

  // Manejar acción de alerta
  const handleAlertAction = useCallback(async (alertId: string, action: 'dismiss' | 'mark_shown') => {
    if (action === 'dismiss') {
      return await dismissAlert(alertId);
    } else if (action === 'mark_shown') {
      return await markAlertAsShown(alertId);
    }
    return false;
  }, [dismissAlert, markAlertAsShown]);

  // Inicializar al montar
  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  // Polling para nuevas alertas (cada 2 minutos)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAlerts();
    }, 120000);

    return () => clearInterval(interval);
  }, [fetchAlerts]);

  // Auto-limpiar alertas expiradas (cada 10 minutos)
  useEffect(() => {
    const interval = setInterval(() => {
      clearExpiredAlerts();
    }, 600000);

    return () => clearInterval(interval);
  }, [clearExpiredAlerts]);

  return {
    // Estado
    alerts,
    stats,
    isLoading,
    error,
    
    // Funciones principales
    fetchAlerts,
    createAlert,
    dismissAlert,
    markAlertAsShown,
    handleAlertAction,
    
    // Funciones de utilidad
    getAlertsByCategory,
    getAlertsByType,
    getHighPriorityAlerts,
    getUnreadAlerts,
    getAlertsByPriority,
    
    // Acciones en lote
    markAllAsShown,
    clearExpiredAlerts,
    
    // Refrescar datos
    refresh: () => fetchAlerts(),
    
    // Limpiar error
    clearError: () => setError(null),
    
    // Computed values
    hasUnreadAlerts: (stats?.unread || 0) > 0,
    hasHighPriorityAlerts: getHighPriorityAlerts().length > 0,
    totalAlerts: alerts.length,
    unreadCount: stats?.unread || 0
  };
};

// Funciones auxiliares
const getPriorityName = (priority: 1 | 2 | 3): 'high' | 'medium' | 'low' => {
  switch (priority) {
    case 1: return 'high';
    case 2: return 'medium';
    case 3: return 'low';
    default: return 'medium';
  }
};

// Hook para crear alertas rápidas
export const useQuickAlerts = () => {
  const { createAlert } = useProactiveAlerts();

  const createReminder = useCallback((title: string, message: string, category: string = 'personal') => {
    return createAlert({
      type: 'reminder',
      category,
      priority: 2,
      title,
      message
    });
  }, [createAlert]);

  const createSuggestion = useCallback((title: string, message: string, category: string = 'personal') => {
    return createAlert({
      type: 'suggestion',
      category,
      priority: 3,
      title,
      message
    });
  }, [createAlert]);

  const createWarning = useCallback((title: string, message: string, category: string = 'personal') => {
    return createAlert({
      type: 'warning',
      category,
      priority: 1,
      title,
      message
    });
  }, [createAlert]);

  const createOpportunity = useCallback((title: string, message: string, category: string = 'personal') => {
    return createAlert({
      type: 'opportunity',
      category,
      priority: 2,
      title,
      message
    });
  }, [createAlert]);

  return {
    createReminder,
    createSuggestion,
    createWarning,
    createOpportunity
  };
};