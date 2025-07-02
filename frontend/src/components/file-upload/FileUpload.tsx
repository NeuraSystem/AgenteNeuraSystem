import React, { useState, useRef, useCallback } from 'react';
import { useAppStore } from '../../stores/appStore';
import { Document } from '../../types';

interface FileUploadProps {
  onUploadComplete?: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [uploadStatus, setUploadStatus] = useState<{ [key: string]: 'uploading' | 'success' | 'error' }>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addDocument, updateNeuralActivity, uploadAndAnalyzeFile } = useAppStore();

  const acceptedTypes = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/plain': '.txt',
    'text/markdown': '.md'
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  };

  const handleFiles = async (files: File[]) => {
    updateNeuralActivity({
      memory_access: 0.8,
      thinking_state: 'processing'
    });

    for (const file of files) {
      const fileId = `${file.name}-${Date.now()}`;
      
      // Validate file type
      if (!Object.keys(acceptedTypes).includes(file.type) && !file.name.match(/\.(pdf|docx|xlsx|txt|md)$/i)) {
        setUploadStatus(prev => ({ ...prev, [fileId]: 'error' }));
        continue;
      }

      setUploadStatus(prev => ({ ...prev, [fileId]: 'uploading' }));
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));

      try {
        // Use the store function instead of direct API call
        await uploadAndAnalyzeFile(file);
        setUploadStatus(prev => ({ ...prev, [fileId]: 'success' }));
        setUploadProgress(prev => ({ ...prev, [fileId]: 100 }));
      } catch (error) {
        console.error('Upload error:', error);
        setUploadStatus(prev => ({ ...prev, [fileId]: 'error' }));
      }
    }

    updateNeuralActivity({
      memory_access: 0.2,
      thinking_state: 'idle'
    });

    // Auto-close after successful uploads
    setTimeout(() => {
      onUploadComplete?.();
    }, 2000);
  };

  // Note: Upload logic moved to uploadAndAnalyzeFile in the store

  const getFileType = (filename: string): Document['type'] => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'pdf';
      case 'docx': return 'docx';
      case 'xlsx': return 'xlsx';
      case 'txt': return 'txt';
      case 'md': return 'md';
      default: return 'txt';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="glass-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <svg className="w-5 h-5 text-brain-memory" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
          <span>Subir Documentos</span>
        </h3>
        
        <div className="text-xs text-gray-400">
          PDF, DOCX, XLSX, TXT, MD
        </div>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-300
          ${isDragging 
            ? 'border-brain-memory bg-brain-memory/10 scale-105' 
            : 'border-gray-600 hover:border-brain-memory/50 hover:bg-brain-memory/5'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={Object.values(acceptedTypes).join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <div className="space-y-3">
          <div className={`
            w-16 h-16 mx-auto rounded-full flex items-center justify-center transition-all duration-300
            ${isDragging ? 'bg-brain-memory text-white scale-110' : 'bg-brain-memory/20 text-brain-memory'}
          `}>
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          
          <div>
            <p className="text-white font-medium">
              {isDragging ? 'Suelta los archivos aquí' : 'Arrastra archivos aquí'}
            </p>
            <p className="text-gray-400 text-sm mt-1">
              o haz clic para seleccionar archivos
            </p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-1 text-xs">
            {Object.values(acceptedTypes).map((ext) => (
              <span key={ext} className="px-2 py-1 bg-gray-700/50 rounded text-gray-300">
                {ext.replace('.', '').toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-white">Progreso de subida:</h4>
          {Object.entries(uploadProgress).map(([fileId, progress]) => {
            const filename = fileId.split('-')[0];
            const status = uploadStatus[fileId];
            
            return (
              <div key={fileId} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-300 truncate flex-1">{filename}</span>
                  <div className="flex items-center space-x-2">
                    {status === 'uploading' && (
                      <span className="text-brain-processing">{Math.round(progress)}%</span>
                    )}
                    {status === 'success' && (
                      <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                    {status === 'error' && (
                      <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>
                
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      status === 'success' ? 'bg-green-500' :
                      status === 'error' ? 'bg-red-500' :
                      'bg-brain-memory'
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Instructions */}
      <div className="text-xs text-gray-500 space-y-1 border-t border-gray-700/50 pt-4">
        <p>• Los documentos se procesarán automáticamente para búsqueda semántica</p>
        <p>• Tamaño máximo: 10MB por archivo</p>
        <p>• Los archivos Excel se analizarán con IA para mejor comprensión</p>
      </div>
    </div>
  );
};

export default FileUpload;