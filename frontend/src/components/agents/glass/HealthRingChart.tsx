'use client'

import * as React from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { useReducedMotion } from 'framer-motion'

const COLORS = {
  healthy: '#4ade80',
  running: '#818cf8',
  warning: '#fbbf24',
  failed:  '#f87171',
}

interface HealthRingChartProps {
  data: { healthy: number; running: number; warning: number; failed: number }
  isLoading?: boolean
}

export function HealthRingChart({ data, isLoading }: HealthRingChartProps) {
  const prefersReduced = useReducedMotion()
  const total = data.healthy + data.running + data.warning + data.failed

  const chartData = [
    { name: 'Healthy', value: data.healthy, color: COLORS.healthy },
    { name: 'Running', value: data.running, color: COLORS.running },
    { name: 'Warning', value: data.warning, color: COLORS.warning },
    { name: 'Failed',  value: data.failed,  color: COLORS.failed },
  ].filter((d) => d.value > 0)

  const srLabel = `Agent health chart: ${data.healthy} healthy (${total > 0 ? Math.round(data.healthy/total*100) : 0}%), ${data.running} running, ${data.warning} warning, ${data.failed} failed`

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="ap-skeleton h-32 w-32 rounded-full" />
      </div>
    )
  }

  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-[var(--color-text-muted)] text-sm">
        No agents
      </div>
    )
  }

  return (
    <div role="img" aria-label={srLabel}>
      <span className="sr-only">{srLabel}</span>
      <div className="relative">
        <ResponsiveContainer width="100%" height={160}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={3}
              dataKey="value"
              isAnimationActive={!prefersReduced}
              strokeWidth={0}
            >
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'rgba(15,23,42,0.95)',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: 8,
                color: 'var(--color-text-primary)',
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold text-[var(--color-text-primary)]">{total}</span>
          <span className="text-xs text-[var(--color-text-muted)]">Total</span>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {[
          { label: 'Healthy', count: data.healthy, color: COLORS.healthy },
          { label: 'Running', count: data.running, color: COLORS.running },
          { label: 'Warning', count: data.warning, color: COLORS.warning },
          { label: 'Failed',  count: data.failed,  color: COLORS.failed },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: item.color }} aria-hidden="true" />
            <span>{item.label}</span>
            <span className="ml-auto font-semibold text-[var(--color-text-primary)]">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
