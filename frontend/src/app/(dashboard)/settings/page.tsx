"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Workspace Settings</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your organization settings and preferences.
        </p>
      </div>
      <EmptyState 
        variant="coming-soon" 
        title="Settings Module Coming Soon"
        description="We are currently building the workspace configuration service. This will be available in a future phase."
        dependency="GET /api/v1/workspaces/{id}"
        status="Missing"
      />
    </div>
  )
}
