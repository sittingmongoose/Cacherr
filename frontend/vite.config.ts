import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/store': path.resolve(__dirname, './src/store'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    host: '0.0.0.0', // Required for Docker container access
    port: 3000,
    strictPort: true, // Prevent Vite from choosing different ports
    proxy: {
      // Proxy API requests to Flask backend during development
      '/api': {
        target: 'http://localhost:5445',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
      '/health': {
        target: 'http://localhost:5445',
        changeOrigin: true,
        secure: false
      },
      // WebSocket proxy for real-time updates
      '/ws': {
        target: 'ws://localhost:5445',
        ws: true,
        changeOrigin: true,
        secure: false
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['lucide-react', 'framer-motion'],
          charts: ['recharts'],
        },
      },
    },
  },
})