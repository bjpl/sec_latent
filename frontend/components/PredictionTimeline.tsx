'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { usePredictionStore } from '@/stores/predictionStore'
import { formatDate, formatNumber } from '@/lib/utils'
import { TrendingUp, TrendingDown, Clock } from 'lucide-react'

export function PredictionTimeline() {
  const { predictions } = usePredictionStore()

  const getStatusIcon = (prediction: any) => {
    if (prediction.status === 'pending') return <Clock className="h-4 w-4" />
    if (prediction.actual_value && prediction.predicted_value) {
      return prediction.actual_value > prediction.predicted_value ? (
        <TrendingUp className="h-4 w-4 text-green-500" />
      ) : (
        <TrendingDown className="h-4 w-4 text-red-500" />
      )
    }
    return null
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'validated':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      default:
        return 'bg-yellow-500'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prediction Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        {predictions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No predictions available
          </div>
        ) : (
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
            <div className="space-y-4">
              {predictions.slice(0, 10).map((prediction) => (
                <div key={prediction.id} className="relative flex gap-4 pl-10">
                  <div
                    className={`absolute left-2.5 w-3 h-3 rounded-full ${getStatusColor(prediction.status)}`}
                  />
                  <div className="flex-1 border rounded-lg p-4 hover:bg-accent transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">
                          {prediction.ticker}
                        </span>
                        {getStatusIcon(prediction)}
                        <Badge variant="outline">
                          {prediction.prediction_type}
                        </Badge>
                      </div>
                      <Badge
                        variant={
                          prediction.status === 'validated'
                            ? 'default'
                            : prediction.status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {prediction.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                      <div>
                        <span className="text-muted-foreground">
                          Predicted:{' '}
                        </span>
                        <span className="font-medium">
                          {formatNumber(prediction.predicted_value)}
                        </span>
                      </div>
                      {prediction.actual_value && (
                        <div>
                          <span className="text-muted-foreground">
                            Actual:{' '}
                          </span>
                          <span className="font-medium">
                            {formatNumber(prediction.actual_value)}
                          </span>
                        </div>
                      )}
                      <div>
                        <span className="text-muted-foreground">
                          Confidence:{' '}
                        </span>
                        <span className="font-medium">
                          {formatNumber(prediction.confidence * 100, 0)}%
                        </span>
                      </div>
                      {prediction.error && (
                        <div>
                          <span className="text-muted-foreground">Error: </span>
                          <span className="font-medium">
                            {formatNumber(prediction.error * 100, 1)}%
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Created: {formatDate(prediction.created_at)} • Target:{' '}
                      {formatDate(prediction.target_date)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
