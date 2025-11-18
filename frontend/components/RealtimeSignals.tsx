'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { useSignalStore } from '@/stores/signalStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { formatDate, formatNumber } from '@/lib/utils'
import { Activity } from 'lucide-react'

export function RealtimeSignals() {
  useWebSocket() // Initialize WebSocket connection
  const { signals, loading } = useSignalStore()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary animate-pulse" />
          Real-time Signals
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">
            Loading signals...
          </div>
        ) : signals.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No signals yet. Waiting for data...
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {signals.slice(0, 20).map((signal) => (
              <div
                key={signal.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold">{signal.ticker}</span>
                    <Badge variant="outline">{signal.signal_type}</Badge>
                    <Badge
                      variant={
                        signal.strength > 0.7
                          ? 'default'
                          : signal.strength > 0.4
                          ? 'secondary'
                          : 'outline'
                      }
                    >
                      {formatNumber(signal.strength * 100, 0)}%
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatDate(signal.timestamp)} • {signal.timeframe}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {formatNumber(signal.confidence * 100, 0)}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Confidence
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
