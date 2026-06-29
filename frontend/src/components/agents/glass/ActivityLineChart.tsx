'use client'

import * as React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useReducedMotion } from 'framer-motion'

interface ActivityLineChartProps {
  data: { date: string; count: number }[]
  isLoading?: boolean
}

export function ActivityLineChart({ data, isLoading }: ActivityLineChartProps) {
  const prefersReduced = useReducedMotion()

  const totalRuns = data.reduce((s, d) => s + d.count, 0)
  const srLabel = `Run activity chart over 7 days. Total: ${totalRuns} runs.`

  if (isLoading) {
    return (
      <div className="flex items-end gap-1 h-32 px-2">
        {Array(7).fill(0).map((_, i) => (
          <div key={i} className="ap-skeleton flex-1 rounded-t" style={{ height: `${30 + Math.random() * 70}%` }} />
        ))}
      </div>
    )
  }

  if (data.length === 0 || totalRuns === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--color-text-muted)] text-sm">
        No activity in the last 7 days
      </div>
    )
  }

  return (
    <div role="img" aria-label={srLabel}>
      <span className="sr-only">{srLabel}</span>
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="activityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-subtle)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => v.slice(5)}
          />
          <YAxis
            tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(15,23,42,0.95)',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 8,
              color: 'var(--color-text-primary)',
              fontSize: 12,
            }}
            formatter={(v: any) => [v, 'Runs']}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#6366f1"
            strokeWidth={2}
            fill="url(#activityGradient)"
            isAnimationActive={!prefersReduced}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
