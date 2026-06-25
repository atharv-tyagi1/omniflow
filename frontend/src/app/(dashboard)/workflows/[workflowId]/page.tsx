"use client"

import React, { use } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { useWorkflowDraft, usePublishWorkflow } from "@/services/workflows/builder"
import { WorkflowCanvas } from "@/components/workflows/builder/WorkflowCanvas"
import { PageShell } from "@/components/ui/dashboard-primitives"
import { Loader2, ArrowLeft, Globe, AlertCircle } from "lucide-react"

export default function WorkflowBuilderPage({ params }: { params: Promise<{ workflowId: string }> }) {
  const router = useRouter()
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  
  const { workflowId } = use(params)
  const { data, isLoading, error } = useWorkflowDraft(workspaceId, workflowId)
  const publishMutation = usePublishWorkflow(workspaceId, workflowId)

  if (isLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-[var(--color-bg-primary)]">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <PageShell>
        <div className="flex flex-col items-center justify-center h-[50vh] space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500" />
          <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Failed to load workflow</h2>
          <button onClick={() => router.back()} className="text-violet-400 hover:text-violet-300">
            Go Back
          </button>
        </div>
      </PageShell>
    )
  }

  const handlePublish = async () => {
    try {
      await publishMutation.mutateAsync()
      alert("Workflow published successfully!")
    } catch (e) {
      console.error(e)
      alert("Failed to publish workflow")
    }
  }

  // Transform backend API format to ReactFlow format
  const initialNodes = data.nodes.map(n => ({
    id: n.id,
    type: n.type,
    position: { x: n.position_x, y: n.position_y },
    data: { config: n.config }
  }))

  const initialEdges = data.edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.source_handle,
    targetHandle: e.target_handle
  }))

  return (
    <div className="h-screen w-full flex flex-col bg-[var(--color-bg-primary)]">
      {/* Header */}
      <header className="h-14 border-b border-white/10 px-4 flex items-center justify-between shrink-0 bg-[var(--color-bg-primary)] z-20">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push("/workflows")}
            className="p-1.5 rounded-md hover:bg-white/10 text-[var(--color-text-muted)] hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-sm font-semibold text-[var(--color-text-primary)]">{data.workflow.name}</h1>
            <p className="text-[10px] text-[var(--color-text-muted)]">
              {data.workflow.active_version_id ? `Active Version ID: ${data.workflow.active_version_id.substring(0,8)}` : "Draft - Not Published"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--color-text-muted)]">
            {publishMutation.isPending ? "Publishing..." : "Autosaved"}
          </span>
          <button
            onClick={handlePublish}
            disabled={publishMutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-md transition-colors shadow-sm"
          >
            <Globe className="h-3.5 w-3.5" />
            Publish
          </button>
        </div>
      </header>

      {/* Canvas Area */}
      <main className="flex-1 relative">
        <WorkflowCanvas 
          workspaceId={workspaceId} 
          workflowId={workflowId} 
          initialNodes={initialNodes}
          initialEdges={initialEdges}
        />
      </main>
    </div>
  )
}
