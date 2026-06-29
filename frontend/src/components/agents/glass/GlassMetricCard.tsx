'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface GlassMetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: number | null   // percent change, positive = up
  trendLabel?: string
  icon?: React.ReactNode
  className?: string
  isLoading?: boolean
  scopeLabel?: string     // e.g. "Based on 10 most recent agents"
}

export function GlassMetricCard({
  title,
  value,
  subtitle,
  trend,
  trendLabel,
  icon,
  className,
  isLoading,
  scopeLabel,
}: GlassMetricCardProps) {
  if (isLoading) {
    return (
      <div className={cn('ap-glass-metric p-5 flex flex-col gap-3', className)} aria-busy="true">
        <div className="ap-skeleton h-3 w-24 rounded" />
        <div className="ap-skeleton h-8 w-32 rounded" />
        <div className="ap-skeleton h-3 w-20 rounded" />
      </div>
    )
  }

  const trendPositive = trend != null && trend > 0
  const trendNegative = trend != null && trend < 0

  const ariaLabel = `${title}: ${value}${trend != null ? `, ${Math.abs(trend)}% ${trendPositive ? 'increase' : 'decrease'}` : ''}`

  return (
    <div
      className={cn('ap-glass-metric p-5 flex flex-col gap-2', className)}
      aria-label={ariaLabel}
      role="region"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          {title}
        </span>
        {icon && (
          <span className="text-[var(--color-primary-start)] opacity-70" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>

      <p className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">
        {value}
      </p>

      <div className="flex flex-col gap-1">
        {trend != null && (
          <div className={cn(
            'flex items-center gap-1 text-xs font-medium',
            trendPositive ? 'text-emerald-400' : trendNegative ? 'text-red-400' : 'text-[var(--color-text-muted)]'
          )}>
            {trendPositive ? <TrendingUp className="h-3.5 w-3.5" /> :
             trendNegative ? <TrendingDown className="h-3.5 w-3.5" /> :
             <Minus className="h-3.5 w-3.5" />}
            <span>
              {trend > 0 ? '+' : ''}{trend}%{trendLabel ? ` ${trendLabel}` : ' vs last month'}
            </span>
          </div>
        )}
        {subtitle && (
          <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
        )}
        {scopeLabel && (
          <p className="text-[10px] text-[var(--color-text-muted)] opacity-60 italic">{scopeLabel}</p>
        )}
      </div>
    </div>
  )
}
