import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:5000',
      '/targets': 'http://127.0.0.1:5000',
      '/checks': 'http://127.0.0.1:5000',
      '/incidents': 'http://127.0.0.1:5000',
      '/check': 'http://127.0.0.1:5000',
    },
  },
})
