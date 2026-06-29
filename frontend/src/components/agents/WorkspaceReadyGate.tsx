'use client'

import * as React from 'react'

interface WorkspaceReadyGateProps {
  activeWorkspaceId: string | null
  children: React.ReactNode
}

/**
 * WorkspaceReadyGate
 *
 * Blocks Agent Platform content from rendering until activeWorkspaceId is settled.
 * Prevents cross-workspace data flash during workspace switch Phase 3.
 */
export function WorkspaceReadyGate({ activeWorkspaceId, children }: WorkspaceReadyGateProps) {
  if (!activeWorkspaceId) {
    return (
      <div className="flex h-64 items-center justify-center" aria-live="polite" aria-label="Loading workspace">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full border-2 border-[var(--color-primary-start)] border-t-transparent animate-spin" />
          <p className="text-sm text-[var(--color-text-muted)]">Loading workspace…</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
