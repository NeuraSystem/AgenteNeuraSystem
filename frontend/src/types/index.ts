export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isThinking?: boolean;
  neural_activity?: NeuralActivity;
  metadata?: Record<string, any>;
}

export interface Document {
  id: string;
  name: string;
  filename?: string;
  type: 'pdf' | 'docx' | 'xlsx' | 'txt' | 'md' | 'url';
  status: 'uploading' | 'processing' | 'ready' | 'error';
  uploaded_at?: string;
  chunks_count?: number;
  semantic_search_available?: boolean;
  confidence?: number;
  summary?: string;
}

export interface NeuralActivity {
  input_intensity: number;
  processing_intensity: number;
  output_intensity: number;
  memory_access: number;
  thinking_state: 'idle' | 'processing' | 'generating' | 'searching';
}

export interface ViewMode {
  current: 'immersive' | 'traditional';
  transitioning: boolean;
}

export interface AudioState {
  isRecording: boolean;
  isPlaying: boolean;
  volume: number;
  frequency_data?: Float32Array;
}

export interface SemanticAnalysis {
  topics: string[];
  intent: string;
  confidence: number;
  document_relevance?: number;
}

// =======================================================================
// Tipos para el Sistema AgenteIng
// =======================================================================

/** Representa una categoría de memoria de AgenteIng */
export interface Category {
  id: string;
  name: string;
  displayName: string;
  description: string;
  enabled: boolean;
  subcategories: string[];
}

/** Representa una alerta generada por el Asistente Proactivo */
export interface ProactiveAlert {
  id: string;
  title: string;
  message: string;
  priority: number;
  category: string;
  timestamp: string;
  related_items?: string[];
}

/** Información de un archivo pendiente de categorización */
export interface PendingFile {
  file_id: string;
  file_name: string;
  file_path: string;
  suggested_category: string;
  confidence: number;
  reasoning: string;
  alternative_categories: { category: string; confidence: number }[];
}

/** Respuesta de la API para el análisis de archivos */
export interface FileAnalysisResponse {
  success: boolean;
  file_info?: {
    id: string;
    name: string;
    path: string;
  };
  suggested_category: string;
  confidence: number;
  reasoning: string;
  alternative_categories: { category: string; confidence: number }[];
  error?: string;
}