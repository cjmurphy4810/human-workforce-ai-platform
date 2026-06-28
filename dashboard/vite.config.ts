import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => ({
  // In CI the workflow sets VITE_BASE_PATH=/human-workforce-ai-platform/
  // for GitHub Pages subdirectory hosting. Locally defaults to /.
  base: process.env.VITE_BASE_PATH ?? (mode === 'production' ? '/' : '/'),
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          charts: ['recharts'],
        },
      },
    },
  },
}))
