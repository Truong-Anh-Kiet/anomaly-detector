/**
 * Notification Listener Component
 * Initializes WebSocket and displays real-time notifications
 */

import { useEffect, useCallback, useRef } from 'react'
import { wsService, type NotificationEvent } from '@/services/websocket'
import { useAuthStore } from '@/services/authStore'
import { useToast } from '@/services/notificationsStore'

const MAX_RETRY_ATTEMPTS = 3
const RETRY_DELAY_MS = 2000

export function NotificationListener() {
  const { user } = useAuthStore()
  const { success, error, warning, info } = useToast()
  const retryCountRef = useRef(0)
  const connectionAttemptRef = useRef(false)

  // Memoize toast handlers to prevent dependency array issues
  const handleAnomalyEvent = useCallback((event: NotificationEvent) => {
    const severity = event.severity as 'success' | 'error' | 'warning' | 'info'
    if (severity === 'success') success(event.title, event.message)
    else if (severity === 'error') error(event.title, event.message)
    else if (severity === 'warning') warning(event.title, event.message)
    else info(event.title, event.message)
  }, [success, error, warning, info])

  const handleThresholdEvent = useCallback((event: NotificationEvent) => {
    warning(event.title, event.message, 8000)
  }, [warning])

  const handleSystemAlert = useCallback((event: NotificationEvent) => {
    const severity = event.severity as 'success' | 'error' | 'warning' | 'info'
    if (severity === 'error') error(event.title, event.message, 8000)
    else if (severity === 'warning') warning(event.title, event.message, 8000)
    else if (severity === 'success') success(event.title, event.message)
    else info(event.title, event.message)
  }, [error, warning, success, info])

  const handleUserAction = useCallback((event: NotificationEvent) => {
    info(event.title, event.message)
  }, [info])

  const connectWebSocket = useCallback(async () => {
    // Prevent multiple simultaneous connection attempts
    if (connectionAttemptRef.current) return

    const token = localStorage.getItem('access_token')
    
    // Validate token exists
    if (!token) {
      console.warn('No access token available for WebSocket connection')
      return
    }

    connectionAttemptRef.current = true

    try {
      await wsService.connect(token)
      retryCountRef.current = 0 // Reset retry counter on successful connection
      console.log('WebSocket connected successfully')
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      
      // Retry connection with exponential backoff
      if (retryCountRef.current < MAX_RETRY_ATTEMPTS) {
        retryCountRef.current += 1
        const delay = RETRY_DELAY_MS * Math.pow(2, retryCountRef.current - 1)
        console.log(`Retrying WebSocket connection in ${delay}ms (attempt ${retryCountRef.current}/${MAX_RETRY_ATTEMPTS})`)
        
        setTimeout(() => {
          connectionAttemptRef.current = false
          connectWebSocket()
        }, delay)
      } else {
        console.error('Max WebSocket reconnection attempts reached')
        error('Connection Failed', 'Unable to establish real-time connection. Please refresh the page.')
      }
    } finally {
      connectionAttemptRef.current = false
    }
  }, [error])

  useEffect(() => {
    if (!user) return

    // Initiate WebSocket connection
    connectWebSocket()

    // Subscribe to anomaly detections
    const unsubscribeAnomalies = wsService.subscribeToAnomalies(handleAnomalyEvent)

    // Subscribe to threshold alerts
    const unsubscribeThresholds = wsService.subscribeToThresholdAlerts(handleThresholdEvent)

    // Subscribe to system alerts
    const unsubscribeSystem = wsService.subscribeToSystemAlerts(handleSystemAlert)

    // Subscribe to user actions
    const unsubscribeActions = wsService.subscribeToUserActions(handleUserAction)

    // Cleanup function: disconnect and unsubscribe on unmount or user change
    return () => {
      try {
        unsubscribeAnomalies()
        unsubscribeThresholds()
        unsubscribeSystem()
        unsubscribeActions()
      } catch (err) {
        console.warn('Error unsubscribing from events:', err)
      }
      
      try {
        wsService.disconnect()
      } catch (err) {
        console.warn('Error disconnecting WebSocket:', err)
      }
    }
  }, [user, connectWebSocket, handleAnomalyEvent, handleThresholdEvent, handleSystemAlert, handleUserAction])

  return null
}
