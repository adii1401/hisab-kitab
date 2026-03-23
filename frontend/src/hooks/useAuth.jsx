import { createContext, useContext, useState } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => { 
    try { 
      return JSON.parse(localStorage.getItem('user')) 
    } catch { 
      return null 
    } 
  })

  const login = async (email, password) => {
    const form = new URLSearchParams()
    // FastAPI/OAuth2 usually expects 'username', which you have correctly
    form.append('username', email) 
    form.append('password', password)

    // 1. Get the token
    const { data } = await api.post('/auth/login', form, { 
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' } 
    })

    // 2. Save token FIRST
    localStorage.setItem('token', data.access_token)

    // 3. CRITICAL: Manually set the header for the next immediate call
    // This ensures '/auth/me' doesn't fail with a 401
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

    try {
      // 4. Get user details
      const me = await api.get('/auth/me')
      localStorage.setItem('user', JSON.stringify(me.data))
      setUser(me.data)
      return me.data
    } catch (err) {
      // If fetching 'me' fails, clean up to prevent a half-logged-in state
      logout()
      throw err
    }
  }

  const logout = () => { 
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    // Clear the global axios header
    delete api.defaults.headers.common['Authorization']
    setUser(null) 
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)