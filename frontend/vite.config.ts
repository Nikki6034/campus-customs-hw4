import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Proxy the API and the product photographs to the FastAPI backend so the app
// can use relative paths (the database stores relative image paths).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/images': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
