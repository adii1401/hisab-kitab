import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import toast from 'react-hot-toast'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    // STOP the browser from refreshing the page
    if (e) e.preventDefault()
    
    setLoading(true)
    
    try {
      // 1. Perform backend login
      await login(email, password)
      
      // 2. Success message
      toast.success('Welcome back!')
      
      // 3. Navigate to the root (Dashboard) 
      // replace: true removes /login from history
      navigate('/', { replace: true })
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Invalid email or password'
      toast.error(errorMsg)
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-box">
        <div className="login-header">
          <h1>Hisab Kitab</h1>
          <p>Sign in to manage your trading operations</p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="admin@hisab.com" 
              required 
              autoFocus 
              autoComplete="email"
            />
          </div>
          
          <div className="form-group" style={{ marginBottom: 24 }}>
            <label>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••" 
              required 
              autoComplete="current-password"
            />
          </div>
          
          <button 
            type="submit"
            className="btn btn-primary login-btn" 
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}