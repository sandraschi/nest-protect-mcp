import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 7770,
    proxy: {
      '/api': {
        target: 'http://localhost:7771',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:7771',
        ws: true,
      },
    },
  },
})