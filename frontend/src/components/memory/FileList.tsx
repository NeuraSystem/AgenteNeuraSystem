/**
 * FileList - Componente simplificado para mostrar archivos en el MemoryPanel
 * Integrado con el diseño elegante del panel de memoria
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../../stores/appStore';

interface FileListProps {
  categoryFilter?: string;
  maxItems?: number;
}

export const FileList: React.FC<FileListProps> = ({ 
  categoryFilter, 
  maxItems = 5 
}) => {
  const { documents, deleteDocument, isLoading } = useAppStore();

  // Filter documents by category if specified
  const filteredDocuments = categoryFilter 
    ? documents.filter(doc => doc.category === categoryFilter)
    : documents;

  // Limit number of items shown
  const displayedDocuments = filteredDocuments.slice(0, maxItems);
  const remainingCount = filteredDocuments.length - maxItems;

  const getFileIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'pdf': return '📄';
      case 'docx': 
      case 'doc': return '📝';
      case 'xlsx':
      case 'xls': return '📊';
      case 'txt': return '📋';
      case 'pptx':
      case 'ppt': return '📊';
      default: return '📁';
    }
  };

  const getStatusIndicator = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'ready': 
      case 'processed': return { icon: '✅', color: 'text-green-400' };
      case 'processing': return { icon: '🔄', color: 'text-yellow-400' };
      case 'error': return { icon: '😅', color: 'text-red-400' };
      default: return { icon: '📝', color: 'text-gray-400' };
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-gray-700/50 rounded-lg p-3 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-gray-600 rounded" />
              <div className="flex-1">
                <div className="h-3 bg-gray-600 rounded w-3/4 mb-1" />
                <div className="h-2 bg-gray-600 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (displayedDocuments.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        <div className="text-2xl mb-2">📂</div>
        <p className="text-sm">Aún no hemos guardado nada</p>
        {categoryFilter && (
          <p className="text-xs mt-1">en este espacio</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {displayedDocuments.map((doc, index) => {
        const statusInfo = getStatusIndicator(doc.status);
        
        return (
          <motion.div
            key={doc.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-gray-700/50 hover:bg-gray-700 rounded-lg p-3 transition-colors group"
          >
            <div className="flex items-center gap-3">
              {/* File Icon */}
              <div className="text-lg flex-shrink-0">
                {getFileIcon(doc.type)}
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium text-white truncate" title={doc.name}>
                    {doc.name}
                  </h4>
                  <div className={`text-xs ${statusInfo.color}`}>
                    {statusInfo.icon}
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-400 uppercase">
                    {doc.type || 'archivo'}
                  </span>
                  {doc.summary && (
                    <>
                      <span className="text-gray-500">•</span>
                      <span className="text-xs text-gray-500 truncate flex-1">
                        {doc.summary}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => deleteDocument(doc.id)}
                  className="p-1 text-gray-400 hover:text-red-400 transition-colors text-sm"
                  title="Quitar de aquí"
                >
                  🗑️
                </button>
              </div>
            </div>
          </motion.div>
        );
      })}

      {/* Show remaining count if there are more files */}
      {remainingCount > 0 && (
        <div className="text-center py-2">
          <span className="text-xs text-gray-500">
            y {remainingCount} cosa{remainingCount !== 1 ? 's' : ''} más
          </span>
        </div>
      )}
    </div>
  );
};