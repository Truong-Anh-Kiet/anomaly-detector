import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Anomaly Detection Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Detect and analyze financial transaction anomalies
          </p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 px-4">
        <Outlet />
      </main>
      
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-600">
          <p>&copy; 2026 Anomaly Detector. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
