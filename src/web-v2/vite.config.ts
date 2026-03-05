import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/battery_data.json': 'http://localhost:3000',
      '/disk_data.json': 'http://localhost:3000'
    }
  }
})
