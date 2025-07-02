/**
 * AddCategoryModal - Modal para crear nuevas categorías de memoria
 * Permite al usuario definir nombre, nombre visible y descripción
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../../stores/appStore';

interface AddCategoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AddCategoryModal: React.FC<AddCategoryModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    name: '',
    displayName: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { createCategory } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Validate form
      if (!formData.name.trim() || !formData.displayName.trim()) {
        throw new Error('El nombre y nombre visible son requeridos');
      }

      // Generate internal name from display name if not provided
      const internalName = formData.name.trim().toLowerCase().replace(/\s+/g, '_');
      
      await createCategory({
        name: internalName,
        displayName: formData.displayName.trim(),
        description: formData.description.trim() || `Categoría ${formData.displayName}`
      });

      // Reset form and close modal
      setFormData({ name: '', displayName: '', description: '' });
      onClose();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear la categoría');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({ name: '', displayName: '', description: '' });
      setError(null);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          <motion.div
            className="bg-gray-800 border border-gray-600 rounded-lg p-6 w-full max-w-md"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                ✨ Crear tu nuevo espacio
              </h2>
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Display Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  ¿Cómo quieres llamar a tu espacio? *
                </label>
                <input
                  type="text"
                  value={formData.displayName}
                  onChange={(e) => {
                    const displayName = e.target.value;
                    setFormData(prev => ({
                      ...prev,
                      displayName,
                      // Auto-generate internal name from display name
                      name: displayName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
                    }));
                  }}
                  placeholder="ej. Trabajo, Hobbies, Finanzas, Recetas..."
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  disabled={isSubmitting}
                  required
                />
              </div>

              {/* Internal Name (auto-generated, read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Nombre interno (generado automáticamente)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  readOnly
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-gray-400 text-sm"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Cuéntame qué vas a guardar aquí
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Por ejemplo: cosas de mi trabajo, recetas que me gustan, documentos de la casa..."
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
                  rows={3}
                  disabled={isSubmitting}
                />
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3">
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-white rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !formData.displayName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Creando...
                    </>
                  ) : (
                    'Crear mi espacio'
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};