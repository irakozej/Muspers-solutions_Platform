import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND = 'http://localhost:8001';

// Proxy /api and /health → backend, so the browser sees both origins as one.
// That makes the auth refresh cookie (HTTP-only, SameSite=Lax) work cleanly in dev,
// and it mirrors the typical production deployment shape.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/health': { target: BACKEND, changeOrigin: true },
    },
  },
});
