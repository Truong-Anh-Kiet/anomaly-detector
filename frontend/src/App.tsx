import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/services/authStore'
import { useNotifications } from '@/services/notificationsStore'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import LoginPage from '@/pages/Login'
import RegisterPage from '@/pages/Register'
import AnomaliesPage from '@/pages/Anomalies'
import AuditLogsPage from '@/pages/AuditLogs'
import SettingsPage from '@/pages/Settings'
import { Users } from '@/pages/Users'
import { NotificationListener } from '@/components/NotificationListener'
import { ToastContainer } from '@/components/ui'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loadUser } = useAuthStore()

  useEffect(() => {
    if (!user) {
      loadUser()
    }
  }, [user, loadUser])

  if (user === null && !localStorage.getItem('access_token')) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  const { toasts } = useNotifications()
  const { removeToast } = useNotifications()

  return (
    <>
      <NotificationListener />
      <ToastContainer
        toasts={toasts}
        onClose={(id) => removeToast(id)}
      />
      <Routes>
        {/* Auth Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="users" element={<Users />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
