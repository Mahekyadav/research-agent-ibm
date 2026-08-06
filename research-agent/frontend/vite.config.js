import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // Proxy every non-asset request directly to FastAPI.
    // The frontend uses no /api prefix — all API paths go straight to :8000.
    proxy: {
      '/health':              { target: 'http://localhost:8000', changeOrigin: true },
      '/stats':               { target: 'http://localhost:8000', changeOrigin: true },
      '/search':              { target: 'http://localhost:8000', changeOrigin: true },
      '/ingest':              { target: 'http://localhost:8000', changeOrigin: true },
      '/research':            { target: 'http://localhost:8000', changeOrigin: true },
      '/chat':                { target: 'http://localhost:8000', changeOrigin: true },
      '/api-info':            { target: 'http://localhost:8000', changeOrigin: true },
      '/docs':                { target: 'http://localhost:8000', changeOrigin: true },
      '/openapi.json':        { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
