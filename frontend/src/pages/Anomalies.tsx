/**
 * Anomalies Page Component
 * View and manage detected anomalies
 */

import { useState, useMemo } from 'react'
import { useAnomalies } from '@/hooks'
import {
  LoadingSpinner,
  ErrorAlert,
  Card,
  CardHeader,
  CardBody,
  Button,
  StatusBadge,
  CategoryBadge,
} from '@/components/ui'
import { Filter, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { apiService } from '@/services/api'

function AnomaliesPage() {
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    minScore: 0,
    days: 30,
  })
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editStatus, setEditStatus] = useState('')
  const [editNotes, setEditNotes] = useState('')

  const { anomalies, loading, error, refetch, updateStatus } = useAnomalies({
    category: filters.category || undefined,
    status: filters.status || undefined,
    min_score: filters.minScore,
    days: filters.days,
    limit: 100,
  })

  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((a) => {
      if (filters.category && a.category !== filters.category) return false
      if (filters.status && a.status !== filters.status) return false
      return true
    })
  }, [anomalies, filters])

  const handleStatusUpdate = async (anomalyId: string) => {
    try {
      await updateStatus(anomalyId, editStatus, editNotes)
      setEditingId(null)
      setEditStatus('')
      setEditNotes('')
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await apiService.exportAnomalies(format, {
        category: filters.category || undefined,
        status: filters.status || undefined,
        days: filters.days,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `anomalies.${format}`
      a.click()
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Anomalies</h1>
          <p className="text-gray-600 mt-1">
            {filteredAnomalies.length} anomalies found
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleExport('json')}
          >
            Export JSON
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleExport('csv')}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && <ErrorAlert message={error} onDismiss={refetch} />}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) =>
                  setFilters({ ...filters, category: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                <option value="payment">Payment</option>
                <option value="network">Network</option>
                <option value="behavioral">Behavioral</option>
                <option value="system">System</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) =>
                  setFilters({ ...filters, status: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending_review">Pending Review</option>
                <option value="confirmed">Confirmed</option>
                <option value="false_positive">False Positive</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            {/* Min Score Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Score: {(filters.minScore * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.minScore}
                onChange={(e) =>
                  setFilters({ ...filters, minScore: parseFloat(e.target.value) })
                }
                className="w-full"
              />
            </div>

            {/* Days Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Days
              </label>
              <select
                value={filters.days}
                onChange={(e) =>
                  setFilters({ ...filters, days: parseInt(e.target.value) })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Anomalies List */}
      <Card>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : filteredAnomalies.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No anomalies match your filters</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredAnomalies.map((anomaly) => (
                <div
                  key={anomaly.anomaly_id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <CategoryBadge category={anomaly.category} />
                        <StatusBadge status={anomaly.status} />
                        <span className="text-sm text-gray-600">
                          {format(
                            new Date(anomaly.detection_timestamp),
                            'MMM dd, yyyy HH:mm:ss'
                          )}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-xs text-gray-600">Amount</p>
                          <p className="font-semibold text-lg">${anomaly.amount.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Anomaly Score</p>
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
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
                            <span className="font-semibold">
                              {(anomaly.score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Threshold</p>
                          <p className="font-semibold">{(anomaly.threshold * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setEditingId(anomaly.anomaly_id)
                        setEditStatus(anomaly.status)
                        setEditNotes(anomaly.review_notes || '')
                      }}
                      className="px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      Review
                    </button>
                  </div>

                  {/* Edit Form */}
                  {editingId === anomaly.anomaly_id && (
                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Status
                        </label>
                        <select
                          value={editStatus}
                          onChange={(e) => setEditStatus(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="pending_review">Pending Review</option>
                          <option value="confirmed">Confirmed</option>
                          <option value="false_positive">False Positive</option>
                          <option value="resolved">Resolved</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Review Notes
                        </label>
                        <textarea
                          value={editNotes}
                          onChange={(e) => setEditNotes(e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="Add any review notes..."
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() =>
                            handleStatusUpdate(anomaly.anomaly_id)
                          }
                        >
                          Save
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setEditingId(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}

export default AnomaliesPage
