/**
 * Main Layout Component
 * Includes sidebar navigation, header, and main content area
 */

import { Outlet, useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/services/authStore'
import { useTheme } from '@/services/themeStore'
import {
  LayoutDashboard,
  AlertCircle,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  Users,
  Moon,
  Sun,
} from 'lucide-react'
import { useState, useEffect } from 'react'

export default function Layout() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { setTheme, isDark, initializeTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    initializeTheme()
  }, [initializeTheme])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const navigationItems = [
    { label: 'Dashboard', icon: LayoutDashboard, href: '/', role: ['admin', 'analyst', 'auditor', 'guest'] },
    { label: 'Anomalies', icon: AlertCircle, href: '/anomalies', role: ['admin', 'analyst', 'auditor'] },
    { label: 'Audit Logs', icon: BarChart3, href: '/audit-logs', role: ['admin', 'auditor'] },
    { label: 'Users', icon: Users, href: '/users', role: ['admin'] },
    { label: 'Settings', icon: Settings, href: '/settings', role: ['admin'] },
  ]

  const visibleItems = navigationItems.filter((item) =>
    user?.role ? item.role.includes(user.role) : false
  )

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow sticky top-0 z-40">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
            >
              {sidebarOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
            <Link to="/" className="flex items-center gap-2">
              <AlertCircle className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Anomaly Detector</h1>
            </Link>
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setTheme(isDark ? 'light' : 'dark')}
              className="p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            {user && (
              <>
                <div className="text-right">
                  <p className="font-medium text-gray-900">
                    <span className="hidden sm:inline">{user.full_name}</span>
                    <span className="sm:hidden">{user.username}</span>
                  </p>
                  <p className="text-sm text-gray-500 capitalize">{user.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
            <nav className="p-4 space-y-2">
              {visibleItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </nav>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-600">
          <p>&copy; 2026 Anomaly Detector. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
