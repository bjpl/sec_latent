'use client'

import { useEffect } from 'react'
import { PredictionTimeline } from '@/components/PredictionTimeline'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePredictionStore } from '@/stores/predictionStore'
import { apiClient } from '@/lib/api'
import { TrendingUp, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function PredictionsPage() {
  const { predictions, setPredictions, setLoading, setError } =
    usePredictionStore()

  useEffect(() => {
    async function loadPredictions() {
      try {
        setLoading(true)
        const data = await apiClient.getPredictions()
        setPredictions(data.predictions || [])
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load predictions'
        )
      } finally {
        setLoading(false)
      }
    }

    loadPredictions()
  }, [setPredictions, setLoading, setError])

  const stats = {
    total: predictions.length,
    pending: predictions.filter((p) => p.status === 'pending').length,
    validated: predictions.filter((p) => p.status === 'validated').length,
    failed: predictions.filter((p) => p.status === 'failed').length,
    avgConfidence:
      predictions.reduce((sum, p) => sum + p.confidence, 0) /
        predictions.length || 0,
    accuracy:
      predictions.filter((p) => p.status === 'validated').length /
        predictions.filter((p) => p.status !== 'pending').length || 0,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Predictions</h1>
        <p className="text-muted-foreground">
          Track and validate market predictions over time
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Predictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <div className="text-2xl font-bold">{stats.total}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              <div className="text-2xl font-bold">{stats.pending}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Validated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div className="text-2xl font-bold">{stats.validated}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Accuracy
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={stats.accuracy > 0.7 ? 'default' : 'secondary'}>
                {(stats.accuracy * 100).toFixed(1)}%
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <PredictionTimeline />
    </div>
  )
}
