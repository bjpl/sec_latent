import { useEffect, useRef } from 'react'
import { useSignalStore } from '@/stores/signalStore'
import { usePredictionStore } from '@/stores/predictionStore'
import { useAlertStore } from '@/stores/alertStore'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const { addSignal } = useSignalStore()
  const { addPrediction } = usePredictionStore()
  const { addAlert } = useAlertStore()

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          switch (data.type) {
            case 'signal':
              addSignal({
                ...data.payload,
                timestamp: new Date(data.payload.timestamp),
              })
              break
            case 'prediction':
              addPrediction({
                ...data.payload,
                created_at: new Date(data.payload.created_at),
                target_date: new Date(data.payload.target_date),
              })
              break
            case 'alert':
              addAlert({
                ...data.payload,
                created_at: new Date(data.payload.created_at),
              })
              break
          }
        } catch (error) {
          console.error('WebSocket message error:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...')
        reconnectTimeoutRef.current = setTimeout(connect, 5000)
      }

      wsRef.current = ws
    }

    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [addSignal, addPrediction, addAlert])

  return wsRef.current
}
