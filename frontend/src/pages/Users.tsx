/**
 * User Management Page
 * Admin interface for managing system users
 */

import { useState } from 'react'
import { Trash2, Plus, Edit2 } from 'lucide-react'
import { useUsers } from '@/hooks'
import { useAuthStore } from '@/services/authStore'
import { ErrorAlert, SuccessAlert, LoadingSpinner, Card, CardBody, CardHeader, Badge } from '@/components/ui'
import type { CreateUserRequest, UpdateUserRequest } from '@/types'

export function Users() {
  const { user: currentUser } = useAuthStore()
  const { users, loading, error, createUser, updateUser, deleteUser } = useUsers()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState('')
  const [formError, setFormError] = useState('')

  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'analyst',
  })

  const [editData, setEditData] = useState<UpdateUserRequest>({
    email: '',
    full_name: '',
    role: 'analyst',
  })

  const handleCreateChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    setFormError('')
  }

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setEditData((prev) => ({ ...prev, [name]: value }))
    setFormError('')
  }

  const validateCreateForm = (): boolean => {
    if (!formData.username.trim()) {
      setFormError('Username is required')
      return false
    }
    if (formData.username.length < 3) {
      setFormError('Username must be at least 3 characters')
      return false
    }
    if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setFormError('Invalid email address')
      return false
    }
    if (!formData.password) {
      setFormError('Password is required')
      return false
    }
    if (formData.password.length < 8) {
      setFormError('Password must be at least 8 characters')
      return false
    }
    if (!formData.full_name.trim()) {
      setFormError('Full name is required')
      return false
    }
    return true
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateCreateForm()) return

    try {
      await createUser(formData)
      setSuccessMessage('User created successfully')
      setFormData({ username: '', email: '', password: '', full_name: '', role: 'analyst' })
      setShowCreateForm(false)
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      // Error is already set in the hook
    }
  }

  const handleEditStart = (userId: string) => {
    const user = users.find((u) => u.user_id === userId)
    if (user) {
      setEditingId(userId)
      setEditData({
        email: user.email,
        full_name: user.full_name,
        role: user.role,
      })
      setFormError('')
    }
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingId) return

    if (!editData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setFormError('Invalid email address')
      return
    }

    try {
      await updateUser(editingId, editData)
      setSuccessMessage('User updated successfully')
      setEditingId(null)
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      // Error is already set in the hook
    }
  }

  const handleDelete = async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return
    }

    try {
      await deleteUser(userId)
      setSuccessMessage('User deleted successfully')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      // Error is already set in the hook
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setShowCreateForm(false)
    setFormError('')
  }

  // Only admins can access this page
  if (currentUser?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card>
          <CardBody className="text-center">
            <p className="text-red-600 font-medium">Access Denied</p>
            <p className="text-gray-600 mt-2">Only administrators can manage users.</p>
          </CardBody>
        </Card>
      </div>
    )
  }

  if (loading && users.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600 mt-1">Manage system users and their roles</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          <Plus size={20} />
          New User
        </button>
      </div>

      {/* Messages */}
      {successMessage && <SuccessAlert message={successMessage} />}
      {(error || formError) && <ErrorAlert message={error || formError} />}

      {/* Create Form */}
      {showCreateForm && (
        <Card className="bg-blue-50 border-2 border-blue-200">
          <CardHeader className="text-lg font-semibold text-gray-900">Create New User</CardHeader>
          <CardBody>
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleCreateChange}
                    placeholder="john_doe"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleCreateChange}
                    placeholder="john@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleCreateChange}
                    placeholder="John Doe"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleCreateChange}
                    placeholder="Minimum 8 characters"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleCreateChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="admin">Admin</option>
                    <option value="analyst">Analyst</option>
                    <option value="auditor">Auditor</option>
                    <option value="guest">Guest</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Create User
                </button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {/* Users Table */}
      <Card>
        <CardHeader className="text-lg font-semibold text-gray-900">
          {users.length} {users.length === 1 ? 'User' : 'Users'}
        </CardHeader>
        <CardBody>
          {users.length === 0 ? (
            <p className="text-gray-600 text-center py-8">No users found. Create the first user to get started.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Username</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Full Name</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Email</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Role</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Created</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.user_id} className="hover:bg-gray-50 transition">
                      <td className="py-3 px-4 font-medium text-gray-900">{user.username}</td>
                      <td className="py-3 px-4 text-gray-600">{user.full_name}</td>
                      <td className="py-3 px-4 text-gray-600">{user.email}</td>
                      <td className="py-3 px-4">
                        <Badge variant={getRoleVariant(user.role)}>{user.role}</Badge>
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {editingId === user.user_id ? (
                          <div className="space-y-2">
                            <form onSubmit={handleEditSubmit} className="space-y-3">
                              <div className="grid grid-cols-1 gap-2">
                                <input
                                  type="email"
                                  name="email"
                                  value={editData.email}
                                  onChange={handleEditChange}
                                  placeholder="Email"
                                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <input
                                  type="text"
                                  name="full_name"
                                  value={editData.full_name}
                                  onChange={handleEditChange}
                                  placeholder="Full Name"
                                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <select
                                  name="role"
                                  value={editData.role}
                                  onChange={handleEditChange}
                                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                  <option value="admin">Admin</option>
                                  <option value="analyst">Analyst</option>
                                  <option value="auditor">Auditor</option>
                                  <option value="guest">Guest</option>
                                </select>
                              </div>
                              <div className="flex gap-1">
                                <button
                                  type="submit"
                                  className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition"
                                >
                                  Save
                                </button>
                                <button
                                  type="button"
                                  onClick={handleCancel}
                                  className="px-2 py-1 bg-gray-300 text-gray-700 text-xs rounded hover:bg-gray-400 transition"
                                >
                                  Cancel
                                </button>
                              </div>
                            </form>
                          </div>
                        ) : (
                          <div className="flex gap-2 justify-end">
                            <button
                              onClick={() => handleEditStart(user.user_id)}
                              className="p-1 text-blue-600 hover:bg-blue-100 rounded transition"
                              title="Edit user"
                            >
                              <Edit2 size={18} />
                            </button>
                            <button
                              onClick={() => handleDelete(user.user_id)}
                              className="p-1 text-red-600 hover:bg-red-100 rounded transition"
                              title="Delete user"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
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

function getRoleVariant(role: string) {
  switch (role) {
    case 'admin':
      return 'danger'
    case 'analyst':
      return 'default'
    case 'auditor':
      return 'warning'
    case 'guest':
      return 'secondary'
    default:
      return 'default'
  }
}
