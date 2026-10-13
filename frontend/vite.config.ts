import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import http from 'http';

const agent = new http.Agent({ keepAlive: true, maxSockets: 50 });

const proxyConfig = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    agent: agent,
  },
  '/health': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    agent: agent,
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: proxyConfig,
  },
  preview: {
    port: 5173,
    proxy: proxyConfig,
  },
});
