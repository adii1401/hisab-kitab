import axios from 'axios'

const api = axios.create({ 
  baseURL: '/api',
  withCredentials: true // CRITICAL: This tells Axios to automatically send the secure HttpOnly cookie!
})

// NOTICE: We deleted the api.interceptors.request block entirely!

api.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    const isLoginRequest = err.config.url.includes('/auth/login');
    
    if (!isLoginRequest) {
      localStorage.removeItem('user'); // We only clear user data now, the token is gone
      window.location.href = '/login';
    }
  }
  return Promise.reject(err)
})

export default api