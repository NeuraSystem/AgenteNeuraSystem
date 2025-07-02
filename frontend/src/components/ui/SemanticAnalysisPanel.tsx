import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { SemanticAnalysis } from '../../types';

const SemanticAnalysisPanel: React.FC = () => {
  const { currentInput, neuralActivity, memoryStatus, fetchMemoryStatus } = useAppStore();
  const [analysis, setAnalysis] = useState<SemanticAnalysis | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Si no hay actividad neural, no hacer nada.
    if (!neuralActivity) return;

    // Show panel when there's neural activity or user input
    const shouldShow = currentInput.length > 0 || neuralActivity.thinking_state !== 'idle';
    setIsVisible(shouldShow);

    // Mock semantic analysis (in real app, this would call the backend)
    if (currentInput.length > 3) {
      const mockAnalysis: SemanticAnalysis = {
        topics: extractTopics(currentInput),
        intent: classifyIntent(currentInput),
        confidence: 0.7 + Math.random() * 0.3,
        document_relevance: Math.random() * 0.8
      };
      setAnalysis(mockAnalysis);
    } else {
      setAnalysis(null);
    }
  }, [currentInput, neuralActivity]);

  // Separate effect for memory status - only call once on mount
  useEffect(() => {
    fetchMemoryStatus();
  }, []); // Only call once on mount

  // Guarda de seguridad: si no hay actividad neural o no es visible, no renderizar.
  if (!isVisible || !neuralActivity) return null;

  return (
    <div className={`
      glass-panel p-4 transition-all duration-300 transform
      ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
    `}>
      <div className="flex items-center space-x-2 mb-3">
        <div className="w-3 h-3 rounded-full bg-brain-processing animate-pulse" />
        <h3 className="text-sm font-semibold text-brain-processing">
          Análisis Semántico
        </h3>
      </div>

      {analysis ? (
        <div className="space-y-3 text-xs">
          {/* Intent Recognition */}
          <div>
            <div className="text-brain-output font-medium mb-1">Intención:</div>
            <div className="text-white bg-black/30 px-2 py-1 rounded">
              {analysis.intent}
            </div>
            <div className="text-gray-400 mt-1">
              Confianza: {Math.round(analysis.confidence * 100)}%
            </div>
          </div>

          {/* Topic Extraction */}
          {analysis.topics.length > 0 && (
            <div>
              <div className="text-brain-memory font-medium mb-1">Temas:</div>
              <div className="flex flex-wrap gap-1">
                {analysis.topics.map((topic, index) => (
                  <span
                    key={index}
                    className="bg-brain-memory/20 text-brain-memory px-2 py-1 rounded-full text-xs"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Document Relevance */}
          {analysis.document_relevance !== undefined && (
            <div>
              <div className="text-brain-input font-medium mb-1">Relevancia Documental:</div>
              <div className="w-full bg-black/30 rounded-full h-2">
                <div
                  className="bg-brain-input h-2 rounded-full transition-all duration-500"
                  style={{ width: `${analysis.document_relevance * 100}%` }}
                />
              </div>
              <div className="text-gray-400 mt-1">
                {Math.round(analysis.document_relevance * 100)}% relevancia
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-gray-400 text-xs">
          {neuralActivity.thinking_state === 'processing' ? (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-brain-processing rounded-full animate-ping" />
              <span>Analizando entrada...</span>
            </div>
          ) : (
            'Escribe algo para ver el análisis...'
          )}
        </div>
      )}

      {/* Memory Status - Real Data */}
      {memoryStatus && !memoryStatus.isLoading && !memoryStatus.error && (
        <div className="mt-3 pt-3 border-t border-white/20">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Pensamiento Crítico:</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                memoryStatus.critical_thinking_enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {memoryStatus.critical_thinking_enabled ? 'ACTIVO' : 'INACTIVO'}
              </span>
            </div>
            
            {memoryStatus.category_stats && (
              <div>
                <span className="text-gray-400">Categorías activas:</span>
                <div className="text-white ml-2">
                  {Object.keys(memoryStatus.category_stats).length} categorías
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Alertas pendientes:</span>
              <span className="text-yellow-400">{memoryStatus.active_alerts_count || 0}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Estado Neural:</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                neuralActivity.thinking_state === 'idle' ? 'bg-brain-idle/20 text-brain-idle' :
                neuralActivity.thinking_state === 'processing' ? 'bg-brain-processing/20 text-brain-processing' :
                neuralActivity.thinking_state === 'generating' ? 'bg-brain-output/20 text-brain-output' :
                'bg-brain-memory/20 text-brain-memory'
              }`}>
                {neuralActivity.thinking_state.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions for semantic analysis
function extractTopics(text: string): string[] {
  const topics = [];
  const keywords = {
    'personal': ['yo', 'mi', 'me gusta', 'rutina', 'hobby'],
    'familiar': ['familia', 'esposa', 'esposo', 'hijo', 'hija', 'madre', 'padre'],
    'laboral': ['trabajo', 'oficina', 'empresa', 'proyecto', 'jefe'],
    'social': ['amigo', 'amiga', 'fiesta', 'evento', 'conocido'],
    'escolar': ['clase', 'universidad', 'estudio', 'examen', 'tarea'],
    'deportiva': ['ejercicio', 'gym', 'deporte', 'entrenar', 'fitness']
  };

  for (const [topic, words] of Object.entries(keywords)) {
    if (words.some(word => text.toLowerCase().includes(word))) {
      topics.push(topic);
    }
  }

  return topics;
}

function classifyIntent(text: string): string {
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('recuerda') || lowerText.includes('guarda') || lowerText.includes('anota')) {
    return 'Almacenar información';
  }
  if (lowerText.includes('qué es') || lowerText.includes('explica') || lowerText.includes('definir')) {
    return 'Solicitud de información';
  }
  if (lowerText.includes('buscar') || lowerText.includes('encontrar') || lowerText.includes('mostrar')) {
    return 'Búsqueda en memoria';
  }
  if (lowerText.includes('archivo') || lowerText.includes('documento') || lowerText.includes('pdf')) {
    return 'Gestión de documentos';
  }
  if (lowerText.includes('cómo') || lowerText.includes('cuándo') || lowerText.includes('dónde')) {
    return 'Consulta contextual';
  }
  
  return 'Conversación general';
}

export default SemanticAnalysisPanel;