"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function ApiManagementPage() {
  const isEnabled = hasCapability("apiKeys")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">API Management</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your API keys and webhook integrations.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="API Management Portal Coming Soon"
          description="We are currently building the API Key generation and rotation service. This will be available in a future phase."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">API Management</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your API keys and webhook integrations.
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
        [API Keys Table]
      </div>
    </div>
  )
}
