'use client'

import * as React from 'react'
import { useAuth } from '@/context/AuthContext'
import { useAgentPlatformSnapshot, TOP_N_AGENTS } from '@/services/agent-platform/queries'
import { GlassCard } from '@/components/agents/glass/GlassCard'
import { GlassMetricCard } from '@/components/agents/glass/GlassMetricCard'
import { GlassTable } from '@/components/agents/glass/GlassTable'
import { GlassEmptyState } from '@/components/agents/glass/GlassEmptyState'
import { GlassErrorState } from '@/components/agents/glass/GlassErrorState'
import { StatusChip } from '@/components/agents/glass/StatusChip'
import { HealthRingChart } from '@/components/agents/glass/HealthRingChart'
import { ActivityLineChart } from '@/components/agents/glass/ActivityLineChart'
import { ToolUsageBars } from '@/components/agents/glass/ToolUsageBars'
import { Bot, Activity, CheckCircle, Zap, Clock, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import type { AgentRunRow } from '@/services/agent-platform/queries'

// ─── Helpers ─────────────────────────────────────────────────────────────────
function fmtLatency(ms: number | null) {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function fmtTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function aggregateTools(runs: AgentRunRow[]): { name: string; count: number }[] {
  const counts: Record<string, number> = {}
  runs.forEach((r: any) => {
    const calls = r.tool_calls || []
    calls.forEach((c: any) => {
      const name = c?.tool_name || c?.type || 'unknown'
      counts[name] = (counts[name] || 0) + 1
    })
  })
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}

const SCOPE_LABEL = `Based on ${TOP_N_AGENTS} most recent agents`

// ─── Columns ─────────────────────────────────────────────────────────────────
const RUN_COLUMNS = [
  {
    key: 'agentName',
    header: 'Agent',
    render: (row: AgentRunRow) => (
      <div>
        <p className="font-medium text-[var(--color-text-primary)] text-sm">{row.agentName}</p>
        <p className="text-xs text-[var(--color-text-muted)]">{row.agentCategory}</p>
      </div>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    render: (row: AgentRunRow) => <StatusChip status={row.status} compact />,
  },
  {
    key: 'latencyMs',
    header: 'Latency',
    render: (row: AgentRunRow) => (
      <span className="font-mono text-xs text-[var(--color-text-secondary)]">
        {fmtLatency(row.latencyMs)}
      </span>
    ),
  },
  {
    key: 'startedAt',
    header: 'Started',
    render: (row: AgentRunRow) => (
      <span className="text-xs text-[var(--color-text-muted)]">{fmtTime(row.startedAt)}</span>
    ),
  },
  {
    key: 'action',
    header: '',
    render: (row: AgentRunRow) => (
      <Link
        href={`/agents/${row.agentId}`}
        className="ap-focus inline-flex items-center gap-1 text-xs text-[var(--color-primary-start)] hover:opacity-80 transition-opacity"
        aria-label={`View ${row.agentName} details`}
      >
        <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
      </Link>
    ),
  },
]

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function AgentPlatformOverview() {
  const { workspace } = useAuth()
  const { data, isLoading, error, refetch } = useAgentPlatformSnapshot(workspace?.id)

  const toolUsage = React.useMemo(
    () => (data ? aggregateTools(data.recentRuns) : []),
    [data]
  )

  return (
    <div className="space-y-6">
      {/* ── KPI Cards ── */}
      <section aria-label="Key Performance Indicators">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <GlassMetricCard
            title="Total Agents"
            value={data?.totalAgents ?? '—'}
            icon={<Bot className="h-4 w-4" />}
            isLoading={isLoading}
          />
          <GlassMetricCard
            title="Total Runs"
            value={data?.totalRuns?.toLocaleString() ?? '—'}
            icon={<Activity className="h-4 w-4" />}
            isLoading={isLoading}
            scopeLabel={SCOPE_LABEL}
          />
          <GlassMetricCard
            title="Success Rate"
            value={data ? `${(data.successRate * 100).toFixed(1)}%` : '—'}
            icon={<CheckCircle className="h-4 w-4" />}
            isLoading={isLoading}
            scopeLabel={SCOPE_LABEL}
          />
          <GlassMetricCard
            title="Total Tokens"
            value={data ? `${(data.totalTokensUsed / 1_000_000).toFixed(1)}M` : '—'}
            icon={<Zap className="h-4 w-4" />}
            isLoading={isLoading}
            scopeLabel={SCOPE_LABEL}
          />
          <GlassMetricCard
            title="Avg Latency"
            value={data ? fmtLatency(data.avgLatencyMs) : '—'}
            icon={<Clock className="h-4 w-4" />}
            isLoading={isLoading}
            scopeLabel={SCOPE_LABEL}
          />
        </div>
      </section>

      {/* ── Main Content ── */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Left: Recent Runs Table (2/3) */}
        <section className="xl:col-span-2 space-y-4" aria-label="Recent Agent Runs">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Recent Agent Runs</h2>
            <Link href="/agents/runs" className="ap-focus text-xs text-[var(--color-primary-start)] hover:opacity-80 transition-opacity">
              View all runs →
            </Link>
          </div>

          {error ? (
            <GlassErrorState
              message={(error as Error).message}
              onRetry={refetch}
            />
          ) : (
            <GlassTable
              caption="Recent agent runs"
              columns={RUN_COLUMNS as any}
              data={data?.recentRuns ?? []}
              isLoading={isLoading}
              getRowKey={(r) => r.runId}
              emptyState={
                <GlassEmptyState
                  title="No runs yet"
                  description="Agent runs will appear here once your agents start processing requests."
                  icon={<Activity className="h-10 w-10" />}
                />
              }
            />
          )}
        </section>

        {/* Right: Insight Cards (1/3) */}
        <section className="space-y-4" aria-label="Insights">
          {/* Agent Health */}
          <GlassCard className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Agent Health</h2>
              <Link href="/agents/list" className="ap-focus text-xs text-[var(--color-primary-start)] hover:opacity-80 transition-opacity">
                View all →
              </Link>
            </div>
            <HealthRingChart
              data={data?.agentHealthCounts ?? { healthy: 0, running: 0, warning: 0, failed: 0 }}
              isLoading={isLoading}
            />
          </GlassCard>

          {/* Most Active Agent */}
          {(isLoading || data?.mostActiveAgent) && (
            <GlassCard className="p-5">
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">Most Active Agent</h2>
              {isLoading ? (
                <div className="space-y-2">
                  <div className="ap-skeleton h-4 w-32 rounded" />
                  <div className="ap-skeleton h-3 w-20 rounded" />
                </div>
              ) : data?.mostActiveAgent ? (
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-indigo-400" aria-hidden="true" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
                      {data.mostActiveAgent.name}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {data.mostActiveAgent.runCount.toLocaleString()} runs
                    </p>
                  </div>
                </div>
              ) : null}
            </GlassCard>
          )}

          {/* Top Tools */}
          <GlassCard className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Top Tools by Usage</h2>
            </div>
            <ToolUsageBars data={toolUsage} isLoading={isLoading} />
          </GlassCard>
        </section>
      </div>

      {/* ── Lower Analytics ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Run Activity */}
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Run Activity</h2>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Last 7 days &bull; <span className="italic">{SCOPE_LABEL}</span></p>
            </div>
          </div>
          <ActivityLineChart data={data?.runActivity ?? []} isLoading={isLoading} />
        </GlassCard>

        {/* Agent Distribution */}
        <GlassCard className="p-5">
          <h2 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Agent Distribution</h2>
          {isLoading ? (
            <div className="space-y-3">
              {Array(4).fill(0).map((_, i) => (
                <div key={i} className="flex gap-3">
                  <div className="ap-skeleton h-4 w-24 rounded" />
                  <div className="ap-skeleton h-4 flex-1 rounded" />
                </div>
              ))}
            </div>
          ) : (data?.agentDistribution?.length ?? 0) === 0 ? (
            <GlassEmptyState
              title="No agents"
              description="Create your first agent to see distribution."
              icon={<Bot className="h-8 w-8" />}
            />
          ) : (
            <ToolUsageBars
              data={(data?.agentDistribution ?? []).map((d) => ({ name: d.category, count: d.count }))}
            />
          )}
        </GlassCard>
      </div>
    </div>
  )
}
