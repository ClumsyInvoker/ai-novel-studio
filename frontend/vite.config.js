import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    // 允许经 Cloudflare 隧道从公网域名访问（否则 Vite 拦截外域 Host）
    allowedHosts: ['novel.invokerz.xyz'],
    // 开发期把 /api 代理到后端，避免跨域。
    // 后端端口可用环境变量 NOVEL_BACKEND_PORT 覆盖，默认 8778（避开 8000/8080/3000 等热门端口）。
    proxy: {
      '/api': { target: `http://127.0.0.1:${process.env.NOVEL_BACKEND_PORT || '8778'}`, changeOrigin: true }
    }
  }
})