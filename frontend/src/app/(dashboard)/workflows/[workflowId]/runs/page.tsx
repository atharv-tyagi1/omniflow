"use client"

import React, { use } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { useWorkflowRuns } from "@/services/workflows/queries"
import { PageShell, Badge, SkeletonCard, ErrorState, EmptyState } from "@/components/ui/dashboard-primitives"
import { ArrowLeft, Clock, History, CheckCircle, XCircle, Play } from "lucide-react"

export default function WorkflowRunsPage({ params }: { params: Promise<{ workflowId: string }> }) {
  const router = useRouter()
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  
  const { workflowId } = use(params)
  const { data: runs, isLoading, error } = useWorkflowRuns(workspaceId, workflowId)

  const list = Array.isArray(runs) ? runs : []

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "success": return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1"/> Success</Badge>
      case "failed": return <Badge variant="error"><XCircle className="h-3 w-3 mr-1"/> Failed</Badge>
      case "running": return <Badge variant="info"><Play className="h-3 w-3 mr-1 animate-pulse"/> Running</Badge>
      default: return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <PageShell>
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push("/workflows")}
          className="p-2 rounded-md hover:bg-white/10 text-[var(--color-text-muted)] transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Execution History</h1>
          <p className="text-[var(--color-text-muted)] mt-1 text-sm">View and debug past workflow runs</p>
        </div>
      </div>

      <div className="premium-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            <SkeletonCard className="h-12 w-full" />
            <SkeletonCard className="h-12 w-full" />
            <SkeletonCard className="h-12 w-full" />
          </div>
        ) : error ? (
          <div className="p-8"><ErrorState message="Failed to load run history." /></div>
        ) : list.length === 0 ? (
          <div className="p-8">
            <EmptyState title="No Executions Yet" description="This workflow has not been triggered yet." icon={<History className="h-10 w-10"/>} />
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 border-b border-white/10 text-[var(--color-text-muted)]">
              <tr>
                <th className="px-6 py-4 font-medium">Run ID</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Execution Time</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {list.map((run: any) => (
                <tr key={run.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-[var(--color-text-primary)]">
                    {run.id}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(run.status)}
                  </td>
                  <td className="px-6 py-4 text-[var(--color-text-muted)]">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5" />
                      {new Date(run.executed_at).toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link 
                      href={`/workflows/${workflowId}/runs/${run.id}`}
                      className="text-violet-400 hover:text-violet-300 font-medium bg-violet-500/10 px-3 py-1.5 rounded-md"
                    >
                      View Steps
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </PageShell>
  )
}
