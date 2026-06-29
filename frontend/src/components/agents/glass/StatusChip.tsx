'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export type StatusValue = 'success' | 'running' | 'warning' | 'failed' | 'cancelled' | 'draft' | 'active' | 'inactive' | string

const STATUS_MAP: Record<string, string> = {
  success: 'ap-status-success',
  completed: 'ap-status-success',
  active: 'ap-status-success',
  healthy: 'ap-status-success',
  running: 'ap-status-running',
  pending: 'ap-status-running',
  in_progress: 'ap-status-running',
  warning: 'ap-status-warning',
  inactive: 'ap-status-warning',
  failed: 'ap-status-failed',
  error: 'ap-status-failed',
  cancelled: 'ap-status-cancelled',
  canceled: 'ap-status-cancelled',
  draft: 'ap-status-draft',
  unknown: 'ap-status-draft',
}

const STATUS_LABEL: Record<string, string> = {
  success: 'Success',
  completed: 'Success',
  active: 'Active',
  healthy: 'Healthy',
  running: 'Running',
  pending: 'Pending',
  in_progress: 'Running',
  warning: 'Warning',
  inactive: 'Inactive',
  failed: 'Failed',
  error: 'Failed',
  cancelled: 'Cancelled',
  canceled: 'Cancelled',
  draft: 'Draft',
  unknown: 'Unknown',
}

interface StatusChipProps {
  status: StatusValue
  className?: string
  compact?: boolean
}

export function StatusChip({ status, className, compact }: StatusChipProps) {
  const normalized = status?.toLowerCase?.() ?? 'unknown'
  const chipClass = STATUS_MAP[normalized] ?? 'ap-status-draft'
  const label = STATUS_LABEL[normalized] ?? status

  return (
    <span
      className={cn('ap-status-chip', chipClass, compact && 'text-[10px] px-2 py-0.5', className)}
      aria-label={`Status: ${label}`}
      role="status"
    >
      {label}
    </span>
  )
}
