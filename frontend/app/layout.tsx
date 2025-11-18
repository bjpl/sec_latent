import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/Navigation'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SEC-LATENT - Signal Monitoring',
  description: 'Real-time signal monitoring and prediction system',
  manifest: '/manifest.json',
  themeColor: '#3b82f6',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3b82f6" />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Navigation />
          <main className="flex-1 container mx-auto px-4 py-6">
            {children}
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  )
}
