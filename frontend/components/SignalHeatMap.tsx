'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { useSignalStore } from '@/stores/signalStore'
import { cn } from '@/lib/utils'

interface HeatMapCell {
  ticker: string
  timeframe: string
  strength: number
  count: number
}

export function SignalHeatMap() {
  const { signals } = useSignalStore()

  const heatMapData = useMemo(() => {
    const data = new Map<string, HeatMapCell>()
    const timeframes = ['1h', '4h', '1d']
    const tickers = [...new Set(signals.map((s) => s.ticker))].slice(0, 10)

    tickers.forEach((ticker) => {
      timeframes.forEach((timeframe) => {
        const key = `${ticker}-${timeframe}`
        const relevantSignals = signals.filter(
          (s) => s.ticker === ticker && s.timeframe === timeframe
        )
        const avgStrength =
          relevantSignals.reduce((sum, s) => sum + s.strength, 0) /
            relevantSignals.length || 0

        data.set(key, {
          ticker,
          timeframe,
          strength: avgStrength,
          count: relevantSignals.length,
        })
      })
    })

    return { data, tickers, timeframes }
  }, [signals])

  const getColorClass = (strength: number) => {
    if (strength === 0) return 'bg-gray-100 dark:bg-gray-800'
    if (strength < 0.3) return 'bg-blue-200 dark:bg-blue-900'
    if (strength < 0.6) return 'bg-yellow-300 dark:bg-yellow-800'
    return 'bg-red-400 dark:bg-red-700'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Signal Heat Map</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full">
            <div className="flex">
              <div className="w-20" />
              <div className="flex flex-1">
                {heatMapData.timeframes.map((tf) => (
                  <div
                    key={tf}
                    className="flex-1 text-center text-sm font-medium py-2"
                  >
                    {tf}
                  </div>
                ))}
              </div>
            </div>
            {heatMapData.tickers.map((ticker) => (
              <div key={ticker} className="flex items-center">
                <div className="w-20 text-sm font-medium pr-2">{ticker}</div>
                <div className="flex flex-1 gap-1">
                  {heatMapData.timeframes.map((timeframe) => {
                    const cell = heatMapData.data.get(`${ticker}-${timeframe}`)
                    return (
                      <div
                        key={timeframe}
                        className={cn(
                          'flex-1 h-12 rounded flex items-center justify-center text-xs font-medium cursor-pointer transition-all hover:scale-105',
                          getColorClass(cell?.strength || 0)
                        )}
                        title={`${ticker} ${timeframe}: ${cell?.count || 0} signals, ${((cell?.strength || 0) * 100).toFixed(1)}% strength`}
                      >
                        {cell?.count || 0}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
