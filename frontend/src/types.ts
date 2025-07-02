
// =======================================================================
// Tipos Fundamentales de la Aplicación
// =======================================================================

/** Define el modo de visualización de la interfaz */
export interface ViewMode {
  current: 'traditional';
  transitioning: boolean;
}

/** Representa un único mensaje en el historial del chat */
export interface Message {
  id: string;
  timestamp: Date;
  sender: 'user' | 'ai';
  content: string;
  metadata?: Record<string, any>;
}


/** Representa un documento subido y procesado */
export interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'txt' | 'url';
  status: 'uploading' | 'processing' | 'ready' | 'error';
  confidence?: number;
  summary?: string;
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
