"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function AgentsPage() {
  const isEnabled = hasCapability("agentMetrics")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">AI Agents</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your autonomous customer service agents.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="AI Agents Module Coming Soon"
          description="We are currently building the agent lifecycle and metrics service. This will be available in a future phase."
          dependency="GET /api/v1/agents"
          status="Missing"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">AI Agents</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your autonomous customer service agents.
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
        [AI Agents Dashboard Layout]
      </div>
    </div>
  )
}
