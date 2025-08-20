import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import svgr from 'vite-plugin-svgr';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    svgr({
      svgrOptions: {
        exportType: 'named',
      }
    }),
  ],
  server: {
    proxy: {
      // any request starting with "/game" will be forwarded to the backend API server.
      '/game': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,  
      }
    }
  }
})
