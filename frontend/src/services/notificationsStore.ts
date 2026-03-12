/**
 * Notifications Store
 * Zustand store for managing toast notifications
 */

import { create } from 'zustand'
import type { ToastProps } from '@/components/ui'

interface NotificationsState {
  toasts: ToastProps[]
  addToast: (notification: Omit<ToastProps, 'id'>) => void
  removeToast: (id: string) => void
  clearAll: () => void
}

export const useNotifications = create<NotificationsState>((set) => ({
  toasts: [],

  addToast: (notification) => {
    const id = `toast-${Date.now()}-${Math.random()}`
    set((state) => ({
      toasts: [
        ...state.toasts,
        {
          ...notification,
          id,
        },
      ],
    }))

    // Auto-remove after duration (default 5 seconds)
    const duration = notification.duration || 5000
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, duration)

    return id
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },

  clearAll: () => {
    set({ toasts: [] })
  },
}))

// Convenience methods
export function useToast() {
  const { addToast } = useNotifications()

  return {
    success: (title: string, message: string, duration?: number) =>
      addToast({ type: 'success', title, message, duration }),
    error: (title: string, message: string, duration?: number) =>
      addToast({ type: 'error', title, message, duration }),
    warning: (title: string, message: string, duration?: number) =>
      addToast({ type: 'warning', title, message, duration }),
    info: (title: string, message: string, duration?: number) =>
      addToast({ type: 'info', title, message, duration }),
  }
}
