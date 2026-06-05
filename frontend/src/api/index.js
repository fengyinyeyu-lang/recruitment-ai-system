import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 300000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || ''
    const message = detail || error.message || '请求失败'
    const isLoginRequest = error.config?.url?.includes('/auth/login')

    if (status === 401) {
      // 登录请求的 401 是"用户名或密码错误"，不要清除 token 或重定向
      if (isLoginRequest) {
        ElMessage.error(message)
      } else {
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      }
    } else if (status === 403) {
      ElMessage.error(detail || '没有权限执行此操作')
    } else if (status === 404) {
      ElMessage.error(detail || '请求的资源不存在')
    } else if (status === 500) {
      ElMessage.error(detail || '服务器内部错误')
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

// 认证相关 API
export const authAPI = {
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  getMe: () => request.get('/auth/me')
}

// 数据概览 API
export const dataAPI = {
  getOverview: () => request.get('/data/overview'),
  getJobs: (params) => request.get('/data/jobs', { params }),
  getFilters: () => request.get('/data/filters')
}

// 可视化 API
export const vizAPI = {
  getSalary: () => request.get('/visualization/salary'),
  getCitySalary: () => request.get('/visualization/city-salary'),
  getEducation: () => request.get('/visualization/education'),
  getExperienceSalary: () => request.get('/visualization/experience-salary'),
  getPositionDemand: () => request.get('/visualization/position-demand'),
  getWordCloud: (data) => request.post('/visualization/wordcloud', data),
  getCityDemand: () => request.get('/visualization/city-demand'),
  getIndustry: () => request.get('/visualization/industry')
}

// 机器学习 API
export const mlAPI = {
  kmeans: (data) => request.post('/ml/kmeans', data),
  nnTrain: (data) => request.post('/ml/nn-train', data),
  nnProgress: (taskId) => request.get(`/ml/nn-progress/${taskId}`),
  nnPredict: (data) => request.post('/ml/nn-predict', data),
  salaryPredict: (data) => request.post('/ml/salary-predict', data)
}

// AI 助手 API
export const aiAPI = {
  chat: (data) => request.post('/ai/chat', data),
  ragChat: (data) => request.post('/ai/rag-chat', data),
  agentChat: (data) => request.post('/ai/agent-chat', data),
  agentChatStream: (data) => fetch('/api/ai/agent-chat-stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(data)
  }),
  getFollowup: (params) => request.get('/ai/followup', { params }),
  rebuildRag: () => request.post('/ai/rebuild-rag')
}

// 简历匹配 API
export const resumeAPI = {
  upload: (formData) => request.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  recommend: (params) => request.post('/resume/recommend', null, { params })
}

// 企业画像 API
export const companyAPI = {
  getList: () => request.get('/company/list'),
  getProfile: (name) => request.get('/company/profile', { params: { name } })
}

// 报告导出 API
export const reportAPI = {
  generate: (data) => request.post('/report/generate', data)
}

export default request
