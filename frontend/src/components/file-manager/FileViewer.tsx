
import React, { useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { Category } from '../../types';

// =======================================================================
// Componente Principal: FileViewer
// =======================================================================

export const FileViewer: React.FC<{ className?: string }> = ({ className = '' }) => {
  const {
    categories,
    documents,
    isLoading,
    error,
    fetchCategories,
    fetchDocuments,
    uploadAndAnalyzeFile,
    deleteDocument,
  } = useAppStore();

  useEffect(() => {
    fetchCategories();
    fetchDocuments();
  }, []); // Only call once on mount - functions are now rate-limited

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        uploadAndAnalyzeFile(file);
      });
    }
  };

  return (
    <div className={`w-96 bg-gray-800 border-l border-gray-700 flex flex-col ${className}`}>
      {/* --- Header --- */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          🧠 Memoria de AgenteIng
        </h3>
        <p className="text-sm text-gray-400">Gestor de conocimiento y archivos</p>
      </div>

      {/* --- Zona de Subida de Archivos --- */}
      <div className="m-4">
        <label className="block p-6 border-2 border-dashed border-gray-600 hover:border-gray-500 rounded-lg text-center cursor-pointer transition-colors">
          <input 
            type="file" 
            multiple 
            className="hidden"
            accept=".pdf,.docx,.txt,.xlsx"
            onChange={handleFileUpload}
          />
          <div className="text-3xl mb-2">📤</div>
          <p className="text-sm text-gray-300">
            Haz clic para subir archivos
          </p>
          <p className="text-xs text-gray-500">PDF, DOCX, TXT, XLSX</p>
        </label>
      </div>

      {/* --- Indicador de Carga y Errores --- */}
      {isLoading && <LoadingSpinner text="Procesando..." />}
      {error && <ErrorMessage message={error} />}

      {/* --- Lista de Categorías y Archivos --- */}
      <div className="flex-1 overflow-y-auto px-4">
        {categories.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <>
            {categories.filter(cat => cat.enabled).map(category => (
              <CategorySection key={category.id} category={category} />
            ))}
            <AddCategoryButton />
          </>
        )}
      </div>
    </div>
  );
};

// =======================================================================
// Sub-componentes para organizar la UI
// =======================================================================

const CategorySection: React.FC<{ category: Category }> = ({ category }) => {
  const { documents, deleteDocument } = useAppStore();
  // Por ahora mostramos todos los documentos en cada categoría
  // En el futuro se filtrará por categoría cuando el backend lo soporte
  const filesInCategory = documents;

  return (
    <div className="mb-4">
      <h4 className="text-md font-bold text-blue-300 mb-2 sticky top-0 bg-gray-800 py-1">{category.displayName}</h4>
      <div className="space-y-2">
        {filesInCategory.length > 0 ? (
          filesInCategory.map(file => <FileCard key={file.id} file={file} onDelete={() => deleteDocument(file.id)} />)
        ) : (
          <p className="text-xs text-gray-500 pl-2">No hay archivos en esta categoría.</p>
        )}
      </div>
    </div>
  );
};

const FileCard: React.FC<{ file: any; onDelete: () => void }> = ({ file, onDelete }) => {
  const getFileIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf': return '📄';
      case 'docx': return '📝';
      case 'xlsx': return '📊';
      case 'txt': return '📋';
      default: return '📁';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ready': return 'text-green-400';
      case 'processing': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-gray-700 p-3 rounded-lg text-sm border border-gray-600 hover:border-gray-500 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-lg">{getFileIcon(file.type)}</span>
          <div className="flex-1 min-w-0">
            <p className="text-white font-medium truncate" title={file.name}>{file.name}</p>
            <p className="text-xs text-gray-400">{file.type.toUpperCase()}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs ${getStatusColor(file.status)}`}>
            {file.status === 'ready' ? '✓' : file.status === 'processing' ? '⏳' : '✗'}
          </span>
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-400 transition-colors p-1"
            title="Eliminar archivo"
          >
            🗑️
          </button>
        </div>
      </div>
      {file.summary && (
        <p className="text-xs text-gray-400 mt-1 truncate">{file.summary}</p>
      )}
    </div>
  );
};

const LoadingSpinner: React.FC<{ text: string }> = ({ text }) => (
  <div className="p-4 flex items-center justify-center gap-2 text-gray-400">
    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
    <span>{text}</span>
  </div>
);

const ErrorMessage: React.FC<{ message: string }> = ({ message }) => (
  <div className="m-4 p-3 bg-red-900/50 text-red-300 rounded-lg text-sm">
    <strong>Error:</strong> {message}
  </div>
);

const EmptyState: React.FC = () => (
  <div className="p-4 text-center text-gray-500 mt-8">
    <div className="text-4xl mb-2">🗂️</div>
    <p className="text-sm">La memoria está vacía.</p>
    <p className="text-xs">Sube un archivo para empezar a organizar.</p>
  </div>
);

const AddCategoryButton: React.FC = () => {
  const { categories } = useAppStore();
  const optionalCategories = categories.filter(cat => !cat.enabled);

  if (optionalCategories.length === 0) return null;

  return (
    <div className="mt-4 mb-4">
      <button className="w-full p-3 border-2 border-dashed border-gray-600 hover:border-gray-500 rounded-lg text-gray-400 hover:text-gray-300 transition-colors text-sm">
        <div className="flex items-center justify-center gap-2">
          <span>➕</span>
          <span>Agregar categoría</span>
        </div>
        <p className="text-xs mt-1">
          {optionalCategories.length} categorías disponibles
        </p>
      </button>
    </div>
  );
};
