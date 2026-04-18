import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:3000', changeOrigin: true },
      '/risk-map': { target: 'http://localhost:3000', changeOrigin: true },
      '/overview': { target: 'http://localhost:3000', changeOrigin: true },
      '/locations': { target: 'http://localhost:3000', changeOrigin: true },
      '/logs': { target: 'http://localhost:3000', changeOrigin: true },
      '/emissions': { target: 'http://localhost:3000', changeOrigin: true },
      '/analyze-zone': { target: 'http://localhost:3000', changeOrigin: true },
      '/search-location': { target: 'http://localhost:3000', changeOrigin: true },
      '/health': { target: 'http://localhost:3000', changeOrigin: true },
    }
  }
})
