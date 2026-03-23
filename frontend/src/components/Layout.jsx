import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦' }, // Changed to '/' to match your App.jsx index
  { section: 'Operations' },
  // UPDATED: Changed from /trips to /invoices
  { to: '/invoices', label: 'Invoices', icon: '📄' }, 
  { to: '/rates', label: 'Daily Rates', icon: '◈' },
  { to: '/payments', label: 'Payments', icon: '◎' },
  { section: 'Masters' },
  { to: '/vendors', label: 'Vendors', icon: '◉' },
  { to: '/mills', label: 'Mills', icon: '⬡' },
  { section: 'Reports' },
  { to: '/ledger', label: 'Ledger', icon: '≡' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Hisab Kitab</h1>
          <p>Trading Management</p>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((item, i) =>
            item.section
              ? <div key={i} className="nav-section">{item.section}</div>
              : <NavLink 
                  key={item.to} 
                  to={item.to} 
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <span style={{ fontSize: '1rem', lineHeight: 1 }}>{item.icon}</span>
                  {item.label}
                </NavLink>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{user?.full_name?.[0] || 'A'}</div>
            <div className="sidebar-user-info">
              <p>{user?.full_name || 'Admin'}</p>
              <span>{user?.role}</span>
            </div>
            <button 
              className="logout-btn" 
              onClick={() => { logout(); navigate('/login') }} 
              title="Logout"
            >
              ✕
            </button>
          </div>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}