"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"

export default function TeamPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Team Members</h1>
        <p className="text-[var(--color-text-muted)]">
          Manage your organization's users and roles.
        </p>
      </div>
      <EmptyState 
        variant="coming-soon" 
        title="Team Management Coming Soon"
        description="We are currently building the user invitation and RBAC service. This will be available in a future phase."
        dependency="GET /api/v1/users"
        status="Missing"
      />
    </div>
  )
}
