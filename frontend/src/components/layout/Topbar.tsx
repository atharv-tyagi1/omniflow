'use client'

import * as React from 'react'
import { Search, Bell, Menu, Plus } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/lib/utils'
import Link from 'next/link'

interface TopbarProps {
  onMenuClick?: () => void
  className?: string
}

export function Topbar({ onMenuClick, className }: TopbarProps) {
  const { user, workspace, logout } = useAuth()
  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() || 'U'

  return (
    <header
      className={cn(
        'sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-[var(--color-border-strong)] bg-[var(--color-surface)]/80 px-4 backdrop-blur-md',
        className
      )}
      role="banner"
    >
      {/* Mobile menu */}
      <button
        onClick={onMenuClick}
        className="ap-focus md:hidden h-8 w-8 flex items-center justify-center rounded text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
        aria-label="Toggle navigation menu"
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>

      {/* Workspace selector */}
      <div className="hidden md:flex items-center gap-2 min-w-0">
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-semibold leading-none truncate text-[var(--color-text-primary)]">
            {workspace?.name || 'Select Workspace'}
          </span>
          <span className="text-xs text-[var(--color-text-muted)] leading-none mt-0.5">Enterprise</span>
        </div>
      </div>

      {/* Search */}
      <form
        className="ml-auto hidden md:flex relative w-full max-w-sm items-center"
        role="search"
        aria-label="Search OmniFlow"
        onSubmit={(e) => e.preventDefault()}
      >
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-[var(--color-text-muted)]" aria-hidden="true" />
        <input
          type="search"
          placeholder="Search resources, agents…"
          aria-label="Search"
          className="ap-focus h-9 w-full rounded-md border border-[var(--color-border-strong)] bg-[var(--color-background)] pl-9 pr-4 text-sm outline-none placeholder:text-[var(--color-text-muted)] text-[var(--color-text-primary)]"
        />
        <div className="absolute right-2.5 top-1.5 flex items-center gap-0.5 pointer-events-none">
          <span className="text-[10px] text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] border border-[var(--color-border-subtle)] rounded px-1 py-0.5 font-mono">⌘K</span>
        </div>
      </form>

      {/* Actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Notification bell */}
        <button
          className="ap-focus relative h-8 w-8 flex items-center justify-center rounded-md text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          <span
            className="absolute right-1.5 top-1.5 flex h-1.5 w-1.5 rounded-full bg-[var(--color-error)]"
            aria-hidden="true"
          />
        </button>

        {/* Create Agent CTA */}
        <Link
          href="/agents/list"
          className="ap-focus hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white
            bg-gradient-to-r from-indigo-600 to-violet-600
            shadow-[0_0_12px_rgba(99,102,241,0.25)]
            hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]
            hover:-translate-y-0.5 transition-all duration-200"
          aria-label="Create a new agent"
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          Create Agent
        </Link>

        {/* User avatar */}
        <button
          className="ap-focus h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center border border-indigo-500/30 flex-shrink-0"
          aria-label={`User menu for ${user?.full_name || user?.email || 'User'}`}
          onClick={() => logout()}
          title="Click to log out"
        >
          <span className="text-xs font-semibold text-white leading-none">{initials}</span>
        </button>
      </div>
    </header>
  )
}
