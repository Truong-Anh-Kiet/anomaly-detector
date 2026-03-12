/**
 * Audit Logs Page Component
 * View system audit trail
 */

import { useState } from 'react'
import { useAuditLogs } from '@/hooks'
import {
  LoadingSpinner,
  ErrorAlert,
  Card,
  CardHeader,
  CardBody,
} from '@/components/ui'
import { LogIn, AlertCircle, Activity, Filter } from 'lucide-react'
import { format } from 'date-fns'

function AuditLogsPage() {
  const [filters, setFilters] = useState({
    days: 30,
    action: '',
  })

  const { logs, loading, error, refetch } = useAuditLogs(filters.days)

  const filteredLogs = logs.filter((log: any) => {
    if (filters.action && log.action !== filters.action) return false
    return true
  })

  // Get unique actions for filter dropdown
  const uniqueActions = [
    ...new Set(logs.map((log: any) => log.action)),
  ] as string[]

  // Group logs by type for statistics
  const actionStats = {
    login: logs.filter((l: any) => l.action === 'login').length,
    view_anomalies: logs.filter((l: any) => l.action === 'view_anomalies').length,
    update_status: logs.filter((l: any) => l.action === 'update_status').length,
    export: logs.filter((l: any) => l.action === 'export').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600 mt-1">
          System activity and user actions
        </p>
      </div>

      {/* Error Alert */}
      {error && <ErrorAlert message={error} onDismiss={refetch} />}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Actions</p>
              <p className="text-3xl font-bold text-gray-900">{logs.length}</p>
            </div>
            <Activity className="w-12 h-12 text-blue-600 opacity-20" />
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Logins</p>
              <p className="text-3xl font-bold text-green-600">{actionStats.login}</p>
            </div>
            <LogIn className="w-12 h-12 text-green-600 opacity-20" />
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Anomaly Views</p>
              <p className="text-3xl font-bold text-blue-600">
                {actionStats.view_anomalies}
              </p>
            </div>
            <AlertCircle className="w-12 h-12 text-blue-600 opacity-20" />
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Status Updates</p>
              <p className="text-3xl font-bold text-purple-600">
                {actionStats.update_status}
              </p>
            </div>
            <Activity className="w-12 h-12 text-purple-600 opacity-20" />
          </CardBody>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Days Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Period
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

            {/* Action Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action
              </label>
              <select
                value={filters.action}
                onChange={(e) =>
                  setFilters({ ...filters, action: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Actions</option>
                {uniqueActions.map((action) => (
                  <option key={action} value={action}>
                    {action.replace(/_/g, ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Audit Logs Table */}
      <Card>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No audit logs found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Resource
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredLogs.map((log: any) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-sm text-gray-900 whitespace-nowrap">
                        {format(
                          new Date(log.timestamp),
                          'MMM dd, yyyy HH:mm:ss'
                        )}
                      </td>
                      <td className="px-6 py-3 text-sm">
                        <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                          {log.user_id || 'System'}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-sm font-medium text-gray-900">
                        {log.action.replace(/_/g, ' ').toUpperCase()}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {log.resource_type && log.resource_id && (
                          <span>
                            {log.resource_type}: {log.resource_id}
                          </span>
                        )}
                        {!log.resource_type && '-'}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600 max-w-md">
                        {log.details ? (
                          <details className="cursor-pointer">
                            <summary className="text-blue-600 hover:underline">
                              View Details
                            </summary>
                            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </details>
                        ) : (
                          '-'
                        )}
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

export default AuditLogsPage
