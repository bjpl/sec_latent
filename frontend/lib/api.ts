const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  // Signals
  async getSignals(limit: number = 100) {
    return this.request(`/api/v1/signals?limit=${limit}`)
  }

  async getSignalById(id: string) {
    return this.request(`/api/v1/signals/${id}`)
  }

  // Predictions
  async getPredictions(ticker?: string) {
    const query = ticker ? `?ticker=${ticker}` : ''
    return this.request(`/api/v1/predictions${query}`)
  }

  async createPrediction(data: any) {
    return this.request('/api/v1/predictions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Alerts
  async getAlerts(status?: string) {
    const query = status ? `?status=${status}` : ''
    return this.request(`/api/v1/alerts${query}`)
  }

  async resolveAlert(id: string) {
    return this.request(`/api/v1/alerts/${id}/resolve`, {
      method: 'POST',
    })
  }

  // Analysis
  async analyzeSignals(tickers: string[], startDate: Date, endDate: Date) {
    return this.request('/api/v1/analysis', {
      method: 'POST',
      body: JSON.stringify({
        tickers,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      }),
    })
  }
}

export const apiClient = new ApiClient()
