
import { create } from 'zustand';
import axios from 'axios';
import { 
  Message, 
  Document, 
  Category, 
  ProactiveAlert, 
  PendingFile,
  NeuralActivity
} from '../types/index';

// =======================================================================
// Configuración de API y Tipos de Respuesta
// =======================================================================

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

interface DocumentUploadResponse {
  document_id: string;
  file_name: string;
  file_type: string;
  status: string;
  message: string;
}

// =======================================================================
// Definición del Estado Global (Store)
// =======================================================================

interface AppState {
  // --- Estado de la Interfaz y Chat ---
  messages: Message[];
  isTyping: boolean;
  currentInput: string;
  
  // --- Estado de AgenteIng ---
  isLoading: boolean;
  error: string | null;
  categories: Category[];
  proactiveAlerts: ProactiveAlert[];
  pendingFiles: PendingFile[];
  documents: Document[];
  memoryStatus: any;
  neuralActivity: NeuralActivity;
  
  // --- Estado de Interacciones Activas ---
  activeInteractions: string[];
  
  // --- Control de Rate Limiting ---
  lastFetchTimes: {
    categories: number;
    documents: number;
    memoryStatus: number;
    alerts: number;
  };

  // --- Acciones (Funciones) ---
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setTyping: (typing: boolean) => void;
  setCurrentInput: (input: string) => void;
  updateNeuralActivity: (activity: Partial<NeuralActivity>) => void;
  addDocument: (document: Document) => void;
  addInteraction: (interaction: string) => void;
  removeInteraction: (interaction: string) => void;
  sendMessage: (message: string) => Promise<void>;
  fetchCategories: () => Promise<void>;
  uploadAndAnalyzeFile: (file: File) => Promise<void>;
  approveCategorization: (fileId: string, approvedCategory: string) => Promise<void>;
  fetchActiveAlerts: () => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;
  fetchDocuments: () => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  fetchMemoryStatus: () => Promise<void>;
  createCategory: (categoryData: { name: string; displayName: string; description: string }) => Promise<void>;
  checkBackendHealth: () => Promise<boolean>;
  debugSystemStatus: () => Promise<void>;
}

// =======================================================================
// Implementación del Store con Zustand
// =======================================================================

// Estado inicial seguro para memoryStatus y neuralActivity
const initialMemoryStatus = {
  critical_thinking_enabled: false,
  buffer_status: { total_items: 0, processed_items: 0, pending_items: 0 },
  category_stats: { total_categories: 0, enabled_categories: 0 },
  active_alerts_count: 0,
  pending_review_count: 0,
  error: null,
  isLoading: true,
};

const initialNeuralActivity = {
  thinking_state: 'idle',
  input_intensity: 0,
  processing_intensity: 0,
  output_intensity: 0,
};

export const useAppStore = create<AppState>((set, get) => ({
  // --- Estado Inicial ---
  messages: [],
  isTyping: false,
  currentInput: '',
  isLoading: false,
  error: null,
  categories: [],
  proactiveAlerts: [],
  pendingFiles: [],
  documents: [],
  memoryStatus: initialMemoryStatus,
  neuralActivity: initialNeuralActivity,
  activeInteractions: [],
  lastFetchTimes: {
    categories: 0,
    documents: 0,
    memoryStatus: 0,
    alerts: 0
  },

  // --- Implementación de Acciones ---
  addMessage: (message) => set((state) => ({ messages: [...state.messages, { ...message, id: crypto.randomUUID(), timestamp: new Date() }] })),
  setTyping: (typing) => set({ isTyping: typing }),
  setCurrentInput: (input) => set({ currentInput: input }),
  updateNeuralActivity: (activity) => set(state => ({ neuralActivity: { ...state.neuralActivity, ...activity } })),
  addDocument: (document) => set(state => ({ documents: [...state.documents, document] })),
  addInteraction: (interaction) => set(state => ({ 
    activeInteractions: [...state.activeInteractions.filter(i => i !== interaction), interaction] 
  })),
  removeInteraction: (interaction) => set(state => ({ 
    activeInteractions: state.activeInteractions.filter(i => i !== interaction)
  })),

  sendMessage: async (message: string) => {
    const userMessage: Omit<Message, 'id' | 'timestamp'> = { sender: 'user', content: message };
    get().addMessage(userMessage);
    set({ isTyping: true });
    get().updateNeuralActivity({ thinking_state: 'generating' });
    try {
      // Añadir información de debug sobre documentos disponibles
      const { documents } = get();
      console.log(`💬 Enviando mensaje con ${documents.length} documentos disponibles:`, 
                  documents.map(d => ({ name: d.name, status: d.status })));
      
      const response = await apiClient.post('/chat', { mensaje: message });
      const aiMessage: Omit<Message, 'id' | 'timestamp'> = { sender: 'ai', content: response.data.respuesta };
      get().addMessage(aiMessage);
      
      // Log para debug si la respuesta usa información de documentos
      if (response.data.respuesta.includes('📄') || response.data.respuesta.includes('documento')) {
        console.log('✅ La respuesta parece usar información de documentos');
      } else {
        console.log('⚠️ La respuesta no parece usar información de documentos específicos');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? `Error: ${err.message}` : 'Failed to get response from AI';
      get().addMessage({ sender: 'ai', content: errorMsg });
    } finally {
      set({ isTyping: false });
      get().updateNeuralActivity({ thinking_state: 'idle' });
    }
  },

  fetchCategories: async () => {
    const now = Date.now();
    const { lastFetchTimes } = get();
    
    // Rate limiting: solo hacer la llamada si han pasado al menos 10 segundos
    if (now - lastFetchTimes.categories < 10000) {
      return;
    }
    
    set(state => ({ 
      isLoading: true, 
      error: null,
      lastFetchTimes: { ...state.lastFetchTimes, categories: now }
    }));
    
    try {
      const response = await apiClient.get('/agente/categories');
      const categories = response.data.categories.map((cat: any) => ({
        id: cat.id,
        name: cat.name,
        displayName: cat.displayName,
        description: cat.description,
        enabled: cat.enabled,
        subcategories: cat.subcategories || []
      }));
      set({ categories, isLoading: false });
    } catch (err: any) {
      // Handle 503 Service Unavailable gracefully
      if (err.response?.status === 503) {
        console.warn('AgenteIng backend not available, using default categories');
        set({ 
          categories: [], 
          isLoading: false, 
          error: 'Sistema de categorización no disponible temporalmente'
        });
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch categories';
        set({ isLoading: false, error: errorMsg });
      }
    }
  },

  uploadAndAnalyzeFile: async (file: File) => {
    set({ isLoading: true, error: null });
    get().updateNeuralActivity({ thinking_state: 'processing' });
    
    // Verificar salud del backend antes de intentar subir
    const isBackendHealthy = await get().checkBackendHealth();
    if (!isBackendHealthy) {
      set({ isLoading: false });
      get().updateNeuralActivity({ thinking_state: 'idle' });
      return; // Error ya está establecido por checkBackendHealth
    }
    
    // Ejecutar diagnóstico detallado si hay problemas
    await get().debugSystemStatus();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      console.log(`📁 Subiendo archivo: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
      
      // 1. Subir archivo al endpoint básico de documentos
      const uploadResponse = await apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      const { document_id, file_name, file_type, status } = uploadResponse.data;

      // 2. Crear documento y añadirlo inmediatamente a la lista
      const newDocument: Document = {
        id: document_id,
        name: file_name,
        filename: file_name,
        type: file_type as any,
        status: status as any,
        uploaded_at: new Date().toISOString(),
        chunks_count: 0,
        semantic_search_available: true,
        confidence: 1.0,
        summary: `Subido el ${new Date().toLocaleDateString()}`
      };

      // Añadir documento a la lista inmediatamente
      set(state => ({ 
        documents: [...state.documents, newDocument],
        isLoading: false 
      }));

      // 3. Intentar análisis opcional con AgenteIng (en background, no crítico)
      try {
        const analysisResponse = await apiClient.post('/agente/analyze/file', {
          file_path: `uploads/${document_id}_${file_name}`,
          file_name: file_name
        });

        if (analysisResponse.data.success) {
          const analysisResult: PendingFile = {
            file_id: document_id,
            file_name: file_name,
            file_path: `uploads/${document_id}_${file_name}`,
            suggested_category: analysisResponse.data.suggested_category,
            confidence: analysisResponse.data.confidence,
            reasoning: analysisResponse.data.reasoning,
            alternative_categories: analysisResponse.data.alternative_categories || [],
          };

          set(state => ({ pendingFiles: [...state.pendingFiles, analysisResult] }));
          console.log('AgenteIng analysis completed for:', file_name);
        }
      } catch (analysisErr) {
        // Si AgenteIng no está disponible, solo hacer log pero no fallar
        console.warn('AgenteIng analysis not available (this is OK):', analysisErr);
      }

    } catch (err: any) {
      // Handle 503 Service Unavailable gracefully
      if (err.response?.status === 503) {
        console.warn('Upload service not available');
        set({ 
          isLoading: false, 
          error: 'Servicio de subida de archivos no disponible temporalmente. Asegúrate de que el backend esté corriendo.'
        });
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to upload file';
        set({ isLoading: false, error: errorMsg });
      }
    } finally {
      get().updateNeuralActivity({ thinking_state: 'idle' });
    }
  },

  approveCategorization: async (fileId: string, approvedCategory: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post('/agente/approve/categorization', {
        file_id: fileId,
        approved_category: approvedCategory,
      });
      set((state) => ({ pendingFiles: state.pendingFiles.filter(f => f.file_id !== fileId), isLoading: false }));
      
      // Actualizar lista de documentos después de categorizar
      const { fetchDocuments } = get();
      fetchDocuments();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to approve categorization';
      set({ isLoading: false, error: errorMsg });
    }
  },

  fetchActiveAlerts: async () => {
    const now = Date.now();
    const { lastFetchTimes } = get();
    
    // Rate limiting: solo hacer la llamada si han pasado al menos 15 segundos
    if (now - lastFetchTimes.alerts < 15000) {
      return;
    }
    
    set(state => ({ 
      isLoading: true, 
      error: null,
      lastFetchTimes: { ...state.lastFetchTimes, alerts: now }
    }));
    
    try {
      const response = await apiClient.get('/agente/alerts');
      set({ proactiveAlerts: response.data.alerts || [], isLoading: false });
    } catch (err: any) {
      // Handle 503 Service Unavailable gracefully
      if (err.response?.status === 503) {
        console.warn('Alerts service not available, keeping existing alerts');
        set({ 
          isLoading: false, 
          error: 'Servicio de alertas no disponible temporalmente'
        });
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch alerts';
        set({ isLoading: false, error: errorMsg });
      }
    }
  },

  dismissAlert: async (alertId: string) => {
    try {
      await apiClient.post('/agente/alerts/action', { alert_id: alertId, action: 'dismiss' });
      set((state) => ({ proactiveAlerts: state.proactiveAlerts.filter(a => a.id !== alertId) }));
    } catch (err) {
      console.error("Failed to dismiss alert:", err);
    }
  },

  fetchDocuments: async () => {
    const now = Date.now();
    const { lastFetchTimes } = get();
    
    // Rate limiting: solo hacer la llamada si han pasado al menos 10 segundos
    if (now - lastFetchTimes.documents < 10000) {
      return;
    }
    
    set(state => ({ 
      isLoading: true, 
      error: null,
      lastFetchTimes: { ...state.lastFetchTimes, documents: now }
    }));
    
    try {
      const response = await apiClient.get('/documents/list');
      const documents = response.data.map((doc: any) => ({
        id: doc.document_id,
        name: doc.file_name,
        type: doc.file_type,
        status: doc.status,
        confidence: 1.0,
        summary: `Processed at ${doc.processed_at}`
      }));
      set({ documents, isLoading: false });
    } catch (err: any) {
      // Handle 503 Service Unavailable gracefully
      if (err.response?.status === 503) {
        console.warn('Documents service not available, keeping existing documents');
        set({ 
          isLoading: false, 
          error: 'Servicio de documentos no disponible temporalmente'
        });
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch documents';
        set({ isLoading: false, error: errorMsg });
      }
    }
  },

  deleteDocument: async (documentId: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.delete(`/documents/${documentId}`);
      set((state) => ({ 
        documents: state.documents.filter(doc => doc.id !== documentId),
        isLoading: false 
      }));
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete document';
      set({ isLoading: false, error: errorMsg });
    }
  },

  fetchMemoryStatus: async () => {
    const now = Date.now();
    const { lastFetchTimes } = get();
    
    // Rate limiting: solo hacer la llamada si han pasado al menos 30 segundos
    if (now - lastFetchTimes.memoryStatus < 30000) {
      return;
    }
    
    set(state => ({ 
      memoryStatus: { ...state.memoryStatus, isLoading: true },
      lastFetchTimes: { ...state.lastFetchTimes, memoryStatus: now }
    }));
    
    try {
      const response = await apiClient.get('/agente/status');
      set({ memoryStatus: { ...response.data, isLoading: false, error: null } });
    } catch (err: any) {
      // Handle 503 Service Unavailable gracefully
      if (err.response?.status === 503) {
        console.warn('AgenteIng memory system not available, using fallback status');
        set({ 
          memoryStatus: { 
            ...initialMemoryStatus, 
            isLoading: false, 
            error: 'Sistema de memoria no disponible temporalmente'
          } 
        });
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch memory status';
        console.error("Failed to fetch memory status:", err);
        set({ memoryStatus: { ...initialMemoryStatus, isLoading: false, error: errorMsg } });
      }
    }
  },

  createCategory: async (categoryData: { name: string; displayName: string; description: string }) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/agente/categories', categoryData);
      if (response.data.success) {
        // Refresh categories after creating new one
        await get().fetchCategories();
      } else {
        throw new Error(response.data.error || 'Failed to create category');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create category';
      set({ isLoading: false, error: errorMsg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  checkBackendHealth: async () => {
    try {
      console.log('🔍 Verificando salud del backend...');
      
      // Intentar hacer una llamada simple al chat endpoint
      const response = await apiClient.post('/chat', { 
        mensaje: 'health check',
        timeout: 5000 
      }, {
        timeout: 5000
      });
      
      console.log('✅ Backend está respondiendo:', response.status);
      return true;
    } catch (err: any) {
      console.error('❌ Backend no está respondiendo:', {
        status: err.response?.status,
        message: err.message,
        code: err.code
      });
      
      // Mostrar error específico al usuario
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        set({ 
          error: '🔴 Backend no está corriendo. Por favor ejecuta: cd backend && python run.py' 
        });
      } else if (err.response?.status >= 500) {
        set({ 
          error: `🔴 Error del servidor backend (${err.response.status}). Revisa los logs del backend.` 
        });
      } else {
        set({ 
          error: `🔴 Error de conexión con backend: ${err.message}` 
        });
      }
      
      return false;
    }
  },

  debugSystemStatus: async () => {
    try {
      console.log('🔍 Diagnosticando estado del sistema...');
      const response = await apiClient.get('/debug/system-status');
      
      console.log('📊 Estado del sistema:', response.data);
      
      const { document_processing, agente_ing, contextual_memory } = response.data;
      
      // Mostrar información específica sobre cada sistema
      if (!document_processing.enabled) {
        console.error('❌ DocumentManager no inicializado:', document_processing.error || 'Error desconocido');
      } else {
        console.log('✅ DocumentManager inicializado correctamente');
      }
      
      if (!agente_ing.enabled) {
        console.error('❌ AgenteIng no inicializado:', agente_ing.error || 'Error desconocido');
      } else {
        console.log('✅ AgenteIng inicializado correctamente');
      }
      
      if (!contextual_memory.enabled) {
        console.error('❌ ContextualMemory no inicializado:', contextual_memory.error || 'Error desconocido');
      } else {
        console.log('✅ ContextualMemory inicializado correctamente');
      }
      
    } catch (err: any) {
      console.error('❌ Error al consultar estado del sistema:', err);
    }
  },
}));
