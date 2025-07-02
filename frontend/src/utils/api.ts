// API utility functions for ChatIng frontend

export interface ChatMessage {
  mensaje: string;  // Backend expects 'mensaje' not 'message'
  proveedor?: string;
}

export interface ChatResponse {
  respuesta: string;  // Backend returns 'respuesta' not 'response'
  proveedor: string;
  metadatos?: any;
}

export interface DocumentUpload {
  file: File;
  process_immediately?: boolean;
}

export interface DocumentResponse {
  document_id: string;
  filename: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  chunks_count: number;
  semantic_search_available: boolean;
  message: string;
}

export interface DocumentSearchQuery {
  query: string;
  limit?: number;
  document_ids?: string[];
  similarity_threshold?: number;
}

export interface DocumentSearchResult {
  document_id: string;
  filename: string;
  content: string;
  similarity: number;
  chunk_index: number;
  metadata: Record<string, any>;
}

class ChatIngAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  // Chat endpoints
  async sendMessage(data: ChatMessage): Promise<ChatResponse> {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Document upload
  async uploadDocument(file: File, processImmediately: boolean = true): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Document upload error: ${response.statusText}`);
    }

    return response.json();
  }

  // Document search
  async searchDocuments(data: DocumentSearchQuery): Promise<DocumentSearchResult[]> {
    const response = await fetch(`${this.baseURL}/documents/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Document search error: ${response.statusText}`);
    }

    const result = await response.json();
    return result.results || [];
  }

  // Get uploaded documents
  async getDocuments(): Promise<DocumentResponse[]> {
    const response = await fetch(`${this.baseURL}/documents`);

    if (!response.ok) {
      throw new Error(`Get documents error: ${response.statusText}`);
    }

    const result = await response.json();
    return result.documents || [];
  }

  // Delete document
  async deleteDocument(documentId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Delete document error: ${response.statusText}`);
    }

    return response.json();
  }

  // Get chat history
  async getChatHistory(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    const response = await fetch(`${this.baseURL}/chat/history/${sessionId}?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Get chat history error: ${response.statusText}`);
    }

    const result = await response.json();
    return result.messages || [];
  }

  // Clear chat history
  async clearChatHistory(sessionId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/chat/history/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Clear chat history error: ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/health`);

    if (!response.ok) {
      throw new Error(`Health check error: ${response.statusText}`);
    }

    return response.json();
  }

  // Get semantic analysis for text
  async getSemanticAnalysis(text: string): Promise<{
    topics: string[];
    intent: string;
    confidence: number;
    document_relevance?: number;
  }> {
    const response = await fetch(`${this.baseURL}/analysis/semantic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error(`Semantic analysis error: ${response.statusText}`);
    }

    return response.json();
  }

  // Voice transcription (future feature)
  async transcribeAudio(audioBlob: Blob): Promise<{ transcript: string; confidence: number }> {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    const response = await fetch(`${this.baseURL}/voice/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Audio transcription error: ${response.statusText}`);
    }

    return response.json();
  }

  // Text to speech (future feature)
  async synthesizeSpeech(text: string, voice: string = 'es-ES'): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/voice/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, voice }),
    });

    if (!response.ok) {
      throw new Error(`Speech synthesis error: ${response.statusText}`);
    }

    return response.blob();
  }
}

// Create and export API instance
export const api = new ChatIngAPI();

// Utility functions
export const createSessionId = (): string => {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const isValidFileType = (filename: string): boolean => {
  const validExtensions = ['.pdf', '.docx', '.xlsx', '.txt', '.md'];
  const ext = filename.toLowerCase().substr(filename.lastIndexOf('.'));
  return validExtensions.includes(ext);
};

export const getFileIcon = (filename: string): string => {
  const ext = filename.toLowerCase().substr(filename.lastIndexOf('.'));
  switch (ext) {
    case '.pdf': return '📄';
    case '.docx': return '📝';
    case '.xlsx': return '📊';
    case '.txt': return '📃';
    case '.md': return '📋';
    default: return '📎';
  }
};

// Error handling utilities
export class APIError extends Error {
  public status: number;
  public endpoint: string;

  constructor(message: string, status: number = 500, endpoint: string = '') {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.endpoint = endpoint;
  }
}

export const handleAPIError = (error: any): string => {
  if (error instanceof APIError) {
    return `Error en ${error.endpoint}: ${error.message}`;
  }
  
  if (error.name === 'NetworkError' || error.message?.includes('fetch')) {
    return 'Error de conexión. Verifica que el servidor esté funcionando.';
  }
  
  return error.message || 'Error desconocido';
};