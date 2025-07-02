import React, { useState } from 'react';
import { useAppStore } from '../../stores/appStore';

const MultitaskingPanel: React.FC = () => {
  const { isMultitasking, activeInteractions, addInteraction, removeInteraction } = useAppStore();
  const [isExpanded, setIsExpanded] = useState(false);

  const interactions = [
    { id: 'voice', label: 'Voz', icon: '🎤', color: 'text-brain-input' },
    { id: 'text', label: 'Texto', icon: '💬', color: 'text-brain-processing' },
    { id: 'file', label: 'Archivos', icon: '📁', color: 'text-brain-memory' },
    { id: 'search', label: 'Búsqueda', icon: '🔍', color: 'text-brain-output' }
  ];

  const toggleInteraction = (interactionId: string) => {
    if (activeInteractions.includes(interactionId)) {
      removeInteraction(interactionId);
    } else {
      addInteraction(interactionId);
    }
  };

  return (
    <div className="glass-panel p-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center space-x-2 text-sm w-full"
      >
        <span className="text-brain-processing">⚡</span>
        <span className="text-white">Multitarea</span>
        <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-2">
          {interactions.map((interaction) => {
            const isActive = activeInteractions.includes(interaction.id);
            return (
              <button
                key={interaction.id}
                onClick={() => toggleInteraction(interaction.id)}
                className={`
                  flex items-center space-x-2 w-full p-2 rounded transition-all text-xs
                  ${isActive 
                    ? 'bg-white/20 border border-white/30' 
                    : 'bg-black/20 border border-white/10 hover:bg-white/10'
                  }
                `}
              >
                <span className="text-base">{interaction.icon}</span>
                <span className={interaction.color}>{interaction.label}</span>
                {isActive && (
                  <div className="ml-auto w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                )}
              </button>
            );
          })}
          
          {activeInteractions.length > 1 && (
            <div className="mt-2 pt-2 border-t border-white/20">
              <div className="text-xs text-brain-processing">
                {activeInteractions.length} interacciones activas
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MultitaskingPanel;