'use client'

import { useEffect } from 'react'
import { SignalHeatMap } from '@/components/SignalHeatMap'
import { RealtimeSignals } from '@/components/RealtimeSignals'
import { RiskMatrix } from '@/components/RiskMatrix'
import { MobileDashboard } from '@/components/MobileDashboard'
import { useSignalStore } from '@/stores/signalStore'
import { apiClient } from '@/lib/api'

export default function DashboardPage() {
  const { setSignals, setLoading, setError } = useSignalStore()

  useEffect(() => {
    async function loadSignals() {
      try {
        setLoading(true)
        const data = await apiClient.getSignals(100)
        setSignals(data.signals || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load signals')
      } finally {
        setLoading(false)
      }
    }

    loadSignals()
  }, [setSignals, setLoading, setError])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Signal Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time monitoring of trading signals and market indicators
        </p>
      </div>

      <MobileDashboard />

      <div className="hidden lg:grid lg:grid-cols-2 gap-6">
        <SignalHeatMap />
        <RealtimeSignals />
      </div>

      <div className="hidden lg:block">
        <RiskMatrix />
      </div>
    </div>
  )
}
