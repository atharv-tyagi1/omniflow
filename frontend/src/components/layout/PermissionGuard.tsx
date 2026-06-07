"use client"

import * as React from "react"
import { useAuth, User } from "@/context/AuthContext"
import { ShieldAlert } from "lucide-react"
import { trackEvent } from "@/lib/telemetry"

interface PermissionGuardProps {
  children: React.ReactNode
  checkPermission: (user: User | null) => boolean
  featureName: string
}

export function PermissionGuard({ children, checkPermission, featureName }: PermissionGuardProps) {
  const { user, isLoading } = useAuth()
  
  React.useEffect(() => {
    if (!isLoading && !checkPermission(user)) {
      trackEvent("permission_denied", { feature: featureName, role: user?.role || "unauthenticated" })
    }
  }, [isLoading, user, checkPermission, featureName])

  if (isLoading) {
    return null // Handled by AuthGuard
  }

  if (!checkPermission(user)) {
    return (
      <div className="flex min-h-[400px] w-full flex-col items-center justify-center rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] mb-4">
          <ShieldAlert className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Access Denied</h2>
        <p className="mt-2 text-sm text-[var(--color-text-muted)] max-w-md">
          You do not have the required permissions to view the <strong>{featureName}</strong> dashboard. 
          Please contact your workspace administrator if you believe this is an error.
        </p>
      </div>
    )
  }

  return <>{children}</>
}
