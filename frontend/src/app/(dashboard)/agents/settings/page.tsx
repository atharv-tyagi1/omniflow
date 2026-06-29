'use client'

import * as React from 'react'
import { useTheme } from 'next-themes'
import { useAuth } from '@/context/AuthContext'
import { GlassCard } from '@/components/agents/glass/GlassCard'
import { Monitor, Moon, Sun, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

type ThemeOption = { value: string; label: string; icon: React.ReactNode; desc: string }

const THEME_OPTIONS: ThemeOption[] = [
  {
    value: 'dark',
    label: 'Dark',
    icon: <Moon className="h-4 w-4" aria-hidden="true" />,
    desc: 'Liquid crystal glassmorphism — matches the reference design.',
  },
  {
    value: 'light',
    label: 'Light (White)',
    icon: <Sun className="h-4 w-4" aria-hidden="true" />,
    desc: 'Clean white glass layout with the same structure and spacing.',
  },
  {
    value: 'system',
    label: 'System',
    icon: <Monitor className="h-4 w-4" aria-hidden="true" />,
    desc: 'Follow your operating system preference.',
  },
]

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { user, workspace } = useAuth()
  const [mounted, setMounted] = React.useState(false)

  // Avoid hydration mismatch — only render theme state after mount
  React.useEffect(() => setMounted(true), [])

  const handleThemeChange = (value: string) => {
    setTheme(value)
    // Optional backend sync — fire-and-forget, never blocks UI
    // fetch('/api/v1/auth/me', { method: 'PATCH', body: JSON.stringify({ theme_preference: value }) })
    //   .catch(() => {}) // silently ignored
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Settings</h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Workspace and appearance configuration</p>
      </div>

      {/* Workspace Info */}
      <section aria-labelledby="workspace-section">
        <h3 id="workspace-section" className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">
          Workspace
        </h3>
        <GlassCard className="p-5 space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-[var(--color-border-subtle)]">
            <span className="text-sm text-[var(--color-text-muted)]">Workspace Name</span>
            <span className="text-sm font-medium text-[var(--color-text-primary)]">{workspace?.name || '—'}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-[var(--color-border-subtle)]">
            <span className="text-sm text-[var(--color-text-muted)]">Workspace ID</span>
            <code className="text-xs font-mono text-[var(--color-text-secondary)]">{workspace?.id || '—'}</code>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-[var(--color-text-muted)]">Account</span>
            <span className="text-sm font-medium text-[var(--color-text-primary)]">{user?.email || '—'}</span>
          </div>
        </GlassCard>
      </section>

      {/* Theme */}
      <section aria-labelledby="theme-section">
        <h3 id="theme-section" className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
          Appearance
        </h3>
        <p className="text-xs text-[var(--color-text-muted)] mb-3">Theme preference is saved in this browser.</p>

        <div
          className="grid grid-cols-3 gap-3"
          role="radiogroup"
          aria-label="Select color theme"
        >
          {THEME_OPTIONS.map((opt) => {
            const isActive = mounted && theme === opt.value
            return (
              <button
                key={opt.value}
                role="radio"
                aria-checked={isActive}
                onClick={() => handleThemeChange(opt.value)}
                className={cn(
                  'ap-focus relative rounded-xl border p-4 text-left transition-all',
                  isActive
                    ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_12px_rgba(99,102,241,0.2)]'
                    : 'border-[var(--color-border-subtle)] hover:border-[var(--color-border-strong)] bg-[var(--color-surface)]'
                )}
              >
                {isActive && (
                  <span className="absolute top-2 right-2">
                    <Check className="h-3.5 w-3.5 text-indigo-400" aria-hidden="true" />
                  </span>
                )}
                <div className={cn('mb-2', isActive ? 'text-indigo-400' : 'text-[var(--color-text-muted)]')}>
                  {opt.icon}
                </div>
                <p className={cn('text-sm font-semibold', isActive ? 'text-indigo-300' : 'text-[var(--color-text-primary)]')}>
                  {opt.label}
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-1 leading-relaxed">{opt.desc}</p>
              </button>
            )
          })}
        </div>

        {/* Browser-scoped notice — explicit, not implying cross-device */}
        <div
          className="mt-3 flex items-start gap-2 text-xs text-[var(--color-text-muted)]"
          role="note"
          aria-label="Theme persistence scope"
        >
          <span className="mt-0.5 opacity-60">ⓘ</span>
          <span>
            Theme preference is saved in this browser.{' '}
            Sign in on another device to set your preference there.
          </span>
        </div>
      </section>

      {/* Danger Zone placeholder */}
      <section aria-labelledby="danger-section">
        <h3 id="danger-section" className="text-sm font-semibold text-red-400 mb-3">Danger Zone</h3>
        <GlassCard className="p-5 border-red-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">Reset Workspace</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                Permanently delete all agents, runs, and knowledge data.
              </p>
            </div>
            <button
              disabled
              aria-disabled="true"
              className="ap-focus px-3 py-1.5 rounded-lg text-xs font-medium border border-red-500/30 text-red-400 opacity-50 cursor-not-allowed"
            >
              Contact Support
            </button>
          </div>
        </GlassCard>
      </section>
    </div>
  )
}
