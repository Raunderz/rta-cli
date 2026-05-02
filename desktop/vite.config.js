import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
  },
  optimizeDeps: {
    include: ['@monaco-editor/react']
  }
});
