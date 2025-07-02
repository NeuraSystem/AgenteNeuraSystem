/**
 * MemoryPanel - Panel principal de gestión de memoria inteligente
 * Ubicado en el lado izquierdo, muestra categorías, archivos y alertas de manera organizada
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CategoryFolders } from './CategoryFolders';
import { ProactiveAlerts } from './ProactiveAlerts';
import { MemoryStatus } from './MemoryStatus';
import { FileList } from './FileList';
import { useAppStore } from '../../stores/appStore';

interface MemoryPanelProps {
  isVisible?: boolean;
  className?: string;
}

type PanelSection = 'categories' | 'files' | 'alerts' | 'status';

export const MemoryPanel: React.FC<MemoryPanelProps> = ({
  isVisible = true,
  className = ''
}) => {
  const [expandedSection, setExpandedSection] = useState<PanelSection | null>('categories');
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // Zustand store connections
  const {
    categories,
    proactiveAlerts,
    memoryStatus,
    documents,
    fetchCategories,
    fetchActiveAlerts,
    fetchMemoryStatus,
    fetchDocuments
  } = useAppStore();
  
  // Fetch data on component mount
  useEffect(() => {
    fetchCategories();
    fetchActiveAlerts();
    fetchMemoryStatus();
    fetchDocuments();
  }, [fetchCategories, fetchActiveAlerts, fetchMemoryStatus, fetchDocuments]);

  const toggleSection = (section: PanelSection) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
    if (!isCollapsed) {
      setExpandedSection(null);
    } else {
      setExpandedSection('categories');
    }
  };

  if (!isVisible) return null;

  const panelVariants = {
    expanded: { width: 320 },
    collapsed: { width: 60 },
  };

  const contentVariants = {
    show: { opacity: 1, x: 0 },
    hide: { opacity: 0, x: -20 },
  };

  return (
    <motion.div
      className={`bg-gray-800 border-r border-gray-700 flex flex-col h-full ${className}`}
      variants={panelVariants}
      animate={isCollapsed ? 'collapsed' : 'expanded'}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <AnimatePresence mode="wait">
          {!isCollapsed && (
            <motion.div
              variants={contentVariants}
              initial="hide"
              animate="show"
              exit="hide"
              transition={{ duration: 0.2 }}
            >
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                💫 Tu Espacio Personal
              </h2>
              <p className="text-xs text-gray-400 mt-1">
                Donde guardamos todo lo importante
              </p>
            </motion.div>
          )}
        </AnimatePresence>
        
        <button
          onClick={toggleCollapse}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-white"
          title={isCollapsed ? 'Expandir panel' : 'Contraer panel'}
        >
          <motion.div
            animate={{ rotate: isCollapsed ? 0 : 180 }}
            transition={{ duration: 0.3 }}
          >
            {isCollapsed ? '▶️' : '◀️'}
          </motion.div>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {!isCollapsed && (
            <motion.div
              className="h-full flex flex-col"
              variants={contentVariants}
              initial="hide"
              animate="show"
              exit="hide"
              transition={{ duration: 0.2, delay: 0.1 }}
            >
              {/* Sections */}
              <div className="flex-1 overflow-y-auto">
                {/* Categorías */}
                <PanelSection
                  title="🗂️ Mis Espacios"
                  isExpanded={expandedSection === 'categories'}
                  onToggle={() => toggleSection('categories')}
                  badge={categories.filter(c => c.enabled).length.toString()}
                >
                  <CategoryFolders />
                </PanelSection>

                {/* Archivos Recientes */}
                <PanelSection
                  title="📚 Lo que hemos guardado"
                  isExpanded={expandedSection === 'files'}
                  onToggle={() => toggleSection('files')}
                  badge={documents.length > 0 ? documents.length.toString() : undefined}
                  badgeColor="bg-blue-500"
                >
                  <FileList maxItems={4} />
                </PanelSection>

                {/* Alertas Proactivas */}
                <PanelSection
                  title="💡 Recordatorios"
                  isExpanded={expandedSection === 'alerts'}
                  onToggle={() => toggleSection('alerts')}
                  badge={proactiveAlerts.length > 0 ? proactiveAlerts.length.toString() : undefined}
                  badgeColor="bg-yellow-500"
                >
                  <ProactiveAlerts />
                </PanelSection>

                {/* Estado de Memoria */}
                <PanelSection
                  title="🌟 Mi Estado"
                  isExpanded={expandedSection === 'status'}
                  onToggle={() => toggleSection('status')}
                >
                  <MemoryStatus />
                </PanelSection>
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-gray-700 bg-gray-900">
                <div className="text-xs text-gray-500 space-y-1">
                  <div className="flex justify-between">
                    <span>Items guardados:</span>
                    <span className="text-blue-400 font-medium">
                      {memoryStatus ? 
                        Object.values(memoryStatus.category_stats || {}).reduce((total: number, cat: any) => total + (cat.total_items || 0), 0) : 
                        documents.length
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Estado:</span>
                    <span className={`font-medium ${
                      memoryStatus?.critical_thinking_enabled ? 'text-green-400' : 'text-yellow-400'
                    }`}>
                      {memoryStatus?.critical_thinking_enabled ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed Icons */}
        <AnimatePresence>
          {isCollapsed && (
            <motion.div
              className="p-2 space-y-3"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ delay: 0.2 }}
            >
              <CollapsedIcon 
                icon="📁" 
                tooltip="Categorías"
                onClick={() => {
                  setIsCollapsed(false);
                  setExpandedSection('categories');
                }}
              />
              <CollapsedIcon 
                icon="📄" 
                tooltip="Archivos"
                badge={documents.length > 0}
                onClick={() => {
                  setIsCollapsed(false);
                  setExpandedSection('files');
                }}
              />
              <CollapsedIcon 
                icon="🔔" 
                tooltip="Alertas"
                badge={proactiveAlerts.length > 0}
                onClick={() => {
                  setIsCollapsed(false);
                  setExpandedSection('alerts');
                }}
              />
              <CollapsedIcon 
                icon="🧠" 
                tooltip="Estado"
                onClick={() => {
                  setIsCollapsed(false);
                  setExpandedSection('status');
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

// Componente para secciones expandibles
interface PanelSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string;
  badgeColor?: string;
}

const PanelSection: React.FC<PanelSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
  badge,
  badgeColor = 'bg-blue-500'
}) => {
  return (
    <div className="border-b border-gray-700">
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-700 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-white font-medium">{title}</span>
          {badge && (
            <span className={`text-xs px-2 py-1 rounded-full text-white ${badgeColor}`}>
              {badge}
            </span>
          )}
        </div>
        
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-gray-400"
        >
          ▶️
        </motion.div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Componente para íconos cuando está colapsado
interface CollapsedIconProps {
  icon: string;
  tooltip: string;
  badge?: boolean;
  onClick: () => void;
}

const CollapsedIcon: React.FC<CollapsedIconProps> = ({
  icon,
  tooltip,
  badge,
  onClick
}) => {
  return (
    <div className="relative">
      <button
        onClick={onClick}
        className="w-10 h-10 flex items-center justify-center hover:bg-gray-700 rounded-lg transition-colors text-lg"
        title={tooltip}
      >
        {icon}
      </button>
      
      {badge && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />
      )}
    </div>
  );
};