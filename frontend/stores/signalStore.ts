import { create } from 'zustand'

export interface Signal {
  id: string
  timestamp: Date
  ticker: string
  signal_type: string
  confidence: number
  strength: number
  timeframe: string
  indicators: Record<string, number>
  metadata: Record<string, any>
}

interface SignalState {
  signals: Signal[]
  loading: boolean
  error: string | null
  addSignal: (signal: Signal) => void
  setSignals: (signals: Signal[]) => void
  clearSignals: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  loading: false,
  error: null,
  addSignal: (signal) =>
    set((state) => ({
      signals: [signal, ...state.signals].slice(0, 100), // Keep last 100
    })),
  setSignals: (signals) => set({ signals }),
  clearSignals: () => set({ signals: [] }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
