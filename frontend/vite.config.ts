import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// The API has no CORS middleware, so in dev every /api call is proxied to it.
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  };
});
