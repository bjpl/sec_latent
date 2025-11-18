'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  Cell,
} from 'recharts'
import { useSignalStore } from '@/stores/signalStore'

export function RiskMatrix() {
  const { signals } = useSignalStore()

  const chartData = useMemo(() => {
    return signals.slice(0, 50).map((signal) => ({
      x: signal.confidence * 100,
      y: signal.strength * 100,
      z: 100,
      ticker: signal.ticker,
      type: signal.signal_type,
    }))
  }, [signals])

  const getColor = (x: number, y: number) => {
    const risk = (x * y) / 10000
    if (risk > 0.7) return '#ef4444' // red
    if (risk > 0.5) return '#f59e0b' // orange
    if (risk > 0.3) return '#eab308' // yellow
    return '#3b82f6' // blue
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <XAxis
                type="number"
                dataKey="x"
                name="Confidence"
                unit="%"
                domain={[0, 100]}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Strength"
                unit="%"
                domain={[0, 100]}
              />
              <ZAxis type="number" dataKey="z" range={[60, 400]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="bg-background border rounded-lg p-3 shadow-lg">
                        <p className="font-semibold">{data.ticker}</p>
                        <p className="text-sm text-muted-foreground">
                          {data.type}
                        </p>
                        <p className="text-sm">
                          Confidence: {data.x.toFixed(1)}%
                        </p>
                        <p className="text-sm">Strength: {data.y.toFixed(1)}%</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Scatter name="Signals" data={chartData} fill="#8884d8">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.x, entry.y)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-4 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500" />
            <span>Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500" />
            <span>Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500" />
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500" />
            <span>Critical Risk</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
