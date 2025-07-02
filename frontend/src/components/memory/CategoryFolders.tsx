/**
 * CategoryFolders - Componente para mostrar categorías como carpetas visuales
 * Muestra iconos intuitivos y contadores de items por categoría
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../../stores/appStore';
import { AddCategoryModal } from './AddCategoryModal';

interface Category {
  id: string;
  name: string;
  displayName: string;
  description: string;
  enabled: boolean;
  icon: string;
  itemCount: number;
  color: string;
  subcategories?: any[];
}

interface CategoryFoldersProps {
  onCategorySelect?: (categoryId: string) => void;
  onAddCategory?: () => void;
}

export const CategoryFolders: React.FC<CategoryFoldersProps> = ({
  onCategorySelect,
  onAddCategory
}) => {
  // Get categories from Zustand store
  const { categories: storeCategories, memoryStatus } = useAppStore();
  const [showAddModal, setShowAddModal] = useState(false);
  
  // Map store categories to display format with icons and colors
  const categories: Category[] = storeCategories.map(cat => {
    const iconMap: { [key: string]: string } = {
      'personal': '👤',
      'familiar': '👨‍👩‍👧‍👦',
      'social': '👥',
      'laboral': '💼',
      'escolar': '🎓',
      'deportiva': '🏃‍♂️',
      'religion': '⛪'
    };
    
    const colorMap: { [key: string]: string } = {
      'personal': 'bg-blue-500',
      'familiar': 'bg-pink-500',
      'social': 'bg-green-500',
      'laboral': 'bg-orange-500',
      'escolar': 'bg-purple-500',
      'deportiva': 'bg-red-500',
      'religion': 'bg-yellow-500'
    };
    
    const categoryStats = memoryStatus?.category_stats?.[cat.name] || { total_items: 0 };
    
    return {
      ...cat,
      icon: iconMap[cat.name] || '📁',
      color: colorMap[cat.name] || 'bg-gray-500',
      itemCount: categoryStats.total_items || 0
    };
  });

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(categoryId);
    onCategorySelect?.(categoryId);
  };

  const enabledCategories = categories.filter(cat => cat.enabled);
  const disabledCategories = categories.filter(cat => !cat.enabled);

  return (
    <div className="space-y-4">
      {/* Categorías Activas */}
      <div>
        <h3 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
          💫 Espacios donde guardamos cosas
        </h3>
        
        <div className="space-y-2">
          {enabledCategories.map((category) => (
            <CategoryCard
              key={category.id}
              category={category}
              isSelected={selectedCategory === category.id}
              onClick={() => handleCategoryClick(category.id)}
            />
          ))}
        </div>
      </div>

      {/* Categorías Disponibles */}
      {disabledCategories.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            🌟 Otros espacios que puedes usar
          </h3>
          
          <div className="space-y-2">
            {disabledCategories.map((category) => (
              <CategoryCard
                key={category.id}
                category={category}
                isSelected={false}
                disabled
                onClick={() => handleCategoryClick(category.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Botón Agregar */}
      <button
        onClick={() => setShowAddModal(true)}
        className="w-full p-3 border-2 border-dashed border-gray-600 hover:border-gray-500 rounded-lg transition-colors group flex items-center justify-center gap-2 text-gray-400 hover:text-gray-300"
      >
        <span className="text-lg group-hover:scale-110 transition-transform">➕</span>
        <span className="text-sm">Crear un espacio nuevo</span>
      </button>
      
      {/* Modal para agregar categoría */}
      <AddCategoryModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          onAddCategory?.();
          console.log('Category created successfully!');
        }}
      />
    </div>
  );
};

// Componente para cada tarjeta de categoría
interface CategoryCardProps {
  category: Category;
  isSelected: boolean;
  disabled?: boolean;
  onClick: () => void;
}

const CategoryCard: React.FC<CategoryCardProps> = ({
  category,
  isSelected,
  disabled = false,
  onClick
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const cardVariants = {
    idle: { scale: 1, y: 0 },
    hover: { scale: 1.02, y: -2 },
    selected: { scale: 1.02, y: -1 }
  };

  return (
    <motion.button
      className={`w-full p-3 rounded-lg border transition-all duration-200 text-left ${
        disabled
          ? 'bg-gray-800 border-gray-700 opacity-60'
          : isSelected
          ? 'bg-blue-900 border-blue-500 shadow-lg shadow-blue-500/20'
          : 'bg-gray-700 border-gray-600 hover:bg-gray-650 hover:border-gray-500'
      }`}
      variants={cardVariants}
      animate={isSelected ? 'selected' : isHovered ? 'hover' : 'idle'}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      disabled={disabled}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-center gap-3">
        {/* Icono */}
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${
          disabled ? 'bg-gray-600' : category.color
        }`}>
          {category.icon}
        </div>

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className={`font-medium text-sm ${
              disabled ? 'text-gray-500' : 'text-white'
            }`}>
              {category.displayName}
            </h4>
            
            {!disabled && (
              <div className="flex items-center gap-2">
                {category.itemCount > 0 && (
                  <span className="text-xs bg-blue-600 text-blue-100 px-2 py-1 rounded-full">
                    {category.itemCount}
                  </span>
                )}
                {isSelected && (
                  <span className="text-blue-400 text-sm">✓</span>
                )}
              </div>
            )}
          </div>
          
          <p className={`text-xs mt-1 ${
            disabled ? 'text-gray-600' : 'text-gray-400'
          }`}>
            {category.description}
          </p>

          {disabled && (
            <div className="mt-2">
              <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">
                Activar categoría
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Indicador de actividad */}
      {!disabled && category.itemCount > 0 && (
        <div className="mt-2 flex items-center gap-1">
          <div className="flex-1 bg-gray-600 rounded-full h-1">
            <motion.div
              className={`h-1 rounded-full ${category.color}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, (category.itemCount / 50) * 100)}%` }}
              transition={{ duration: 1, delay: 0.2 }}
            />
          </div>
          <span className="text-xs text-gray-400">
            {category.itemCount > 0 ? 'Activo' : 'Vacío'}
          </span>
        </div>
      )}
    </motion.button>
  );
};