/**
 * WebSocket Service for Real-Time Updates
 * Handles WebSocket connections and event subscriptions
 */

export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

export interface NotificationEvent {
  id: string
  type: 'anomaly_detected' | 'threshold_exceeded' | 'user_action' | 'system_alert'
  title: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'success'
  data?: any
  read: boolean
  createdAt: string
}

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private messageHandlers: Map<string, Set<(msg: WebSocketMessage) => void>> = new Map()
  private connectionHandlers: Set<(connected: boolean) => void> = new Set()
  private isIntentionallyClosed = false

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = import.meta.env.VITE_WS_URL || `${protocol}://${window.location.host}/ws`
    this.url = wsUrl
  }

  /**
   * Connect to WebSocket server
   */
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.isIntentionallyClosed = false
        const url = token ? `${this.url}?token=${token}` : this.url
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected')
          this.reconnectAttempts = 0
          this.notifyConnectionHandlers(true)
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error)
          this.notifyConnectionHandlers(false)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('🔌 WebSocket disconnected')
          this.notifyConnectionHandlers(false)
          if (!this.isIntentionallyClosed) {
            this.attemptReconnect()
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.isIntentionallyClosed = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Subscribe to a message type
   */
  subscribe(eventType: string, handler: (msg: WebSocketMessage) => void): () => void {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, new Set())
    }
    this.messageHandlers.get(eventType)!.add(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(eventType)
      if (handlers) {
        handlers.delete(handler)
      }
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.connectionHandlers.add(handler)

    // Return unsubscribe function
    return () => {
      this.connectionHandlers.delete(handler)
    }
  }

  /**
   * Send a message through WebSocket
   */
  send(type: string, payload: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type,
          payload,
          timestamp: new Date().toISOString(),
        })
      )
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Private: Handle incoming messages
   */
  private handleMessage(message: WebSocketMessage): void {
    const { type } = message

    // Broadcast to all handlers for this type
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error(`Error in message handler for type "${type}":`, error)
        }
      })
    }

    // Also broadcast to wildcard listeners
    const wildcardHandlers = this.messageHandlers.get('*')
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error('Error in wildcard message handler:', error)
        }
      })
    }
  }

  /**
   * Private: Notify connection status handlers
   */
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(connected)
      } catch (error) {
        console.error('Error in connection handler:', error)
      }
    })
  }

  /**
   * Private: Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(
        `🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      )
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay)
    } else {
      console.error('❌ Max reconnection attempts reached')
    }
  }

  /**
   * Specific event subscriptions for common message types
   */
  subscribeToAnomalies(handler: (event: NotificationEvent) => void): () => void {
    return this.subscribe('anomaly_detected', (msg) => {
      handler(msg.payload as NotificationEvent)
    })
  }

  subscribeToThresholdAlerts(handler: (event: NotificationEvent) => void): () => void {
    return this.subscribe('threshold_exceeded', (msg) => {
      handler(msg.payload as NotificationEvent)
    })
  }

  subscribeToSystemAlerts(handler: (event: NotificationEvent) => void): () => void {
    return this.subscribe('system_alert', (msg) => {
      handler(msg.payload as NotificationEvent)
    })
  }

  subscribeToUserActions(handler: (event: NotificationEvent) => void): () => void {
    return this.subscribe('user_action', (msg) => {
      handler(msg.payload as NotificationEvent)
    })
  }
}

export const wsService = new WebSocketService()
