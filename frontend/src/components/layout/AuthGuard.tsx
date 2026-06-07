"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useRouter } from "next/navigation"

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const [authResolved, setAuthResolved] = React.useState(false)

  React.useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push("/login")
      } else {
        setAuthResolved(true)
      }
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading || !authResolved) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[var(--color-background)]">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-surface-elevated)] border-t-[var(--color-primary-start)]" />
          <p className="text-sm text-[var(--color-text-muted)] font-medium">Authenticating...</p>
        </div>
      </div>
    )
  }

  // Once resolved, render the children
  return <>{children}</>
}
