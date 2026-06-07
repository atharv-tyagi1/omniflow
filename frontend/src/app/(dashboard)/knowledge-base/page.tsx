"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function KnowledgeBasePage() {
  const isEnabled = hasCapability("knowledgeDocuments")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Knowledge Base</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your agent knowledge documents and training datasets.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Knowledge Base Coming Soon"
          description="We are currently building the document embedding and indexing service. This will be available in a future phase."
          dependency="GET /api/v1/documents"
          status="Missing"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Knowledge Base</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your agent knowledge documents and training datasets.
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
        [Knowledge Base Layout]
      </div>
    </div>
  )
}
