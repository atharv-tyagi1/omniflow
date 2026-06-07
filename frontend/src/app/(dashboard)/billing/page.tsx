"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"

export default function BillingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Billing & Subscription</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your subscription plan and billing methods.
        </p>
      </div>
      <EmptyState 
        variant="coming-soon" 
        title="Billing Portal Coming Soon"
        description="We are currently building the Stripe integration. This will be available in a future phase."
        dependency="GET /api/v1/workspaces/{id}/billing"
        status="Missing"
      />
    </div>
  )
}
