"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"
import { Lightbulb } from "lucide-react"

export default function BusinessAnalystPage() {
  const isEnabled = hasCapability("businessInsights")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Business Analyst</h1>
          <p className="text-[var(--color-text-muted)]">
            AI-driven business intelligence and actionable insights.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Business Insights Engine Coming Soon"
          description="We are currently fine-tuning the deterministic insight generation engine for Phase 14. This feature will be available shortly."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Business Analyst</h1>
        <p className="text-[var(--color-text-muted)]">
          AI-driven business intelligence and actionable insights.
        </p>
      </div>
      
      {/* Real implementation will go here once backend is available */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="col-span-full rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[600px] flex items-center justify-center text-[var(--color-text-muted)]">
          [Business Insights Dashboard]
        </div>
      </div>
    </div>
  )
}
