
import React from 'react';
import TraditionalChat from './components/chat/TraditionalChat';
import { FileViewer } from './components/file-manager/FileViewer';
import { SmartCategorizer } from './components/memory/SmartCategorizer';
import SemanticAnalysisPanel from './components/ui/SemanticAnalysisPanel';

function App() {
  return (
    <div className="relative w-full h-screen overflow-hidden bg-gray-900 flex text-white">
      
      {/* Panel Izquierdo - Gestor de Memoria AgenteIng */}
      <aside className="w-96 h-full flex-shrink-0 bg-gray-800 border-r border-gray-700">
        <FileViewer />
      </aside>

      {/* Área Principal de Contenido */}
      <main className="flex-1 h-full relative bg-gray-900">
        <TraditionalChat />
      </main>

      {/* Panel de Análisis Semántico */}
      <div className="absolute bottom-4 right-4 z-50 max-w-sm">
        <SemanticAnalysisPanel />
      </div>

      {/* Modal de Categorización Inteligente */}
      <SmartCategorizer />

    </div>
  );
}

export default App;
