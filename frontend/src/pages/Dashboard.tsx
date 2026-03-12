/**
 * Dashboard Page Component
 * Main overview of anomalies and system status
 */

import { useEffect } from 'react'
import { useAuthStore } from '@/services/authStore'
import { useAnomalies, useAnomalyStats } from '@/hooks'
import { LoadingSpinner, ErrorAlert, Card, CardHeader, CardBody, Badge, CategoryBadge, StatusBadge } from '@/components/ui'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertCircle, TrendingUp, CheckCircle, Clock } from 'lucide-react'
import { format } from 'date-fns'

function Dashboard() {
  const { user, loadUser } = useAuthStore()
  const { anomalies, loading: anomaliesLoading, error: anomaliesError, refetch } = useAnomalies({ limit: 50 })
  const { stats, loading: statsLoading, error: statsError } = useAnomalyStats()

  useEffect(() => {
    if (!user) {
      loadUser()
    }
    // Refresh anomalies every 30 seconds
    const interval = setInterval(refetch, 30000)
    return () => clearInterval(interval)
  }, [user, loadUser, refetch])

  const loading = anomaliesLoading || statsLoading
  const error = anomaliesError || statsError

  // Prepare data for charts
  const categoryData = stats?.distribution_by_category
    ? Object.entries(stats.distribution_by_category).map(([category, count]) => ({
        name: category.charAt(0).toUpperCase() + category.slice(1),
        value: count,
      }))
    : []

  const statusData = stats
    ? [
        { name: 'Pending Review', value: stats.pending_review, color: '#FBBF24' },
        { name: 'Confirmed', value: stats.confirmed, color: '#EF4444' },
        { name: 'False Positive', value: stats.false_positive, color: '#10B981' },
      ]
    : []

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      {user && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-6 shadow-lg">
          <h1 className="text-3xl font-bold">Welcome, {user.full_name}!</h1>
          <p className="text-blue-100 mt-2">Role: <span className="font-semibold capitalize">{user.role}</span></p>
        </div>
      )}

      {/* Error Alert */}
      {error && <ErrorAlert message={error} onDismiss={refetch} />}

      {/* Key Metrics */}
      {!loading && stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Anomalies</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total_anomalies}</p>
              </div>
              <AlertCircle className="w-12 h-12 text-blue-600 opacity-20" />
            </CardBody>
          </Card>

          <Card>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Pending Review</p>
                <p className="text-3xl font-bold text-yellow-600">{stats.pending_review}</p>
              </div>
              <Clock className="w-12 h-12 text-yellow-600 opacity-20" />
            </CardBody>
          </Card>

          <Card>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Confirmed</p>
                <p className="text-3xl font-bold text-red-600">{stats.confirmed}</p>
              </div>
              <AlertCircle className="w-12 h-12 text-red-600 opacity-20" />
            </CardBody>
          </Card>

          <Card>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Average Score</p>
                <p className="text-3xl font-bold text-blue-600">
                  {(stats.average_score * 100).toFixed(0)}%
                </p>
              </div>
              <TrendingUp className="w-12 h-12 text-blue-600 opacity-20" />
            </CardBody>
          </Card>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution */}
        {categoryData.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="text-xl font-bold text-gray-900">Anomalies by Category</h2>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>
        )}

        {/* Status Distribution */}
        {statusData.some(d => d.value > 0) && (
          <Card>
            <CardHeader>
              <h2 className="text-xl font-bold text-gray-900">Anomalies by Status</h2>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData.filter(d => d.value > 0)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>
        )}
      </div>

      {/* Recent Anomalies Table */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Recent Anomalies</h2>
          <span className="text-sm text-gray-600">Last 50 anomalies</span>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : anomalies.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No anomalies detected yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Timestamp</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Category</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Amount</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Score</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {anomalies.map((anomaly) => (
                    <tr key={anomaly.anomaly_id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-gray-900">
                        {format(new Date(anomaly.detection_timestamp), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="px-6 py-3">
                        <CategoryBadge category={anomaly.category} />
                      </td>
                      <td className="px-6 py-3 font-medium text-gray-900">
                        {anomaly.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                anomaly.score > 0.8
                                  ? 'bg-red-600'
                                  : anomaly.score > 0.5
                                  ? 'bg-yellow-600'
                                  : 'bg-green-600'
                              }`}
                              style={{ width: `${anomaly.score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-gray-900 font-medium">{(anomaly.score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-3">
                        <StatusBadge status={anomaly.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}

export default Dashboard
