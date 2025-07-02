import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CategorySuggestion {
  category: string;
  confidence: number;
  reasoning: string;
  alternative?: string;
}

interface SmartCategorizerProps {
  isVisible: boolean;
  content: string;
  suggestions: CategorySuggestion[];
  onAccept: (category: string) => void;
  onReject: () => void;
  onCreateNew: (categoryName: string) => void;
  onDismiss: () => void;
}

export const SmartCategorizer: React.FC<SmartCategorizerProps> = ({
  isVisible,
  content,
  suggestions,
  onAccept,
  onReject,
  onCreateNew,
  onDismiss
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [showReasoning, setShowReasoning] = useState(false);

  // Reset state when component becomes visible
  useEffect(() => {
    if (isVisible && suggestions && suggestions.length > 0) {
      setSelectedCategory(suggestions[0]?.category || '');
      setIsCreatingNew(false);
      setNewCategoryName('');
      setShowReasoning(false);
    }
  }, [isVisible, suggestions]);

  // Guarda de seguridad: si no hay sugerencias, no renderizar.
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const getCategoryEmoji = (category: string) => {
    const emojis: Record<string, string> = {
      personal: '👤',
      familiar: '👨‍👩‍👧‍👦',
      social: '👥',
      laboral: '💼',
      escolar: '🎓',
      deportiva: '🏃‍♂️',
      religion: '⛪',
      salud: '🏥',
      finanzas: '💰',
      hobbies: '🎨',
      viajes: '✈️',
      tecnologia: '💻'
    };
    return emojis[category] || '📁';
  };

  const getConversationalMessage = () => {
    const messages = [
      "He estado analizando esta información y creo que encaja mejor en...",
      "Después de pensarlo, me parece que esto pertenece a...",
      "Mi intuición me dice que esto debería ir en...",
      "Basándome en el contenido, sugiero organizarlo en...",
      "¿Te parece si guardamos esto en...?"
    ];
    
    return messages[Math.floor(Math.random() * messages.length)];
  };

  const getConfidenceMessage = (confidence: number) => {
    if (confidence > 0.8) return "Estoy bastante seguro de esta categorización";
    if (confidence > 0.6) return "Me siento confiado con esta sugerencia";
    if (confidence > 0.4) return "Esta es mi mejor sugerencia, aunque no estoy 100% seguro";
    return "No estoy muy seguro, ¿podrías ayudarme a decidir?";
  };

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 }
  };

  const modalVariants = {
    hidden: { 
      opacity: 0, 
      scale: 0.8, 
      y: 50,
      rotateX: -15
    },
    visible: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      rotateX: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300
      }
    },
    exit: { 
      opacity: 0, 
      scale: 0.8, 
      y: 50,
      rotateX: 15,
      transition: { duration: 0.2 }
    }
  };

  const suggestionVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: (index: number) => ({
      opacity: 1,
      x: 0,
      transition: { delay: index * 0.1, duration: 0.3 }
    })
  };

  const topSuggestion = suggestions[0];

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={onDismiss}
        >
          <motion.div
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl shadow-2xl max-w-lg w-full border border-gray-600"
            variants={modalVariants}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-2xl">
                  🤔
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    ¿Dónde guardamos esto?
                  </h3>
                  <p className="text-sm text-gray-400">
                    {getConversationalMessage()}
                  </p>
                </div>
              </div>

              {/* Content Preview */}
              <div className="bg-gray-700 rounded-lg p-3 max-h-20 overflow-hidden">
                <p className="text-sm text-gray-300 line-clamp-3">
                  {content.length > 100 ? content.substring(0, 100) + '...' : content}
                </p>
              </div>
            </div>

            {/* Main Content */}
            <div className="p-6">
              {!isCreatingNew ? (
                <>
                  {/* Primary Suggestion */}
                  {topSuggestion && (
                    <motion.div
                      className="mb-4"
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-4 text-white">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl">
                            {getCategoryEmoji(topSuggestion.category)}
                          </span>
                          <div>
                            <h4 className="font-semibold capitalize">
                              {topSuggestion.category}
                            </h4>
                            <p className="text-sm opacity-90">
                              {getConfidenceMessage(topSuggestion.confidence)}
                            </p>
                          </div>
                          <div className="ml-auto">
                            <div className="text-right">
                              <div className="text-xs opacity-75">Confianza</div>
                              <div className="font-semibold">
                                {Math.round(topSuggestion.confidence * 100)}%
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Reasoning toggle */}
                        <button
                          onClick={() => setShowReasoning(!showReasoning)}
                          className="text-xs text-blue-200 hover:text-white transition-colors flex items-center gap-1"
                        >
                          <span>¿Por qué esta categoría?</span>
                          <motion.span
                            animate={{ rotate: showReasoning ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            ▼
                          </motion.span>
                        </button>

                        <AnimatePresence>
                          {showReasoning && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="mt-3 text-sm bg-white/10 rounded p-3"
                            >
                              {topSuggestion.reasoning}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  )}

                  {/* Alternative Suggestions */}
                  {suggestions.length > 1 && (
                    <div className="mb-4">
                      <p className="text-sm text-gray-400 mb-3">
                        O si prefieres, también podría ir en:
                      </p>
                      <div className="space-y-2">
                        {suggestions.slice(1).map((suggestion, index) => (
                          <motion.button
                            key={suggestion.category}
                            className={`w-full p-3 rounded-lg border transition-all text-left ${
                              selectedCategory === suggestion.category
                                ? 'border-blue-500 bg-blue-900/30'
                                : 'border-gray-600 bg-gray-700 hover:bg-gray-650'
                            }`}
                            variants={suggestionVariants}
                            custom={index + 1}
                            initial="hidden"
                            animate="visible"
                            onClick={() => setSelectedCategory(suggestion.category)}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-lg">
                                {getCategoryEmoji(suggestion.category)}
                              </span>
                              <div className="flex-1">
                                <div className="font-medium text-white capitalize">
                                  {suggestion.category}
                                </div>
                                <div className="text-xs text-gray-400">
                                  {Math.round(suggestion.confidence * 100)}% de confianza
                                </div>
                              </div>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Create New Category */}
                  <button
                    onClick={() => setIsCreatingNew(true)}
                    className="w-full p-3 border-2 border-dashed border-gray-600 hover:border-gray-500 rounded-lg text-gray-400 hover:text-gray-300 transition-colors flex items-center justify-center gap-2"
                  >
                    <span className="text-lg">➕</span>
                    <span className="text-sm">Crear nueva categoría</span>
                  </button>
                </>
              ) : (
                /* Create New Category Form */
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      ¿Cómo quieres llamar a esta nueva categoría?
                    </label>
                    <input
                      type="text"
                      value={newCategoryName}
                      onChange={(e) => setNewCategoryName(e.target.value)}
                      placeholder="Ej: Proyectos, Salud, Hobbies..."
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500"
                      autoFocus
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="p-6 border-t border-gray-700 flex gap-3">
              {!isCreatingNew ? (
                <>
                  <button
                    onClick={() => onAccept(selectedCategory || topSuggestion?.category || '')}
                    disabled={!selectedCategory && !topSuggestion}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                  >
                    ✅ Perfecto, guárdalo ahí
                  </button>
                  <button
                    onClick={onReject}
                    className="px-4 py-3 text-gray-400 hover:text-white transition-colors"
                  >
                    No, déjame decidir después
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setIsCreatingNew(false)}
                    className="px-4 py-3 text-gray-400 hover:text-white transition-colors"
                  >
                    Volver
                  </button>
                  <button
                    onClick={() => {
                      if (newCategoryName.trim()) {
                        onCreateNew(newCategoryName.trim());
                      }
                    }}
                    disabled={!newCategoryName.trim()}
                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                  >
                    🎯 Crear y usar esta categoría
                  </button>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};