'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { useSignalStore } from '@/stores/signalStore'
import { useAlertStore } from '@/stores/alertStore'
import { usePredictionStore } from '@/stores/predictionStore'
import { Activity, Bell, TrendingUp } from 'lucide-react'

export function MobileDashboard() {
  const { signals } = useSignalStore()
  const { alerts, unreadCount } = useAlertStore()
  const { predictions } = usePredictionStore()

  const activeSignals = signals.filter(
    (s) => s.confidence > 0.7 && s.strength > 0.6
  ).length
  const pendingPredictions = predictions.filter(
    (p) => p.status === 'pending'
  ).length

  return (
    <div className="lg:hidden space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <Activity className="h-8 w-8 text-primary mb-2" />
              <div className="text-2xl font-bold">{activeSignals}</div>
              <div className="text-xs text-muted-foreground">Active</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <Bell className="h-8 w-8 text-orange-500 mb-2" />
              <div className="text-2xl font-bold">{unreadCount}</div>
              <div className="text-xs text-muted-foreground">Alerts</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <TrendingUp className="h-8 w-8 text-green-500 mb-2" />
              <div className="text-2xl font-bold">{pendingPredictions}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Signals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.slice(0, 5).map((signal) => (
              <div
                key={signal.id}
                className="flex items-center justify-between p-2 border rounded"
              >
                <div>
                  <div className="font-semibold text-sm">{signal.ticker}</div>
                  <div className="text-xs text-muted-foreground">
                    {signal.timeframe}
                  </div>
                </div>
                <Badge
                  variant={signal.strength > 0.7 ? 'default' : 'secondary'}
                >
                  {(signal.strength * 100).toFixed(0)}%
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {alerts
              .filter((a) => a.status === 'active')
              .slice(0, 5)
              .map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start gap-2 p-2 border rounded"
                >
                  <Bell className="h-4 w-4 mt-0.5 flex-shrink-0 text-orange-500" />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm">{alert.ticker}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {alert.message}
                    </div>
                  </div>
                  <Badge variant="outline" className="flex-shrink-0">
                    {alert.severity}
                  </Badge>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
