import { useQuery } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api-client'
import { Agent, AgentRunSummary } from '@/services/agents/types'

// ─── Constants ──────────────────────────────────────────────────────────────
/** Bounded snapshot: fetch runs for at most this many agents to avoid N+1 storms */
export const TOP_N_AGENTS = 10

// ─── Types ───────────────────────────────────────────────────────────────────
export type AgentRunRow = {
  agentId: string
  agentName: string
  agentCategory: string
  runId: string
  status: string
  latencyMs: number | null
  tokensUsed: number | null
  startedAt: string
  completedAt: string | null
  conversationId: string
}

export type AgentPlatformSnapshot = {
  totalAgents: number
  totalRuns: number
  successRate: number        // 0–1
  totalTokensUsed: number
  avgLatencyMs: number
  recentRuns: AgentRunRow[]  // last 20 across top-N agents, sorted by recency
  agentHealthCounts: {
    healthy: number
    running: number
    warning: number
    failed: number
  }
  agentDistribution: { category: string; count: number }[]
  mostActiveAgent: { id: string; name: string; runCount: number } | null
  runActivity: { date: string; count: number }[] // 7-day series
  isBounded: true // always true — this is a TOP_N snapshot, not a full scan
  boundedTo: number
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getLast7Days(): string[] {
  const days: string[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push(d.toISOString().slice(0, 10))
  }
  return days
}

function collapseToSnapshot(
  allAgents: Agent[],
  topAgents: Agent[],
  runResults: PromiseSettledResult<AgentRunSummary[]>[]
): AgentPlatformSnapshot {
  const days = getLast7Days()
  const activityMap = Object.fromEntries(days.map((d) => [d, 0]))

  let totalRuns = 0
  let successRuns = 0
  let totalLatency = 0
  let latencyCount = 0
  let totalTokens = 0
  const allRows: AgentRunRow[] = []
  const agentRunCounts: { id: string; name: string; count: number }[] = []

  topAgents.forEach((agent, i) => {
    const result = runResults[i]
    if (result.status !== 'fulfilled') return
    const runs = result.value || []
    agentRunCounts.push({ id: agent.id, name: agent.name, count: runs.length })
    totalRuns += runs.length

    runs.forEach((run: any) => {
      if (run.status === 'success') successRuns++

      const lat = run.latency_ms ?? run.steps?.[0]?.latency_ms ?? null
      if (lat != null) { totalLatency += lat; latencyCount++ }

      const tokens = run.decision_trace?.cost_tokens ?? run.tokens_used ?? null
      if (tokens != null) totalTokens += tokens

      // Run activity series
      const day = (run.created_at || '').slice(0, 10)
      if (activityMap[day] !== undefined) activityMap[day]++

      allRows.push({
        agentId: agent.id,
        agentName: agent.name,
        agentCategory: agent.category,
        runId: run.id,
        status: run.status,
        latencyMs: lat,
        tokensUsed: tokens,
        startedAt: run.created_at,
        completedAt: run.completed_at ?? null,
        conversationId: run.conversation_id,
      })
    })
  })

  // Agent health: healthy = active + has runs, running = has running runs, etc.
  const healthCounts = { healthy: 0, running: 0, warning: 0, failed: 0 }
  allAgents.forEach((a) => {
    if (!a.is_active) { healthCounts.warning++; return }
    if (a.active_version_id) healthCounts.healthy++
    else healthCounts.warning++
  })

  // Distribution by category
  const catMap: Record<string, number> = {}
  allAgents.forEach((a) => { catMap[a.category] = (catMap[a.category] || 0) + 1 })
  const agentDistribution = Object.entries(catMap).map(([category, count]) => ({ category, count }))

  // Most active
  const sorted = [...agentRunCounts].sort((a, b) => b.count - a.count)
  const mostActiveAgent = sorted[0]
    ? { id: sorted[0].id, name: sorted[0].name, runCount: sorted[0].count }
    : null

  // Recent runs (last 20 sorted by recency)
  const recentRuns = allRows
    .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
    .slice(0, 20)

  return {
    totalAgents: allAgents.length,
    totalRuns,
    successRate: totalRuns > 0 ? successRuns / totalRuns : 0,
    totalTokensUsed: totalTokens,
    avgLatencyMs: latencyCount > 0 ? Math.round(totalLatency / latencyCount) : 0,
    recentRuns,
    agentHealthCounts: healthCounts,
    agentDistribution,
    mostActiveAgent,
    runActivity: days.map((d) => ({ date: d, count: activityMap[d] })),
    isBounded: true,
    boundedTo: TOP_N_AGENTS,
  }
}

// ─── Primary Hook ─────────────────────────────────────────────────────────────
/**
 * useAgentPlatformSnapshot
 *
 * Single coordinated data source for the Agent Platform Overview Dashboard.
 * Bounded to TOP_N_AGENTS (10) most recently created agents to prevent N+1 storms.
 * KPI cards display "Based on 10 most recent agents" label automatically.
 */
export function useAgentPlatformSnapshot(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ['agents', workspaceId, 'snapshot'],
    queryFn: async (): Promise<AgentPlatformSnapshot> => {
      // Step 1: fetch all agents (for totalAgents count + distribution)
      const allAgents: Agent[] = await fetchApi('/api/v1/agents/') || []

      // Step 2: take TOP_N most recently created
      const topAgents = [...allAgents]
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, TOP_N_AGENTS)

      // Step 3: bounded fan-out — max TOP_N parallel requests
      const runResults = await Promise.allSettled(
        topAgents.map((agent) => fetchApi<AgentRunSummary[]>(`/api/v1/agents/${agent.id}/runs`))
      )

      // Step 4: collapse into stable snapshot
      return collapseToSnapshot(allAgents, topAgents, runResults)
    },
    enabled: !!workspaceId,
    staleTime: 30_000,
    retry: 2,
  })
}

// ─── Sub-hooks ────────────────────────────────────────────────────────────────
export function useAllAgentRuns(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ['agents', workspaceId, 'runs'],
    queryFn: async () => {
      const agents: Agent[] = await fetchApi('/api/v1/agents/') || []
      const topAgents = agents
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, TOP_N_AGENTS)

      const results = await Promise.allSettled(
        topAgents.map((a) => fetchApi<AgentRunSummary[]>(`/api/v1/agents/${a.id}/runs`).then((runs) =>
          (runs || []).map((r) => ({ ...r, agentId: a.id, agentName: a.name }))
        ))
      )
      return results
        .filter((r): r is PromiseFulfilledResult<any[]> => r.status === 'fulfilled')
        .flatMap((r) => r.value)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    },
    enabled: !!workspaceId,
    staleTime: 30_000,
    retry: 2,
  })
}
