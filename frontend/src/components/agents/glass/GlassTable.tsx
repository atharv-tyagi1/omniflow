'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export type Column<T> = {
  key: keyof T | string
  header: string
  className?: string
  render?: (row: T) => React.ReactNode
}

interface GlassTableProps<T> {
  columns: Column<T>[]
  data: T[]
  isLoading?: boolean
  skeletonRows?: number
  emptyState?: React.ReactNode
  errorState?: React.ReactNode
  getRowKey: (row: T) => string
  onRowClick?: (row: T) => void
  className?: string
  caption?: string
}

export function GlassTable<T>({
  columns,
  data,
  isLoading,
  skeletonRows = 5,
  emptyState,
  errorState,
  getRowKey,
  onRowClick,
  className,
  caption,
}: GlassTableProps<T>) {
  return (
    <div className={cn('ap-glass-table w-full overflow-x-auto', className)} role="region">
      <table className="w-full text-sm" role="table" aria-label={caption}>
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="ap-glass-table-header">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                scope="col"
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]',
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            Array(skeletonRows).fill(0).map((_, i) => (
              <tr key={i} className="ap-glass-table-row" aria-hidden="true">
                {columns.map((col) => (
                  <td key={String(col.key)} className="px-4 py-3">
                    <div className="ap-skeleton h-4 rounded" style={{ width: `${60 + Math.random() * 30}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : errorState ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12">
                {errorState}
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12">
                {emptyState}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={getRowKey(row)}
                className={cn(
                  'ap-glass-table-row',
                  onRowClick && 'cursor-pointer ap-focus'
                )}
                onClick={() => onRowClick?.(row)}
                onKeyDown={(e) => {
                  if (onRowClick && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault()
                    onRowClick(row)
                  }
                }}
                tabIndex={onRowClick ? 0 : undefined}
                role={onRowClick ? 'button' : 'row'}
              >
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className={cn('px-4 py-3 text-[var(--color-text-secondary)]', col.className)}
                  >
                    {col.render
                      ? col.render(row)
                      : String((row as any)[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
