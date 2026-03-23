import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // 1. SET BASE TO RELATIVE PATHS
  // Essential for Nginx to find index-BAoRl-qS.js in the /assets folder
  base: './',

  // 2. CONFIGURE THE BUILD OUTPUT
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
  },

  // 3. CONFIGURE THE DEV SERVER
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        // Points to the service name defined in docker-compose
        target: 'http://hisab_backend:8000',
        changeOrigin: true,
        // Ensure /api/login becomes /login when it hits FastAPI
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})