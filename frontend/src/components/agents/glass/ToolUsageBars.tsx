'use client'

import * as React from 'react'

interface ToolUsageItem {
  name: string
  count: number
}

interface ToolUsageBarsProps {
  data: ToolUsageItem[]
  isLoading?: boolean
  maxItems?: number
}

export function ToolUsageBars({ data, isLoading, maxItems = 5 }: ToolUsageBarsProps) {
  const displayed = data.slice(0, maxItems)
  const maxCount = displayed[0]?.count || 1
  const srLabel = `Top tools by usage: ${displayed.map((d) => `${d.name} ${d.count}`).join(', ')}`

  if (isLoading) {
    return (
      <div className="space-y-3" aria-busy="true">
        {Array(4).fill(0).map((_, i) => (
          <div key={i} className="space-y-1">
            <div className="ap-skeleton h-3 w-24 rounded" />
            <div className="ap-skeleton h-2 rounded" style={{ width: `${40 + Math.random() * 50}%` }} />
          </div>
        ))}
      </div>
    )
  }

  if (displayed.length === 0) {
    return (
      <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
        No tool calls recorded
      </p>
    )
  }

  return (
    <div role="img" aria-label={srLabel}>
      <span className="sr-only">{srLabel}</span>
      <div className="space-y-3">
        {displayed.map((item, i) => {
          const pct = Math.round((item.count / maxCount) * 100)
          return (
            <div key={item.name}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-[var(--color-text-secondary)] font-mono truncate max-w-[70%]">
                  {item.name}
                </span>
                <span className="text-xs font-semibold text-[var(--color-text-primary)]">
                  {item.count.toLocaleString()}
                </span>
              </div>
              <div
                className="h-1.5 w-full rounded-full overflow-hidden"
                style={{ background: 'rgba(99,102,241,0.12)' }}
                role="progressbar"
                aria-valuenow={pct}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${item.name}: ${item.count} calls`}
              >
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${pct}%`,
                    background: i === 0
                      ? 'linear-gradient(90deg, #6366f1, #818cf8)'
                      : i === 1
                        ? 'linear-gradient(90deg, #06b6d4, #67e8f9)'
                        : 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
                    transition: 'width 0.6s ease',
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
