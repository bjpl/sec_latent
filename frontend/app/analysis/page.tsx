'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { BarChart3, Download, Play } from 'lucide-react'

export default function AnalysisPage() {
  const [selectedTickers, setSelectedTickers] = useState<string[]>([])
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const popularTickers = [
    'AAPL',
    'GOOGL',
    'MSFT',
    'AMZN',
    'TSLA',
    'NVDA',
    'META',
    'AMD',
  ]

  const toggleTicker = (ticker: string) => {
    setSelectedTickers((prev) =>
      prev.includes(ticker)
        ? prev.filter((t) => t !== ticker)
        : [...prev, ticker]
    )
  }

  const runAnalysis = async () => {
    if (selectedTickers.length === 0) {
      toast({
        title: 'No Tickers Selected',
        description: 'Please select at least one ticker to analyze',
        variant: 'destructive',
      })
      return
    }

    try {
      setLoading(true)
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - 30)

      const result = await apiClient.analyzeSignals(
        selectedTickers,
        startDate,
        endDate
      )
      setAnalysisResult(result)

      toast({
        title: 'Analysis Complete',
        description: `Analyzed ${selectedTickers.length} ticker(s)`,
      })
    } catch (err) {
      toast({
        title: 'Analysis Failed',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const exportReport = () => {
    if (!analysisResult) return

    const dataStr = JSON.stringify(analysisResult, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis-${new Date().toISOString()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Signal Analysis</h1>
        <p className="text-muted-foreground">
          Select tickers and generate custom analysis reports
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Tickers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {popularTickers.map((ticker) => (
              <Badge
                key={ticker}
                variant={
                  selectedTickers.includes(ticker) ? 'default' : 'outline'
                }
                className="cursor-pointer text-sm py-2 px-3"
                onClick={() => toggleTicker(ticker)}
              >
                {ticker}
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={runAnalysis} disabled={loading}>
              <Play className="h-4 w-4 mr-2" />
              {loading ? 'Analyzing...' : 'Run Analysis'}
            </Button>
            {analysisResult && (
              <Button variant="outline" onClick={exportReport}>
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {analysisResult && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Signals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  <div className="text-2xl font-bold">
                    {analysisResult.total_signals || 0}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Avg Confidence
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(
                    (analysisResult.avg_confidence || 0) * 100
                  ).toFixed(1)}
                  %
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Avg Strength
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((analysisResult.avg_strength || 0) * 100).toFixed(1)}%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Timeframe
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">30d</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {selectedTickers.map((ticker) => (
                  <div
                    key={ticker}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div>
                      <div className="font-semibold mb-1">{ticker}</div>
                      <div className="text-sm text-muted-foreground">
                        {analysisResult.ticker_stats?.[ticker]?.signal_count ||
                          0}{' '}
                        signals analyzed
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge
                        variant={
                          (analysisResult.ticker_stats?.[ticker]
                            ?.avg_strength || 0) > 0.6
                            ? 'default'
                            : 'secondary'
                        }
                      >
                        {(
                          (analysisResult.ticker_stats?.[ticker]
                            ?.avg_strength || 0) * 100
                        ).toFixed(1)}
                        % strength
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
