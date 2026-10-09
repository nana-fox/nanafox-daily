import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../site/reader',
    emptyOutDir: true,
    manifest: 'manifest.json',
    rollupOptions: { input: 'src/main.jsx' },
  },
});
