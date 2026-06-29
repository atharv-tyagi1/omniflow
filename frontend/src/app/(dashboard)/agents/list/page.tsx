'use client'

import * as React from 'react'
import { useAuth } from '@/context/AuthContext'
import { useAgents } from '@/services/agents/queries'
import { useAgentPlatformStore } from '@/stores/agentPlatformStore'
import { GlassCard } from '@/components/agents/glass/GlassCard'
import { GlassEmptyState } from '@/components/agents/glass/GlassEmptyState'
import { GlassErrorState } from '@/components/agents/glass/GlassErrorState'
import { StatusChip } from '@/components/agents/glass/StatusChip'
import { CreateAgentModal } from '@/components/agents/CreateAgentModal'
import { useRouter } from 'next/navigation'
import { Plus, Bot, Search, Settings2, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function AgentsListPage() {
  const { workspace } = useAuth()
  const router = useRouter()
  const [isCreateOpen, setIsCreateOpen] = React.useState(false)
  const { data: agents = [], isLoading, error, refetch } = useAgents(workspace?.id)

  const agentSearch = useAgentPlatformStore((s) => s.agentSearchText)
  const setAgentSearch = useAgentPlatformStore((s) => s.setAgentSearch)
  const categoryFilter = useAgentPlatformStore((s) => s.agentCategoryFilter)
  const setCategory = useAgentPlatformStore((s) => s.setAgentCategory)

  const categories = React.useMemo(
    () => [...new Set(agents.map((a) => a.category))].filter(Boolean),
    [agents]
  )

  const filtered = agents.filter((a) => {
    const matchSearch = !agentSearch || a.name.toLowerCase().includes(agentSearch.toLowerCase())
    const matchCat = !categoryFilter || a.category === categoryFilter
    return matchSearch && matchCat
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Agents</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            {agents.length} agent{agents.length !== 1 ? 's' : ''} in this workspace
          </p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="ap-focus flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white
            bg-gradient-to-r from-indigo-600 to-violet-600
            shadow-[0_0_16px_rgba(99,102,241,0.25)]
            hover:shadow-[0_0_24px_rgba(99,102,241,0.4)]
            hover:-translate-y-0.5 transition-all duration-200 self-start"
          aria-label="Create a new agent"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Create Agent
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Search */}
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" aria-hidden="true" />
          <input
            type="search"
            value={agentSearch}
            onChange={(e) => setAgentSearch(e.target.value)}
            placeholder="Search agents…"
            aria-label="Search agents"
            className="ap-focus w-full rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface)] pl-9 pr-4 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
          />
        </div>

        {/* Category filter */}
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
          <button
            onClick={() => setCategory(null)}
            className={cn(
              'ap-focus px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
              !categoryFilter
                ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400'
                : 'border-[var(--color-border-subtle)] text-[var(--color-text-muted)] hover:border-[var(--color-border-strong)]'
            )}
            aria-pressed={!categoryFilter}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat === categoryFilter ? null : cat)}
              className={cn(
                'ap-focus px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                categoryFilter === cat
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400'
                  : 'border-[var(--color-border-subtle)] text-[var(--color-text-muted)] hover:border-[var(--color-border-strong)]'
              )}
              aria-pressed={categoryFilter === cat}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {error ? (
        <GlassErrorState message={(error as Error).message} onRetry={refetch} />
      ) : isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array(6).fill(0).map((_, i) => (
            <div key={i} className="ap-glass-card p-5 space-y-3" aria-hidden="true">
              <div className="ap-skeleton h-4 w-32 rounded" />
              <div className="ap-skeleton h-3 w-20 rounded" />
              <div className="ap-skeleton h-8 w-full rounded mt-4" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <GlassCard className="p-0">
          <GlassEmptyState
            title={agentSearch || categoryFilter ? 'No agents match your filter' : 'No agents yet'}
            description={
              agentSearch || categoryFilter
                ? 'Try adjusting your search or category filter.'
                : 'Build your first custom agent to get started.'
            }
            icon={<Bot className="h-12 w-12" />}
            action={
              !agentSearch && !categoryFilter ? (
                <button
                  onClick={() => setIsCreateOpen(true)}
                  className="ap-focus flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600"
                >
                  <Plus className="h-4 w-4" />
                  Create Agent
                </button>
              ) : (
                <button
                  onClick={() => { setAgentSearch(''); setCategory(null) }}
                  className="ap-focus flex items-center gap-1.5 text-sm text-[var(--color-primary-start)] hover:opacity-80"
                >
                  <X className="h-3.5 w-3.5" /> Clear filters
                </button>
              )
            }
          />
        </GlassCard>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((agent) => (
            <GlassCard
              key={agent.id}
              className="p-5 flex flex-col gap-4 cursor-pointer"
              as="div"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-bold text-[var(--color-text-primary)] truncate">{agent.name}</p>
                  <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">{agent.category}</p>
                </div>
                <StatusChip status={agent.is_active ? 'active' : 'inactive'} compact />
              </div>

              <p className="text-xs text-[var(--color-text-secondary)] flex-1">
                {agent.active_version_id ? 'Configuration published' : 'Draft — needs configuration'}
              </p>

              <div className="border-t border-[var(--color-border-subtle)] pt-3 flex gap-2">
                <button
                  onClick={() => router.push(`/agents/${agent.id}`)}
                  className="ap-focus flex-1 flex items-center justify-center gap-1.5 text-xs font-medium py-1.5 rounded-lg border border-[var(--color-border-subtle)] text-[var(--color-text-secondary)] hover:border-indigo-500 hover:text-indigo-400 transition-colors"
                  aria-label={`Configure ${agent.name}`}
                >
                  <Settings2 className="h-3.5 w-3.5" aria-hidden="true" />
                  Configure
                </button>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <CreateAgentModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  )
}
