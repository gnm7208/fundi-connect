import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  ClipboardList,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Search,
  Settings,
  Shield,
  User as UserIcon,
  Wallet,
} from 'lucide-react'

import { DemoBanner } from '@/components/layout/DemoBanner'
import { NotificationBell } from '@/components/layout/NotificationBell'
import { Avatar, Button } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import type { Role } from '@/lib/types'

interface NavItem {
  to: string
  label: string
  icon: typeof Search
  roles: Role[]
}

const NAV: NavItem[] = [
  { to: '/find', label: 'Find', icon: Search, roles: ['customer', 'admin'] },
  { to: '/jobs', label: 'Jobs', icon: ClipboardList, roles: ['fundi'] },
  { to: '/bookings', label: 'Bookings', icon: ClipboardList, roles: ['customer', 'admin'] },
  { to: '/requests', label: 'Requests', icon: LayoutDashboard, roles: ['customer', 'fundi', 'admin'] },
  { to: '/wallet', label: 'Wallet', icon: Wallet, roles: ['fundi'] },
  { to: '/messages', label: 'Messages', icon: MessageSquare, roles: ['customer', 'fundi', 'admin'] },
  { to: '/admin', label: 'Admin', icon: Shield, roles: ['admin'] },
]

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuWrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    const onPointerDown = (event: MouseEvent) => {
      if (!menuWrap.current?.contains(event.target as Node)) setMenuOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [menuOpen])

  const items = user ? NAV.filter((item) => item.roles.includes(user.role)) : []

  async function handleLogout() {
    setMenuOpen(false)
    await logout()
    navigate('/')
  }

  return (
    <div className="shell">
      <DemoBanner />
      <header className="topbar">
        <Link to={user ? '/dashboard' : '/'} className="brand">
          <span className="brand-mark">F</span>
          <span>Fundi Connect</span>
        </Link>

        {user && (
          <nav className="topbar-nav" aria-label="Primary">
            <NavLink to="/dashboard" className="nav-link">
              Dashboard
            </NavLink>
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} className="nav-link">
                {item.label}
              </NavLink>
            ))}
          </nav>
        )}

        <span className="topbar-spacer" />

        <div className="topbar-actions">
          {user ? (
            <>
              <NotificationBell />
              <div className="menu-wrap" ref={menuWrap}>
                <button
                  className="icon-btn"
                  onClick={() => setMenuOpen((open) => !open)}
                  aria-label="Account menu"
                  aria-expanded={menuOpen}
                  style={{ width: 34, height: 34 }}
                >
                  <Avatar name={user.full_name} src={user.avatar_url} size="sm" />
                </button>

                {menuOpen && (
                  <div className="menu">
                    <div className="menu-head row">
                      <Avatar name={user.full_name} src={user.avatar_url} />
                      <div style={{ minWidth: 0 }}>
                        <strong style={{ fontSize: 'var(--text-sm)' }}>{user.full_name}</strong>
                        <p className="subtle" style={{ textTransform: 'capitalize' }}>
                          {user.role}
                        </p>
                      </div>
                    </div>
                    <Link className="menu-item" to="/profile" onClick={() => setMenuOpen(false)}>
                      <UserIcon size={15} /> My profile
                    </Link>
                    <Link className="menu-item" to="/settings" onClick={() => setMenuOpen(false)}>
                      <Settings size={15} /> Account settings
                    </Link>
                    <div className="menu-sep" />
                    <button className="menu-item" onClick={handleLogout}>
                      <LogOut size={15} /> Log out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Log in
              </Button>
              <Button variant="primary" size="sm" onClick={() => navigate('/register')}>
                Get started
              </Button>
            </>
          )}
        </div>
      </header>

      <main className="main">
        <Outlet />
      </main>

      {user && (
        <nav className="bottomnav" aria-label="Primary mobile">
          <NavLink to="/dashboard">
            <LayoutDashboard size={19} />
            Home
          </NavLink>
          {items.slice(0, 3).map((item) => (
            <NavLink key={item.to} to={item.to}>
              <item.icon size={19} />
              {item.label}
            </NavLink>
          ))}
          <NavLink to="/profile">
            <UserIcon size={19} />
            Profile
          </NavLink>
        </nav>
      )}
    </div>
  )
}
