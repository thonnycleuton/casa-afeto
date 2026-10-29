/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
  test: {
    globals: true,
    environment: 'happy-dom',
  },
  // In production, API is served via Nginx reverse proxy on the same domain.
  // The frontend API endpoints already include the full path (e.g., '/api/v1/products'),
  // so the base URL should be empty. Nginx proxies /api/ to the backend container.
  // Override with VITE_API_BASE_URL env var if needed (e.g., for custom setups).
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
      process.env.VITE_API_BASE_URL || '',
    ),
  },
})
