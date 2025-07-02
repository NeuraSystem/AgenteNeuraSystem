/**
 * useMemorySystem - Hook para gestionar el sistema de memoria inteligente
 * Proporciona funciones para interactuar con el backend de AgenteIng
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Interfaces
interface Category {
  id: string;
  name: string;
  displayName: string;
  description: string;
  enabled: boolean;
  icon: string;
  itemCount: number;
  color: string;
}

interface MemoryItem {
  id: string;
  content: string;
  category: string;
  type: 'conversation' | 'document';
  confidence: number;
  tags: string[];
  timestamp: string;
  metadata?: Record<string, any>;
}

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

interface SearchResult {
  items: MemoryItem[];
  total: number;
  query: string;
  categories: string[];
}

interface ProcessFileResponse {
  success: boolean;
  message: string;
  category?: string;
  confidence?: number;
  items_created?: number;
}

// Hook principal
export const useMemorySystem = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/agente';

  // Obtener categorías
  const fetchCategories = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE}/categories`);
      
      // Mapear respuesta del backend a formato del frontend
      const mappedCategories: Category[] = Object.entries(response.data.categories).map(([key, config]: [string, any]) => ({
        id: key,
        name: key,
        displayName: config.display_name || key,
        description: config.description || '',
        enabled: config.enabled || false,
        icon: getCategoryIcon(key),
        itemCount: 0, // Se actualizará con las estadísticas
        color: getCategoryColor(key)
      }));

      setCategories(mappedCategories);
    } catch (err) {
      setError('Error al cargar categorías');
      console.error('Error fetching categories:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Obtener estadísticas
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
      
      // Actualizar conteos de items en categorías
      if (response.data.category_stats) {
        setCategories(prev => prev.map(cat => ({
          ...cat,
          itemCount: response.data.category_stats[cat.name]?.total_items || 0
        })));
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  // Buscar en memoria
  const searchMemory = useCallback(async (
    query: string,
    categories?: string[],
    limit: number = 10
  ): Promise<SearchResult | null> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(`${API_BASE}/search`, {
        query,
        categories: categories || [],
        limit
      });

      return {
        items: response.data.results || [],
        total: response.data.total || 0,
        query,
        categories: categories || []
      };
    } catch (err) {
      setError('Error en la búsqueda');
      console.error('Error searching memory:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Procesar archivo
  const processFile = useCallback(async (
    file: File,
    category?: string
  ): Promise<ProcessFileResponse | null> => {
    try {
      setIsLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);
      if (category) {
        formData.append('category', category);
      }

      const response = await axios.post(`${API_BASE}/process-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      // Actualizar estadísticas después del procesamiento
      await fetchStats();

      return response.data;
    } catch (err) {
      setError('Error al procesar archivo');
      console.error('Error processing file:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [fetchStats]);

  // Agregar conversación a memoria
  const addConversation = useCallback(async (
    content: string,
    category?: string
  ): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      await axios.post(`${API_BASE}/add-conversation`, {
        content,
        category: category || 'personal'
      });

      // Actualizar estadísticas
      await fetchStats();
      return true;
    } catch (err) {
      setError('Error al agregar conversación');
      console.error('Error adding conversation:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchStats]);

  // Habilitar/deshabilitar categoría
  const toggleCategory = useCallback(async (
    categoryName: string,
    enabled: boolean
  ): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      await axios.post(`${API_BASE}/toggle-category`, {
        category: categoryName,
        enabled
      });

      // Actualizar categorías localmente
      setCategories(prev => prev.map(cat => 
        cat.name === categoryName ? { ...cat, enabled } : cat
      ));

      return true;
    } catch (err) {
      setError('Error al actualizar categoría');
      console.error('Error toggling category:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Obtener items por categoría
  const getItemsByCategory = useCallback(async (
    category: string,
    limit: number = 20
  ): Promise<MemoryItem[]> => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE}/category/${category}/items`, {
        params: { limit }
      });
      return response.data.items || [];
    } catch (err) {
      console.error('Error fetching category items:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Procesar buffer manualmente
  const processBuffer = useCallback(async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      await axios.post(`${API_BASE}/process-buffer`);
      
      // Actualizar estadísticas
      await fetchStats();
      return true;
    } catch (err) {
      setError('Error al procesar buffer');
      console.error('Error processing buffer:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchStats]);

  // Limpiar cache
  const clearCache = useCallback(async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      await axios.post(`${API_BASE}/clear-cache`);
      
      // Actualizar estadísticas
      await fetchStats();
      return true;
    } catch (err) {
      setError('Error al limpiar cache');
      console.error('Error clearing cache:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchStats]);

  // Inicializar al montar
  useEffect(() => {
    fetchCategories();
    fetchStats();
  }, [fetchCategories, fetchStats]);

  // Polling para estadísticas (cada 30 segundos)
  useEffect(() => {
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  return {
    // Estado
    categories,
    stats,
    isLoading,
    error,
    
    // Funciones
    searchMemory,
    processFile,
    addConversation,
    toggleCategory,
    getItemsByCategory,
    processBuffer,
    clearCache,
    
    // Refrescar datos
    refresh: () => {
      fetchCategories();
      fetchStats();
    },
    
    // Limpiar error
    clearError: () => setError(null)
  };
};

// Funciones auxiliares
const getCategoryIcon = (categoryName: string): string => {
  const icons: Record<string, string> = {
    personal: '👤',
    familiar: '👨‍👩‍👧‍👦',
    social: '👥',
    laboral: '💼',
    escolar: '🎓',
    deportiva: '🏃‍♂️',
    religion: '⛪'
  };
  return icons[categoryName] || '📁';
};

const getCategoryColor = (categoryName: string): string => {
  const colors: Record<string, string> = {
    personal: 'bg-blue-500',
    familiar: 'bg-pink-500',
    social: 'bg-green-500',
    laboral: 'bg-orange-500',
    escolar: 'bg-purple-500',
    deportiva: 'bg-red-500',
    religion: 'bg-yellow-500'
  };
  return colors[categoryName] || 'bg-gray-500';
};