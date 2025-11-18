import { create } from 'zustand'

export interface Alert {
  id: string
  signal_id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  ticker: string
  created_at: Date
  status: 'active' | 'resolved' | 'expired'
  metadata: Record<string, any>
}

interface AlertState {
  alerts: Alert[]
  unreadCount: number
  loading: boolean
  error: string | null
  addAlert: (alert: Alert) => void
  setAlerts: (alerts: Alert[]) => void
  markAsRead: (id: string) => void
  resolveAlert: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],
  unreadCount: 0,
  loading: false,
  error: null,
  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts],
      unreadCount: state.unreadCount + 1,
    })),
  setAlerts: (alerts) =>
    set({
      alerts,
      unreadCount: alerts.filter((a) => a.status === 'active').length,
    }),
  markAsRead: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) => (a.id === id ? { ...a } : a)),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),
  resolveAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, status: 'resolved' as const } : a
      ),
    })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
