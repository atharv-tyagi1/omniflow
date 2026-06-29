'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface GlassEmptyStateProps {
  title: string
  description?: string
  icon?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export function GlassEmptyState({ title, description, icon, action, className }: GlassEmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-6 text-center', className)}>
      {icon && (
        <div className="mb-4 text-[var(--color-text-muted)] opacity-50" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-[var(--color-text-primary)] mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-[var(--color-text-muted)] max-w-xs mb-4">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  )
}
