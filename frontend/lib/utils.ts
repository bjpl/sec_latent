import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleString()
}

export function formatNumber(num: number, decimals: number = 2): string {
  return num.toFixed(decimals)
}

export function getRiskColor(risk: string): string {
  const colors: Record<string, string> = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500',
  }
  return colors[risk.toLowerCase()] || 'bg-gray-500'
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'bg-green-500',
    pending: 'bg-yellow-500',
    resolved: 'bg-blue-500',
    expired: 'bg-gray-500',
  }
  return colors[status.toLowerCase()] || 'bg-gray-500'
}
