"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { PageShell, PageHeader } from "@/components/ui/dashboard-primitives"

export default function BillingPage() {
  return (
    <PageShell variant="standard">
      <div className="space-y-6 w-full">
        <PageHeader 
          title="Billing & Usage"
          subtitle="Manage your subscription plan and monitor API usage."
        />

        <div className="rounded-xl border border-[var(--color-error)]/20 bg-[var(--color-error)]/10 p-4 mb-8">
          <h3 className="text-sm font-medium text-[var(--color-error)] mb-1 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            Implementation Gap
          </h3>
          <p className="text-sm text-[var(--color-error)] opacity-90">
            Stripe billing and usage limits are not currently implemented in the backend. 
          </p>
        </div>

        <EmptyState 
          variant="coming-soon" 
          title="Stripe Billing Unavailable"
          description="We are integrating Stripe for subscription management and usage tracking. For now, all workspaces have unlimited access."
          dependency="Stripe API + Backend Webhooks"
          status="Missing"
        />
      </div>
    </PageShell>
  )
}
