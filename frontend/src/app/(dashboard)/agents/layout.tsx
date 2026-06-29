'use client'

import * as React from 'react'
import './agent-platform.css'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { useWorkspaceSwitchEffect } from '@/hooks/useWorkspaceSwitchEffect'
import { WorkspaceReadyGate } from '@/components/agents/WorkspaceReadyGate'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Plus } from 'lucide-react'

const TABS = [
  { label: 'Overview',  href: '/agents' },
  { label: 'Agents',    href: '/agents/list' },
  { label: 'Runs',      href: '/agents/runs' },
  { label: 'Knowledge', href: '/agents/knowledge' },
  { label: 'API Keys',  href: '/agents/api-keys' },
  { label: 'Settings',  href: '/agents/settings' },
]

export default function AgentPlatformLayout({ children }: { children: React.ReactNode }) {
  const { workspace } = useAuth()
  const pathname = usePathname()
  const prefersReduced = useReducedMotion()
  const [activeWorkspaceId, setActiveWorkspaceId] = React.useState<string | null>(null)

  useWorkspaceSwitchEffect(workspace?.id, (id) => setActiveWorkspaceId(id))

  const activeTab = TABS.findIndex((t) => {
    if (t.href === '/agents') return pathname === '/agents'
    return pathname.startsWith(t.href)
  })

  return (
    <div className="min-h-full">
      {/* ── Platform Header ── */}
      <div className="sticky top-0 z-20 border-b border-[var(--color-border-subtle)] bg-[var(--color-background)]/90 backdrop-blur-lg">
        <div className="px-6 py-4">
          {/* Title row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-[0_0_16px_rgba(99,102,241,0.4)]">
                <span className="text-white text-sm font-bold">AI</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-[var(--color-text-primary)] leading-none">
                  Agent Platform
                </h1>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  {workspace?.name || 'Workspace'} &bull; Enterprise
                </p>
              </div>
            </div>

            <Link
              href="/agents/list"
              className="ap-focus flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white
                bg-gradient-to-r from-indigo-600 to-violet-600
                shadow-[0_0_16px_rgba(99,102,241,0.3)]
                hover:shadow-[0_0_24px_rgba(99,102,241,0.5)]
                hover:-translate-y-0.5 transition-all duration-200"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Create Agent
            </Link>
          </div>

          {/* Tab strip */}
          <nav
            role="tablist"
            aria-label="Agent Platform sections"
            className="flex items-center gap-1"
          >
            {TABS.map((tab, i) => {
              const isActive = i === activeTab
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  role="tab"
                  aria-selected={isActive}
                  className={cn(
                    'ap-tab ap-focus relative',
                    isActive && 'ap-tab-active'
                  )}
                  onKeyDown={(e) => {
                    // Arrow key navigation
                    if (e.key === 'ArrowRight') {
                      const next = TABS[(i + 1) % TABS.length]
                      ;(document.querySelector(`[href="${next.href}"]`) as HTMLElement)?.focus()
                    }
                    if (e.key === 'ArrowLeft') {
                      const prev = TABS[(i - 1 + TABS.length) % TABS.length]
                      ;(document.querySelector(`[href="${prev.href}"]`) as HTMLElement)?.focus()
                    }
                  }}
                >
                  {tab.label}
                  {isActive && (
                    <motion.div
                      layoutId="ap-tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-400 to-violet-400 rounded-full"
                      transition={prefersReduced ? { duration: 0 } : { type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* ── Content ── */}
      <div role="tabpanel" aria-label="Agent Platform content" className="p-6">
        <WorkspaceReadyGate activeWorkspaceId={activeWorkspaceId}>
          {children}
        </WorkspaceReadyGate>
      </div>
    </div>
  )
}
