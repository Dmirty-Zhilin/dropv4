import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1'

const api = axios.create({
  baseURL: API_BASE,
})

api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - logout
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const login = async (username, password) => {
  const response = await api.post('/auth/login', { username, password })
  return response.data
}

export const register = async (username, password, email) => {
  const response = await api.post('/auth/register', { username, password, email })
  return response.data
}

export const analyzeDomains = async (domains) => {
  const response = await api.post('/domains/analyze', { domains })
  return response.data
}

export const llmAnalyzeDomains = async (domains) => {
  const response = await api.post('/domains/llm-analyze', { domains })
  return response.data
}

export const getDomains = async (page = 1, per_page = 10) => {
  const response = await api.get(`/domains?page=${page}&per_page=${per_page}`)
  return response.data
}

export const getUserReports = async (page = 1, per_page = 10) => {
  const response = await api.get(`/reports?page=${page}&per_page=${per_page}`)
  return response.data
}

export const deleteReport = async (reportId) => {
  const response = await api.delete(`/reports/${reportId}`)
  return response.data
}

export const exportReports = async (format, reportIds) => {
  const response = await api.post('/reports/export', { format, report_ids: reportIds })
  return response.data
}

export const getSettings = async () => {
  const response = await api.get('/settings')
  return response.data
}

export const updateSettings = async (settings) => {
  const response = await api.put('/settings', settings)
  return response.data
}

export const getUsers = async (page = 1, per_page = 10, search = '') => {
  const response = await api.get(`/admin/users?page=${page}&per_page=${per_page}&search=${search}`)
  return response.data
}

export const createUser = async (userData) => {
  const response = await api.post('/admin/users', userData)
  return response.data
}

export const updateUser = async (userId, userData) => {
  const response = await api.put(`/admin/users/${userId}`, userData)
  return response.data
}

export const deleteUser = async (userId) => {
  const response = await api.delete(`/admin/users/${userId}`)
  return response.data
}

export const getDomainDetail = async (domain) => {
  const response = await api.get(`/domains/${domain}`)
  return response.data
}

export const getToken = () => {
  return localStorage.getItem('token')
}

export const setToken = (token) => {
  localStorage.setItem('token', token)
}
