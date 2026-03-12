/**
 * Reusable UI Components
 */

import { AlertCircle, CheckCircle, InfoIcon, AlertTriangle } from 'lucide-react'

// Loading Spinner
export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
    </div>
  )
}

// Error Alert
export function ErrorAlert({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-red-700 font-medium">Error</p>
        <p className="text-red-600 text-sm mt-1">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-600 hover:text-red-700"
        >
          ✕
        </button>
      )}
    </div>
  )
}

// Success Alert
export function SuccessAlert({ message }: { message: string }) {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex gap-3">
      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
      <p className="text-green-700 text-sm">{message}</p>
    </div>
  )
}

// Warning Alert
export function WarningAlert({ message }: { message: string }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex gap-3">
      <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
      <p className="text-yellow-700 text-sm">{message}</p>
    </div>
  )
}

// Info Alert
export function InfoAlert({ message }: { message: string }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
      <InfoIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <p className="text-blue-700 text-sm">{message}</p>
    </div>
  )
}

// Badge
export function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info'
}) {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${variants[variant]}`}>
      {children}
    </span>
  )
}

// Status Badge
export function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    pending_review: { label: 'Pending Review', variant: 'warning' as const },
    confirmed: { label: 'Confirmed', variant: 'error' as const },
    false_positive: { label: 'False Positive', variant: 'success' as const },
    resolved: { label: 'Resolved', variant: 'success' as const },
  }

  const config = statusConfig[status as keyof typeof statusConfig] || {
    label: status,
    variant: 'default' as const,
  }

  return <Badge variant={config.variant}>{config.label}</Badge>
}

// Category Badge
export function CategoryBadge({ category }: { category: string }) {
  const categoryConfig = {
    payment: { label: 'Payment', variant: 'error' as const },
    network: { label: 'Network', variant: 'warning' as const },
    behavioral: { label: 'Behavioral', variant: 'info' as const },
    system: { label: 'System', variant: 'default' as const },
  }

  const config = categoryConfig[category as keyof typeof categoryConfig] || {
    label: category,
    variant: 'default' as const,
  }

  return <Badge variant={config.variant}>{config.label}</Badge>
}

// Card Component
export function Card({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {children}
    </div>
  )
}

// Card Header
export function CardHeader({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  )
}

// Card Body
export function CardBody({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  )
}

// Button Component
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  className = '',
  ...props
}: {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  className?: string
  [key: string]: any
}) {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  }

  const sizes = {
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      disabled={disabled}
      className={`font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

// Toast Notification Component
export interface ToastProps {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  onClose?: (id: string) => void
}

export function Toast({ id, type, title, message, onClose }: ToastProps) {
  const bgColor = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  }

  const textColor = {
    success: 'text-green-700',
    error: 'text-red-700',
    warning: 'text-yellow-700',
    info: 'text-blue-700',
  }

  const iconColor = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-yellow-600',
    info: 'text-blue-600',
  }

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <InfoIcon className="w-5 h-5" />,
  }

  return (
    <div
      className={`border rounded-lg p-4 flex gap-3 shadow-lg animate-slideIn ${bgColor[type]}`}
      role="alert"
    >
      <div className={`flex-shrink-0 mt-0.5 ${iconColor[type]}`}>{icons[type]}</div>
      <div className="flex-1">
        <p className={`font-semibold ${textColor[type]}`}>{title}</p>
        <p className={`text-sm ${textColor[type]} opacity-90 mt-1`}>{message}</p>
      </div>
      {onClose && (
        <button
          onClick={() => onClose(id)}
          className={`flex-shrink-0 ${textColor[type]} hover:opacity-70 transition`}
        >
          ✕
        </button>
      )}
    </div>
  )
}

// Toast Container Component
export function ToastContainer({ toasts, onClose }: { toasts: ToastProps[]; onClose: (id: string) => void }) {
  return (
    <div className="fixed bottom-6 right-6 space-y-3 z-50 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast {...toast} onClose={onClose} />
        </div>
      ))}
    </div>
  )
}
