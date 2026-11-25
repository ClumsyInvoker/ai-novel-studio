import axios from 'axios'

// 开发期经 Vite proxy 到 127.0.0.1:8000；构建后也可配绝对地址
const client = axios.create({ baseURL: '/api' })

client.interceptors.response.use(
  r => r.data,
  e => Promise.reject(e.response?.data || { detail: e.message })
)

export default client