'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { navigationConfig } from '@/config/navigation'
import { hasCapability, CapabilityKeys } from '@/lib/api-capabilities/registry'
import { useAuth } from '@/context/AuthContext'
import { ChevronLeft, ChevronRight, Zap } from 'lucide-react'

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname()
  const { workspace } = useAuth()
  const [collapsed, setCollapsed] = React.useState(false)

  return (
    <aside
      className={cn(
        'flex flex-col bg-[rgba(2,6,23,0.85)] backdrop-blur-[40px] saturate-[1.2] border-r border-[var(--color-border-subtle)] transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div className="flex h-14 items-center border-b border-[var(--color-border-strong)] px-4 justify-between">
        {!collapsed && (
          <Link
            href="/agents"
            className="ap-focus flex items-center space-x-2 font-bold text-lg tracking-tight primary-gradient-text"
          >
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.4)] flex-shrink-0">
              <span className="text-white text-xs leading-none font-bold">O</span>
            </div>
            <span>OmniFlow</span>
          </Link>
        )}
        {collapsed && (
          <div className="h-6 w-6 rounded-md bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center mx-auto">
            <span className="text-white text-xs font-bold">O</span>
          </div>
        )}

        <button
          onClick={() => setCollapsed((c) => !c)}
          className={cn(
            'ap-focus h-6 w-6 rounded flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors flex-shrink-0',
            collapsed && 'mx-auto mt-2'
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
        >
          {collapsed
            ? <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
            : <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />}
        </button>
      </div>

      {/* Nav */}
      <div className="flex-1 overflow-y-auto py-4 canvas-scroll">
        <nav className={cn('grid gap-4', collapsed ? 'px-2' : 'px-2')}>
          {navigationConfig.map((group, index) => {
            const visibleItems = group.items.filter((item) =>
              !item.capability || hasCapability(item.capability as CapabilityKeys)
            )
            if (visibleItems.length === 0) return null

            return (
              <div key={index} className="space-y-1 px-2">
                {!collapsed && (
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                    {group.title}
                  </h4>
                )}
                <div className="grid gap-1">
                  {visibleItems.map((item, itemIndex) => {
                    const isActive = pathname?.startsWith(item.href) || false
                    return (
                      <Link
                        key={itemIndex}
                        href={item.href}
                        className={cn(
                          'ap-focus flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors outline-none',
                          collapsed && 'justify-center px-0',
                          isActive
                            ? 'ap-sidebar-active text-[var(--color-primary-start)]'
                            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)]/50 hover:text-[var(--color-text-primary)]'
                        )}
                        aria-current={isActive ? 'page' : undefined}
                        title={collapsed ? item.title : undefined}
                      >
                        <item.icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                        {!collapsed && item.title}
                      </Link>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </nav>
      </div>

      {/* Plan/Usage Card */}
      {!collapsed && (
        <div className="p-3 border-t border-[var(--color-border-strong)]">
          <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-3.5 w-3.5 text-indigo-400" aria-hidden="true" />
              <span className="text-xs font-semibold text-indigo-300">Enterprise</span>
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-[var(--color-text-muted)]">Runs this month</span>
                <span className="text-[var(--color-text-secondary)] font-medium">6,804</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-indigo-500/10 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500" style={{ width: '68%' }} aria-label="Usage: 68%" />
              </div>
              <p className="text-[10px] text-[var(--color-text-muted)]">68% of 10,000 runs</p>
            </div>
          </div>
        </div>
      )}
      {collapsed && (
        <div className="p-3 border-t border-[var(--color-border-strong)] flex justify-center">
          <Zap className="h-4 w-4 text-indigo-400" aria-label="Enterprise plan" />
        </div>
      )}
    </aside>
  )
}
