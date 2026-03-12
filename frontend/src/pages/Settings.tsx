/**
 * Settings Page Component
 * Configure thresholds and system settings
 */

import { useState } from 'react'
import { useThresholds } from '@/hooks'
import {
  LoadingSpinner,
  ErrorAlert,
  SuccessAlert,
  Card,
  CardHeader,
  CardBody,
  Button,
} from '@/components/ui'
import { Settings as SettingsIcon, AlertCircle } from 'lucide-react'

function SettingsPage() {
  const { thresholds, loading, error, updateThreshold } = useThresholds()
  const [editingCategory, setEditingCategory] = useState<string | null>(null)
  const [editValue, setEditValue] = useState(0)
  const [successMessage, setSuccessMessage] = useState('')

  const handleSaveThreshold = async (category: string) => {
    try {
      await updateThreshold(category, editValue)
      setSuccessMessage(
        `${category} threshold updated to ${(editValue * 100).toFixed(0)}%`
      )
      setEditingCategory(null)
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      console.error('Failed to update threshold:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Configure system parameters and detection thresholds
        </p>
      </div>

      {/* Error Alert */}
      {error && <ErrorAlert message={error} />}

      {/* Success Alert */}
      {successMessage && <SuccessAlert message={successMessage} />}

      {/* Anomaly Detection Thresholds */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-bold text-gray-900">
              Anomaly Detection Thresholds
            </h2>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Adjust the sensitivity of anomaly detection for each category
          </p>
        </CardHeader>

        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-6">
              {thresholds.map((threshold: any) => (
                <div
                  key={threshold.category}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 capitalize">
                        {threshold.category} Anomalies
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {threshold.description}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Current Value</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {(threshold.current_value * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  {/* Range Display */}
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-600 mb-2">
                      <span>Min: {(threshold.min * 100).toFixed(0)}%</span>
                      <span>Max: {(threshold.max * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 relative">
                      <div
                        className="bg-gray-300 h-3 rounded-full"
                        style={{
                          width: `${((threshold.min) / 1) * 100}%`,
                        }}
                      ></div>
                      <div
                        className={`h-3 rounded-full absolute top-0 ${
                          editingCategory === threshold.category
                            ? 'bg-amber-500'
                            : 'bg-blue-500'
                        }`}
                        style={{
                          left: `${
                            ((editingCategory === threshold.category
                              ? editValue
                              : threshold.current_value) /
                              1) *
                            100
                          }%`,
                          width: '20px',
                          transform: 'translateX(-50%)',
                        }}
                      ></div>
                    </div>
                  </div>

                  {/* Edit Form */}
                  {editingCategory === threshold.category ? (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          New Threshold Value
                        </label>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min={threshold.min}
                            max={threshold.max}
                            step={0.01}
                            value={editValue}
                            onChange={(e) =>
                              setEditValue(parseFloat(e.target.value))
                            }
                            className="flex-1"
                          />
                          <span className="font-semibold text-lg text-blue-600 w-16">
                            {(editValue * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() =>
                            handleSaveThreshold(threshold.category)
                          }
                        >
                          Save Changes
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setEditingCategory(null)
                            setEditValue(threshold.current_value)
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setEditValue(threshold.default)
                          }}
                        >
                          Reset to Default
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setEditingCategory(threshold.category)
                        setEditValue(threshold.current_value)
                      }}
                    >
                      Edit Threshold
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-bold text-gray-900">General Settings</h2>
          </div>
        </CardHeader>

        <CardBody>
          <div className="space-y-6">
            {/* Batch Processing */}
            <div className="border-b border-gray-200 pb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">Batch Processing</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Automatically process anomalies in batches
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>

            {/* Email Notifications */}
            <div className="border-b border-gray-200 pb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">Email Notifications</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Send alerts for critical anomalies
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>

            {/* Real-time Detection */}
            <div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">Real-time Detection</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Process anomalies immediately as they occur
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}

export default SettingsPage
