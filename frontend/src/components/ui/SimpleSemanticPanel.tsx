import React from 'react';
import { useAppStore } from '../../stores/appStore';

interface SemanticData {
  keywords: string[];
  topic: string;
  sentiment: string;
  contextualSimilarity: number;
  episodicSimilarity: number;
  vectorSimilarity: number;
  confidence: number;
}

interface SimpleSemanticPanelProps {
  semanticData: SemanticData | null;
  isVisible: boolean;
  isRealtime?: boolean;
}

const SimpleSemanticPanel: React.FC<SimpleSemanticPanelProps> = ({ semanticData, isVisible, isRealtime = false }) => {
  if (!isVisible) return null;
  
  // Get memory status from store for enhanced contextual information
  const { memoryStatus } = useAppStore();
  
  // Datos por defecto si no hay semanticData
  const defaultData: SemanticData = {
    keywords: [],
    topic: 'Esperando entrada...',
    sentiment: 'neutral',
    contextualSimilarity: 0,
    episodicSimilarity: 0,
    vectorSimilarity: 0,
    confidence: 0
  };
  
  const data = semanticData || defaultData;
  
  // Enhanced status based on memory system
  const memoryActive = memoryStatus?.critical_thinking_enabled || false;
  const totalMemoryItems = memoryStatus ? 
    Object.values(memoryStatus.category_stats || {}).reduce((total: number, cat: any) => total + (cat.total_items || 0), 0) : 0;

  return (
    <div className="w-64 sm:w-72 md:w-80 lg:w-96 bg-gray-900/90 backdrop-blur-md border-l border-gray-700 p-2 sm:p-3 md:p-4 h-screen overflow-y-auto flex-shrink-0">
      <div className="space-y-2 sm:space-y-3 md:space-y-4">
        {/* Header */}
        <div className="flex items-center space-x-1 sm:space-x-2 mb-2 sm:mb-3 md:mb-4">
          <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full ${isRealtime ? 'bg-green-500 animate-ping' : 'bg-blue-500 animate-pulse'}`} />
          <h3 className={`text-sm sm:text-base md:text-lg font-semibold ${ isRealtime ? 'text-green-400' : 'text-blue-400'}`} style={{ fontSize: 'clamp(0.875rem, 3vw, 1.125rem)' }}>
            💭 {isRealtime ? 'Pensando...' : 'Mi Reflexión'}
          </h3>
        </div>

        {/* Topic Analysis */}
        <div className="space-y-3">
          <div>
            <div className="text-purple-400 font-medium mb-1 sm:mb-2 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>De qué estamos hablando:</div>
            <div className="bg-purple-900/30 border border-purple-500/30 px-2 sm:px-3 py-1 sm:py-2 rounded-lg">
              <span className="text-purple-300 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>{data.topic}</span>
            </div>
          </div>

          {/* Keywords */}
          {data.keywords.length > 0 && (
            <div>
              <div className="text-green-400 font-medium mb-1 sm:mb-2 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>Palabras importantes:</div>
              <div className="flex flex-wrap gap-1 sm:gap-2">
                {data.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="bg-green-900/30 border border-green-500/30 text-green-300 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-xs"
                    style={{ fontSize: 'clamp(0.625rem, 2vw, 0.75rem)' }}
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sentiment */}
          <div>
            <div className="text-orange-400 font-medium mb-1 sm:mb-2 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>Sentimiento:</div>
            <div className="bg-orange-900/30 border border-orange-500/30 px-2 sm:px-3 py-1 sm:py-2 rounded-lg">
              <span className="text-orange-300 capitalize text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>{data.sentiment}</span>
            </div>
          </div>

          {/* Neural Activity Indicator */}
          <div className="mt-3 sm:mt-4 md:mt-6 pt-2 sm:pt-3 md:pt-4 border-t border-gray-600">
            <div className="text-gray-400 text-xs sm:text-sm mb-1 sm:mb-2" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>Mi estado:</div>
            <div className="flex items-center space-x-1 sm:space-x-2">
              <div className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${
                isRealtime ? 'bg-green-500 animate-ping' : 'bg-blue-500 animate-pulse'
              }`} />
              <span className={`text-xs sm:text-sm ${
                isRealtime ? 'text-green-300' : 'text-blue-300'
              }`} style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
                {isRealtime ? 'PENSANDO' : 'REFLEXIONANDO'}
              </span>
            </div>
          </div>

          {/* Métricas de Similitud */}
          <div className="space-y-2 sm:space-y-3 mt-2 sm:mt-3 md:mt-4">
            <div className="text-cyan-400 font-medium mb-1 sm:mb-2 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)' }}>🔍 Cómo lo entiendo:</div>
            
            {/* Similitud Contextual */}
            <div className="space-y-1 sm:space-y-2">
              <div className="flex justify-between text-xs sm:text-sm" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
                <span className="text-cyan-300">Contexto:</span>
                <span className="text-cyan-200">{data.contextualSimilarity.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 sm:h-2 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-cyan-400 h-1.5 sm:h-2 rounded-full transition-all duration-700 ease-out"
                  style={{ 
                    width: `${data.contextualSimilarity}%`,
                    transform: 'translateX(0)',
                    animation: isRealtime ? 'pulse 1.5s ease-in-out infinite' : 'none'
                  }}
                />
              </div>
            </div>

            {/* Similitud Episódica */}
            <div className="space-y-1 sm:space-y-2">
              <div className="flex justify-between text-xs sm:text-sm" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
                <span className="text-purple-300">Memoria:</span>
                <span className="text-purple-200">{data.episodicSimilarity.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 sm:h-2 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-purple-400 h-1.5 sm:h-2 rounded-full transition-all duration-800 ease-out"
                  style={{ 
                    width: `${data.episodicSimilarity}%`,
                    transform: 'translateX(0)',
                    animation: isRealtime ? 'pulse 1.8s ease-in-out infinite' : 'none'
                  }}
                />
              </div>
            </div>

            {/* Similitud Vectorial */}
            <div className="space-y-1 sm:space-y-2">
              <div className="flex justify-between text-xs sm:text-sm" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
                <span className="text-pink-300">Significado:</span>
                <span className="text-pink-200">{data.vectorSimilarity.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 sm:h-2 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-pink-500 to-pink-400 h-1.5 sm:h-2 rounded-full transition-all duration-900 ease-out"
                  style={{ 
                    width: `${data.vectorSimilarity}%`,
                    transform: 'translateX(0)',
                    animation: isRealtime ? 'pulse 2.1s ease-in-out infinite' : 'none'
                  }}
                />
              </div>
            </div>

            {/* Confianza General */}
            <div className="space-y-1 sm:space-y-2 pt-1 sm:pt-2 border-t border-gray-600">
              <div className="flex justify-between text-xs sm:text-sm" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
                <span className="text-yellow-300 font-medium">Confianza:</span>
                <span className="text-yellow-200 font-medium">{data.confidence.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2 sm:h-3 overflow-hidden">
                <div 
                  className={`h-2 sm:h-3 rounded-full transition-all duration-1000 ease-out ${
                    data.confidence > 80 ? 'bg-gradient-to-r from-green-500 to-green-400' :
                    data.confidence > 60 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' :
                    'bg-gradient-to-r from-red-500 to-red-400'
                  }`}
                  style={{ 
                    width: `${data.confidence}%`,
                    transform: 'translateX(0)',
                    animation: isRealtime ? 'glow 2s ease-in-out infinite' : 'none',
                    boxShadow: isRealtime ? `0 0 ${window.innerWidth < 640 ? '5px' : '10px'} ${data.confidence > 80 ? '#10b981' : data.confidence > 60 ? '#f59e0b' : '#ef4444'}` : 'none'
                  }}
                />
              </div>
            </div>
          </div>

          {/* Memory Status Indicator */}
          <div className="mt-2 sm:mt-3 p-2 bg-gray-800/30 border border-gray-600/50 rounded-lg">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Mi memoria:</span>
              <div className="flex items-center gap-1">
                <div className={`w-1.5 h-1.5 rounded-full ${memoryActive ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`} />
                <span className={`text-xs ${memoryActive ? 'text-green-300' : 'text-yellow-300'}`}>
                  {memoryActive ? 'Activo' : 'Inactivo'}
                </span>
              </div>
            </div>
            {totalMemoryItems > 0 && (
              <div className="mt-1 text-xs text-gray-500">
                {totalMemoryItems} elementos en memoria
              </div>
            )}
          </div>

          {/* AI Insight */}
          <div className="mt-2 sm:mt-3 md:mt-4 p-2 sm:p-3 bg-gray-800/50 border border-gray-600 rounded-lg">
            <div className="text-gray-300 text-xs sm:text-sm" style={{ fontSize: 'clamp(0.625rem, 2vw, 0.875rem)' }}>
              <span className={`font-medium ${isRealtime ? 'text-green-400' : 'text-blue-400'}`}>
                {isRealtime ? '🔮 Lo que creo que vienes a contarme:' : '💡 Lo que entiendo:'}
              </span>
              <div className="mt-1 leading-tight">
                {isRealtime 
                  ? `Tratando de entender lo que me vas a decir... ${data.confidence.toFixed(0)}% seguro`
                  : `Creo que me hablas sobre ${data.topic.toLowerCase()}`
                }
                {memoryActive && totalMemoryItems > 0 && (
                  <div className="mt-1 text-gray-400">
                    Revisando {totalMemoryItems} cosas que tengo guardadas
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleSemanticPanel;

// Estilos CSS para animaciones personalizadas
const styles = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  @keyframes glow {
    0%, 100% { 
      filter: brightness(1) saturate(1);
      transform: scaleY(1);
    }
    50% { 
      filter: brightness(1.2) saturate(1.3);
      transform: scaleY(1.05);
    }
  }
`;

// Inyectar estilos si no existen
if (typeof document !== 'undefined' && !document.getElementById('neural-animations')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'neural-animations';
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}