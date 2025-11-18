'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Activity, Bell, BarChart3, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlertStore } from '@/stores/alertStore'
import { Badge } from './ui/badge'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Activity },
  { name: 'Predictions', href: '/predictions', icon: TrendingUp },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Analysis', href: '/analysis', icon: BarChart3 },
]

export function Navigation() {
  const pathname = usePathname()
  const { unreadCount } = useAlertStore()

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center">
          <Link href="/" className="flex items-center space-x-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">SEC-LATENT</span>
          </Link>
          <div className="ml-auto flex items-center space-x-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              const showBadge = item.href === '/alerts' && unreadCount > 0

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors relative',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{item.name}</span>
                  {showBadge && (
                    <Badge
                      variant="destructive"
                      className="ml-2 px-1.5 py-0.5 text-xs"
                    >
                      {unreadCount}
                    </Badge>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
