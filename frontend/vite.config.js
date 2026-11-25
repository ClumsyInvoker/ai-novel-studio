import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    // 公网域名通过环境变量注入，如 VITE_ALLOWED_HOSTS=novel.yourdomain.com
    allowedHosts: (process.env.VITE_ALLOWED_HOSTS || '').split(',').filter(Boolean),
    // 开发期把 /api 代理到后端，避免跨域。
    // 后端端口可用环境变量 NOVEL_BACKEND_PORT 覆盖，默认 8778（避开 8000/8080/3000 等热门端口）。
    proxy: {
      '/api': { target: `http://127.0.0.1:${process.env.NOVEL_BACKEND_PORT || '8778'}`, changeOrigin: true }
    }
  }
})