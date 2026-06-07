"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function ReportsPage() {
  const isEnabled = hasCapability("businessReports")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Executive Reports</h1>
          <p className="text-[var(--color-text-muted)]">
            Generate and schedule high-level operational reports.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Executive Reports Coming Soon"
          description="We are currently building the scheduled reporting engine. This will be available in a future phase."
          dependency="GET /api/internal/v1/business/reports"
          status="Missing"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Executive Reports</h1>
        <p className="text-[var(--color-text-muted)]">
          Generate and schedule high-level operational reports.
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
        [Executive Reports Layout]
      </div>
    </div>
  )
}
