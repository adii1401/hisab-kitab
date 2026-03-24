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
    form.append('username', email) 
    form.append('password', password)

    // 1. Send login request. The backend will now attach the secure HttpOnly cookie automatically.
    await api.post('/auth/login', form, { 
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' } 
    })

    // NOTE: We no longer do localStorage.setItem('token', ...) !
    // The browser securely holds the token in the background immune to hackers.

    try {
      // 2. Fetch user details (the browser automatically sends the cookie here)
      const me = await api.get('/auth/me')
      localStorage.setItem('user', JSON.stringify(me.data))
      setUser(me.data)
      return me.data
    } catch (err) {
      // If fetching 'me' fails, force a clean logout
      await logout()
      throw err
    }
  }

  const logout = async () => { 
    try {
      // Tell backend to destroy the secure cookie
      await api.post('/auth/logout')
    } catch (err) {
      console.error("Logout error", err)
    } finally {
      localStorage.removeItem('user')
      setUser(null) 
      window.location.href = '/login'
    }
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)