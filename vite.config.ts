import { defineConfig } from 'vite';
import vinext from 'vinext';
import { sites } from './scripts/vite/sites';
import './scripts/sites-env.mjs';

export default defineConfig({
  plugins: [vinext(), sites()],
  server: { host: '127.0.0.1', port: 5173 },
});
