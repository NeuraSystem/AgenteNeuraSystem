/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Paleta principal ChatIng
        'navy': {
          50: '#f0f9ff',
          100: '#e0f2fe', 
          500: '#3b82f6',
          600: '#2563eb',
          800: '#1e40af',
          900: '#1e3a8a', // Azul marino principal
        },
        'neural': {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#0a0e1f', // Fondo cósmico del cerebro
        },
        // Colores de actividad neuronal
        'brain': {
          'input': '#ef4444',     // Rojo para entrada de voz
          'processing': '#3b82f6', // Azul para procesamiento
          'output': '#10b981',    // Verde para salida
          'memory': '#f59e0b',    // Amarillo para memoria/documentos
          'idle': '#6366f1',      // Violeta para estado idle
        }
      },
      boxShadow: {
        'glow': '0 0 15px rgba(59, 130, 246, 0.3)',
        'glow-strong': '0 0 25px rgba(59, 130, 246, 0.5)',
        'neural': '0 0 20px rgba(99, 102, 241, 0.4)',
        'voice-active': '0 0 25px rgba(239, 68, 68, 0.6)',
        'voice-idle': '0 0 15px rgba(148, 163, 184, 0.3)',
      },
      animation: {
        'pulse-glow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'neural-pulse': 'neural-pulse 3s ease-in-out infinite',
        'brain-thinking': 'brain-thinking 1.5s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        'neural-pulse': {
          '0%, 100%': { 
            opacity: '0.4',
            transform: 'scale(1)',
          },
          '50%': { 
            opacity: '1',
            transform: 'scale(1.05)',
          },
        },
        'brain-thinking': {
          '0%, 100%': { 
            opacity: '0.6',
            filter: 'brightness(1)',
          },
          '50%': { 
            opacity: '1',
            filter: 'brightness(1.3)',
          },
        },
        'float': {
          '0%, 100%': { 
            transform: 'translateY(0px)',
          },
          '50%': { 
            transform: 'translateY(-10px)',
          },
        },
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}