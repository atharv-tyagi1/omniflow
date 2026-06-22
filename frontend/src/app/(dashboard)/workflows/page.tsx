"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useWorkflows } from "@/services/workflows/queries"
import { PageHeader, SkeletonCard, ErrorState, EmptyState, Badge, StatusDot, SectionCard, PageShell } from "@/components/ui/dashboard-primitives"
import { Workflow, Play, CheckCircle, XCircle, RefreshCw, Clock, Plus } from "lucide-react"
import { fetchApi } from "@/lib/api-client"

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

      {wf.created_at && (
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] pt-1 border-t border-white/5">
          <Clock className="h-3 w-3" />
          <span>Created {new Date(wf.created_at).toLocaleString()}</span>
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

  const [isCreating, setIsCreating] = React.useState(false)
  const [newWorkflowName, setNewWorkflowName] = React.useState("")
  const [newWorkflowTrigger, setNewWorkflowTrigger] = React.useState("webhook")

  const handleCreate = async () => {
    if (!newWorkflowName.trim()) return
    try {
      await fetchApi(`/api/v1/workflows`, {
        method: "POST",
        body: JSON.stringify({
          name: newWorkflowName,
          trigger_type: newWorkflowTrigger
        })
      })
      setNewWorkflowName("")
      setIsCreating(false)
      refetch()
    } catch (e) {
      console.error("Failed to create workflow", e)
    }
  }

  return (
    <PageShell variant="wide">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Workflow Observability</h1>
          <p className="text-[var(--color-text-muted)] mt-2 text-sm">Monitor workflow execution health and history</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => refetch()} className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[var(--color-surface-elevated)] border border-[var(--color-border-subtle)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button 
            onClick={() => setIsCreating(!isCreating)}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-[var(--color-primary-start)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus className="h-4 w-4" />
            {isCreating ? "Cancel" : "New Workflow"}
          </button>
        </div>
      </div>

      {isCreating && (
        <div className="mb-8 p-6 premium-card border border-violet-500/20 bg-violet-500/5">
          <h3 className="text-lg font-semibold mb-4">Create Minimal Workflow</h3>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            The backend schema currently supports defining a workflow by name and trigger type. Visual node orchestration is coming in the next engine update.
          </p>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">Workflow Name</label>
              <input 
                type="text" 
                value={newWorkflowName}
                onChange={(e) => setNewWorkflowName(e.target.value)}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg px-3 py-2 text-sm"
                placeholder="e.g. Lead Qualification"
              />
            </div>
            <div className="w-48">
              <label className="block text-sm font-medium mb-1">Trigger Type</label>
              <select 
                value={newWorkflowTrigger}
                onChange={(e) => setNewWorkflowTrigger(e.target.value)}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded-lg px-3 py-2 text-sm"
              >
                <option value="webhook">Webhook</option>
                <option value="schedule">Schedule</option>
                <option value="event">Event-driven</option>
              </select>
            </div>
            <button 
              onClick={handleCreate}
              disabled={!newWorkflowName.trim()}
              className="px-6 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50"
            >
              Save Workflow
            </button>
          </div>
        </div>
      )}

      {/* Summary row */}
      <div className="grid gap-4 grid-cols-3 mb-8">
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
          description="Create your first automation workflow to get started."
          icon={<Workflow className="h-10 w-10" />}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((wf: any) => <WorkflowCard key={wf.id} wf={wf} />)}
        </div>
      )}
    </PageShell>
  )
}
