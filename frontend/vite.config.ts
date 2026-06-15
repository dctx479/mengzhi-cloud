import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8001'
const stylesPath = resolve(__dirname, 'src/styles/variables').replace(/\\/g, '/')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "${stylesPath}";\n`,
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
})
