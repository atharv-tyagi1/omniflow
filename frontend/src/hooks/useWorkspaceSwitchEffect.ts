'use client'

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAgentPlatformStore } from '@/stores/agentPlatformStore'

/**
 * useWorkspaceSwitchEffect
 *
 * Orchestrates a strict 3-phase workspace switch for the Agent Platform:
 *   Phase 1 — CANCEL: cancel all inflight queries for the previous workspace
 *   Phase 2 — RESET:  reset React Query cache + Zustand UI state
 *   Phase 3 — GATE:   signals WorkspaceReadyGate to allow new workspace rendering
 */
export function useWorkspaceSwitchEffect(
  workspaceId: string | undefined,
  onSettled: (id: string) => void
) {
  const queryClient = useQueryClient()
  const resetStore = useAgentPlatformStore((s) => s.reset)
  const prevWorkspaceId = useRef<string | undefined>(undefined)

  useEffect(() => {
    if (!workspaceId) return
    if (prevWorkspaceId.current === workspaceId) return

    const previous = prevWorkspaceId.current
    prevWorkspaceId.current = workspaceId

    if (!previous) {
      // First mount — no switch, just settle
      onSettled(workspaceId)
      return
    }

    // ── Phase 1: CANCEL inflight queries for previous workspace ──
    queryClient.cancelQueries({ queryKey: ['agents', previous] })
    queryClient.cancelQueries({ queryKey: ['api-keys', previous] })

    // ── Phase 2: RESET cache + Zustand UI state ──
    queryClient.resetQueries({ queryKey: ['agents', previous] })
    queryClient.resetQueries({ queryKey: ['api-keys', previous] })
    resetStore()

    // ── Phase 3: GATE — settle new workspaceId ──
    onSettled(workspaceId)
  }, [workspaceId, queryClient, resetStore, onSettled])
}
