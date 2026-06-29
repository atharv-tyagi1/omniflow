'use client'

import * as React from 'react'
import { useAuth } from '@/context/AuthContext'
import { useAllAgentRuns } from '@/services/agent-platform/queries'
import { useAgentPlatformStore } from '@/stores/agentPlatformStore'
import { GlassTable } from '@/components/agents/glass/GlassTable'
import { GlassEmptyState } from '@/components/agents/glass/GlassEmptyState'
import { GlassErrorState } from '@/components/agents/glass/GlassErrorState'
import { StatusChip } from '@/components/agents/glass/StatusChip'
import { Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

type RunStatusFilter = 'all' | 'success' | 'failed' | 'running' | 'cancelled'

const STATUS_FILTERS: { label: string; value: RunStatusFilter }[] = [
  { label: 'All',       value: 'all' },
  { label: 'Success',   value: 'success' },
  { label: 'Running',   value: 'running' },
  { label: 'Failed',    value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
]

function fmtLatency(ms: number | null) {
  if (ms == null) return '—'
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`
}

function fmtTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

export default function RunsPage() {
  const { workspace } = useAuth()
  const { data: runs = [], isLoading, error, refetch } = useAllAgentRuns(workspace?.id)

  const statusFilter = useAgentPlatformStore((s) => s.runStatusFilter)
  const setStatusFilter = useAgentPlatformStore((s) => s.setRunFilter)
  const searchText = useAgentPlatformStore((s) => s.runSearchText)
  const setSearch = useAgentPlatformStore((s) => s.setRunSearch)

  const filtered = runs.filter((r: any) => {
    const matchStatus = statusFilter === 'all' || r.status === statusFilter
    const matchSearch = !searchText || (r.agentName || '').toLowerCase().includes(searchText.toLowerCase())
    return matchStatus && matchSearch
  })

  const columns = [
    {
      key: 'agentName',
      header: 'Agent',
      render: (row: any) => (
        <span className="font-medium text-[var(--color-text-primary)] text-sm">{row.agentName}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: any) => <StatusChip status={row.status} compact />,
    },
    {
      key: 'latencyMs',
      header: 'Latency',
      render: (row: any) => (
        <span className="font-mono text-xs text-[var(--color-text-secondary)]">{fmtLatency(row.latency_ms)}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Started',
      render: (row: any) => (
        <span className="text-xs text-[var(--color-text-muted)]">{fmtTime(row.created_at)}</span>
      ),
    },
    {
      key: 'id',
      header: 'Run ID',
      render: (row: any) => (
        <span className="font-mono text-xs text-[var(--color-text-muted)] truncate max-w-[140px] block">
          {row.id?.slice(0, 8)}…
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Runs</h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
          Execution history across all agents (bounded to 10 most recent agents)
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Status chips */}
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter runs by status">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              aria-pressed={statusFilter === f.value}
              className={cn(
                'ap-focus px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                statusFilter === f.value
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400'
                  : 'border-[var(--color-border-subtle)] text-[var(--color-text-muted)] hover:border-[var(--color-border-strong)]'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <input
          type="search"
          value={searchText}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by agent name…"
          aria-label="Filter runs by agent name"
          className="ap-focus flex-1 min-w-40 max-w-xs rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
        />
      </div>

      {/* Table */}
      {error ? (
        <GlassErrorState message={(error as Error).message} onRetry={refetch} />
      ) : (
        <GlassTable
          caption="Agent run history"
          columns={columns as any}
          data={filtered}
          isLoading={isLoading}
          getRowKey={(r: any) => r.id}
          skeletonRows={8}
          emptyState={
            <GlassEmptyState
              title={statusFilter !== 'all' || searchText ? 'No runs match your filter' : 'No runs yet'}
              description="Runs will appear here once agents process requests."
              icon={<Activity className="h-10 w-10" />}
            />
          }
        />
      )}
    </div>
  )
}
