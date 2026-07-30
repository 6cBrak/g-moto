import axios from 'axios'
import { useAuthStore } from '../store/authStore'

export const apiClient = axios.create({
  baseURL: '/api',
})

apiClient.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshPromise = null

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    if (response?.status !== 401 || config._retry) {
      throw error
    }
    const { refreshToken, setTokens, logout } = useAuthStore.getState()
    if (!refreshToken) {
      throw error
    }

    config._retry = true
    try {
      refreshPromise ??= axios
        .post('/api/auth/refresh/', { refresh: refreshToken })
        .finally(() => {
          refreshPromise = null
        })
      const { data } = await refreshPromise
      setTokens(data.access, refreshToken)
      config.headers.Authorization = `Bearer ${data.access}`
      return apiClient(config)
    } catch (refreshError) {
      logout()
      throw refreshError
    }
  },
)
