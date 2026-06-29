'use client'

import * as React from 'react'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import { useWorkspaceSwitchEffect } from '@/hooks/useWorkspaceSwitchEffect'

function WorkspaceSwitchOrchestrator() {
  const { workspace } = useAuth()
  const [, setActiveId] = React.useState<string | null>(null)
  useWorkspaceSwitchEffect(workspace?.id, (id) => setActiveId(id))
  return null
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)

  React.useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSidebarOpen(false)
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-background)]">
      {/* Workspace switch orchestrator (mounts hook in shell scope) */}
      <WorkspaceSwitchOrchestrator />

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <Sidebar className="h-full" />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden bg-[var(--color-background)]">
        <Topbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden canvas-scroll relative">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
