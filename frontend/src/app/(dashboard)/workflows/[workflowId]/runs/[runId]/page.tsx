"use client"

import React, { use, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { useWorkflowRunDetails } from "@/services/workflows/queries"
import { PageShell, Badge, SkeletonCard, ErrorState } from "@/components/ui/dashboard-primitives"
import { StepViewer } from "@/components/workflows/viewer/StepViewer"
import { ArrowLeft, CheckCircle, XCircle, Play, GitMerge } from "lucide-react"

export default function RunDetailsPage({ params }: { params: Promise<{ workflowId: string, runId: string }> }) {
  const router = useRouter()
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  
  const { workflowId, runId } = use(params)
  const { data: run, isLoading, error } = useWorkflowRunDetails(workspaceId, workflowId, runId)

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null)

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "success": return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1"/> Success</Badge>
      case "failed": return <Badge variant="error"><XCircle className="h-3 w-3 mr-1"/> Failed</Badge>
      case "running": return <Badge variant="info"><Play className="h-3 w-3 mr-1 animate-pulse"/> Running</Badge>
      default: return <Badge variant="neutral">{status}</Badge>
    }
  }

  if (isLoading) {
    return (
      <PageShell>
        <div className="flex gap-4 h-[600px]">
          <SkeletonCard className="w-1/3 h-full" />
          <SkeletonCard className="flex-1 h-full" />
        </div>
      </PageShell>
    )
  }

  if (error || !run) {
    return (
      <PageShell>
        <ErrorState message="Failed to load run details." />
      </PageShell>
    )
  }

  const steps = run.steps || []
  const selectedStep = steps.find((s: any) => s.id === selectedStepId) || steps[0]

  return (
    <div className="h-screen w-full flex flex-col bg-[var(--color-bg-primary)]">
      {/* Header */}
      <header className="h-14 border-b border-[var(--color-border-subtle)] px-4 flex items-center justify-between shrink-0 bg-[var(--color-bg-primary)] z-20">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push(`/workflows/${workflowId}/runs`)}
            className="p-1.5 rounded-md hover:bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-sm font-semibold text-[var(--color-text-primary)]">Run: {run.id.substring(0,8)}</h1>
            <p className="text-[10px] text-[var(--color-text-muted)]">
              Executed {new Date(run.executed_at).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {getStatusBadge(run.status)}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex">
        {/* Left pane: Step Timeline */}
        <div className="w-80 border-r border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)] flex flex-col">
          <div className="p-4 border-b border-[var(--color-border-subtle)]">
            <h2 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Execution Steps</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {steps.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)] text-center py-8">No steps executed</p>
            ) : (
              steps.map((step: any, idx: number) => (
                <button
                  key={step.id}
                  onClick={() => setSelectedStepId(step.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    (selectedStepId ? selectedStepId === step.id : idx === 0)
                      ? "bg-violet-500/10 border-violet-500/50 shadow-md"
                      : "bg-[var(--color-bg-primary)] border-[var(--color-border-subtle)] hover:border-[var(--color-border-strong)]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-[var(--color-text-primary)] flex items-center gap-2">
                      <GitMerge className="h-3.5 w-3.5 text-violet-400" />
                      Step {idx + 1}
                    </span>
                    {step.status === "failed" ? (
                      <XCircle className="h-3.5 w-3.5 text-red-500" />
                    ) : (
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                    )}
                  </div>
                  <p className="text-[10px] text-[var(--color-text-muted)] font-mono">
                    Node: {step.node_id.substring(0,8)}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right pane: Step Details */}
        <div className="flex-1 p-6 overflow-hidden bg-[#0A0A0F]">
          {selectedStep ? (
            <StepViewer step={selectedStep} />
          ) : (
            <div className="h-full flex items-center justify-center text-[var(--color-text-muted)] text-sm">
              Select a step to view details
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
