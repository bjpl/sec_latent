'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAlertStore } from '@/stores/alertStore'
import { apiClient } from '@/lib/api'
import { formatDate, getRiskColor, getStatusColor } from '@/lib/utils'
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function AlertsPage() {
  const { alerts, setAlerts, resolveAlert, setLoading, setError } =
    useAlertStore()
  const { toast } = useToast()

  useEffect(() => {
    async function loadAlerts() {
      try {
        setLoading(true)
        const data = await apiClient.getAlerts()
        setAlerts(data.alerts || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load alerts')
      } finally {
        setLoading(false)
      }
    }

    loadAlerts()
  }, [setAlerts, setLoading, setError])

  const handleResolve = async (id: string) => {
    try {
      await apiClient.resolveAlert(id)
      resolveAlert(id)
      toast({
        title: 'Alert Resolved',
        description: 'The alert has been marked as resolved.',
      })
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to resolve alert',
        variant: 'destructive',
      })
    }
  }

  const activeAlerts = alerts.filter((a) => a.status === 'active')
  const resolvedAlerts = alerts.filter((a) => a.status === 'resolved')
  const criticalCount = activeAlerts.filter(
    (a) => a.severity === 'critical'
  ).length
  const highCount = activeAlerts.filter((a) => a.severity === 'high').length

  const getSeverityIcon = (severity: string) => {
    if (severity === 'critical' || severity === 'high') {
      return <AlertCircle className="h-5 w-5" />
    }
    return <AlertCircle className="h-5 w-5" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Alerts</h1>
        <p className="text-muted-foreground">
          Monitor and manage system alerts and notifications
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAlerts.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Critical
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="text-2xl font-bold">{criticalCount}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              High Priority
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500" />
              <div className="text-2xl font-bold">{highCount}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Resolved Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div className="text-2xl font-bold">{resolvedAlerts.length}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {activeAlerts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No active alerts
            </div>
          ) : (
            <div className="space-y-4">
              {activeAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div
                    className={`p-2 rounded-lg ${getRiskColor(alert.severity)}`}
                  >
                    {getSeverityIcon(alert.severity)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">{alert.ticker}</span>
                      <Badge variant="outline">{alert.alert_type}</Badge>
                      <Badge
                        variant={
                          alert.severity === 'critical'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="text-sm mb-2">{alert.message}</p>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(alert.created_at)}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleResolve(alert.id)}
                  >
                    Resolve
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {resolvedAlerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recently Resolved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {resolvedAlerts.slice(0, 10).map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 border rounded-lg opacity-60"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <div>
                      <div className="font-semibold text-sm">
                        {alert.ticker} • {alert.alert_type}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {alert.message}
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline">Resolved</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
