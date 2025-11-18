import { create } from 'zustand'

export interface Prediction {
  id: string
  signal_id: string
  ticker: string
  prediction_type: string
  predicted_value: number
  confidence: number
  target_date: Date
  created_at: Date
  status: 'pending' | 'validated' | 'failed'
  actual_value?: number
  error?: number
}

interface PredictionState {
  predictions: Prediction[]
  loading: boolean
  error: string | null
  addPrediction: (prediction: Prediction) => void
  setPredictions: (predictions: Prediction[]) => void
  updatePrediction: (id: string, updates: Partial<Prediction>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const usePredictionStore = create<PredictionState>((set) => ({
  predictions: [],
  loading: false,
  error: null,
  addPrediction: (prediction) =>
    set((state) => ({
      predictions: [prediction, ...state.predictions],
    })),
  setPredictions: (predictions) => set({ predictions }),
  updatePrediction: (id, updates) =>
    set((state) => ({
      predictions: state.predictions.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
