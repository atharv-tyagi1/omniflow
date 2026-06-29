'use client'

import * as React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface GlassErrorStateProps {
  message?: string
  onRetry?: () => void
  className?: string
}

export function GlassErrorState({ message, onRetry, className }: GlassErrorStateProps) {
  const display = message ? message.slice(0, 80) : 'Something went wrong.'

  return (
    <div
      className={cn('ap-glass-card ap-error-card flex flex-col items-center justify-center py-10 px-6 text-center', className)}
      role="alert"
      aria-live="assertive"
    >
      <AlertCircle className="h-6 w-6 text-[var(--color-error)] mb-3" aria-hidden="true" />
      <p className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">Failed to load data</p>
      <p className="text-xs text-[var(--color-text-muted)] mb-4 max-w-xs">{display}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="ap-focus flex items-center gap-1.5 text-xs font-medium text-[var(--color-primary-start)] hover:opacity-80 transition-opacity"
          aria-label="Retry loading data"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Try Again
        </button>
      )}
    </div>
  )
}
