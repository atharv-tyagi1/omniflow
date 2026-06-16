"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useWorkflows } from "@/services/workflows/queries"
import { PageHeader, SkeletonCard, ErrorState, EmptyState, Badge, StatusDot, SectionCard } from "@/components/ui/dashboard-primitives"
import { Workflow, Play, CheckCircle, XCircle, RefreshCw, Clock } from "lucide-react"

const statusConfig: Record<string, { variant: any; label: string }> = {
  active: { variant: "success", label: "Active" },
  completed: { variant: "info", label: "Completed" },
  failed: { variant: "error", label: "Failed" },
  pending: { variant: "warning", label: "Pending" },
  inactive: { variant: "neutral", label: "Inactive" },
}

function WorkflowCard({ wf }: { wf: any }) {
  const cfg = statusConfig[wf.status?.toLowerCase() ?? "inactive"] ?? statusConfig.inactive
  return (
    <div className="premium-card p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/15 flex items-center justify-center">
            <Workflow className="h-4 w-4 text-violet-400" />
          </div>
          <div>
            <p className="font-semibold text-sm text-[var(--color-text-primary)]">{wf.name}</p>
            {wf.trigger_type && (
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Trigger: {wf.trigger_type}</p>
            )}
          </div>
        </div>
        <Badge variant={cfg.variant}>{cfg.label}</Badge>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { icon: <Play className="h-3.5 w-3.5 text-emerald-400" />, label: "Executions", value: wf.execution_count ?? "—" },
          { icon: <XCircle className="h-3.5 w-3.5 text-red-400" />, label: "Failures", value: wf.failure_count ?? "—" },
          { icon: <RefreshCw className="h-3.5 w-3.5 text-amber-400" />, label: "Retries", value: wf.retry_count ?? "—" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg bg-white/[0.03] p-2.5 space-y-1">
            <div className="flex items-center justify-center">{stat.icon}</div>
            <p className="text-sm font-bold text-[var(--color-text-primary)]">{stat.value}</p>
            <p className="text-[10px] text-[var(--color-text-muted)]">{stat.label}</p>
          </div>
        ))}
      </div>

      {wf.updated_at && (
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] pt-1 border-t border-white/5">
          <Clock className="h-3 w-3" />
          <span>Last updated {new Date(wf.updated_at).toLocaleString()}</span>
        </div>
      )}
    </div>
  )
}

export default function WorkflowsPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""

  const { data: workflows, isLoading, error, refetch } = useWorkflows(workspaceId)
  const list: any[] = Array.isArray(workflows) ? workflows : []

  const stats = React.useMemo(() => ({
    total: list.length,
    active: list.filter((w) => w.is_active || w.status === "active").length,
    failed: list.filter((w) => w.status === "failed").length,
  }), [list])

  return (
    <div className="space-y-6">
      <PageHeader title="Workflow Observability" subtitle="Monitor workflow execution health and history">
        <button onClick={() => refetch()} className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors">
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </PageHeader>

      {/* Summary row */}
      <div className="grid gap-4 grid-cols-3">
        {[
          { label: "Total Workflows", value: stats.total, icon: <Workflow className="h-4 w-4" /> },
          { label: "Active", value: stats.active, icon: <CheckCircle className="h-4 w-4 text-emerald-400" /> },
          { label: "Failed", value: stats.failed, icon: <XCircle className="h-4 w-4 text-red-400" /> },
        ].map((s) => (
          <div key={s.label} className="premium-card p-5 flex items-center gap-4">
            <div className="text-[var(--color-text-muted)]">{s.icon}</div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-text-primary)]">{s.value}</p>
              <p className="text-xs text-[var(--color-text-muted)]">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Workflow cards */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array(6).fill(0).map((_, i) => <SkeletonCard key={i} className="h-44" />)}
        </div>
      ) : error ? (
        <ErrorState message="Failed to load workflows." onRetry={refetch} />
      ) : list.length === 0 ? (
        <EmptyState
          title="No workflows"
          description="Create automation workflows in the Workflow Builder."
          icon={<Workflow className="h-10 w-10" />}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((wf: any) => <WorkflowCard key={wf.id} wf={wf} />)}
        </div>
      )}
    </div>
  )
}
