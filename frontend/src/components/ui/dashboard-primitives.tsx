"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

// ─── Skeleton ────────────────────────────────────────────────────────────────
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-white/5", className)}
      {...props}
    />
  )
}

// ─── SkeletonCard ─────────────────────────────────────────────────────────────
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("premium-card p-5 space-y-3", className)}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  )
}

// ─── SkeletonChart ────────────────────────────────────────────────────────────
export function SkeletonChart({ className }: { className?: string }) {
  return (
    <div className={cn("premium-card p-5 space-y-4", className)}>
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-[280px] w-full" />
    </div>
  )
}

// ─── ErrorState ───────────────────────────────────────────────────────────────
export function ErrorState({
  message = "Failed to load data",
  onRetry,
  className,
}: {
  message?: string
  onRetry?: () => void
  className?: string
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-red-500/30 bg-red-500/10 p-6 flex flex-col items-center gap-3 text-center",
        className
      )}
    >
      <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-sm text-red-300">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 text-xs font-medium text-red-400 hover:text-red-300 underline underline-offset-2 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}

// ─── EmptyState ───────────────────────────────────────────────────────────────
export function EmptyState({
  title = "No data",
  description = "Nothing to show yet.",
  icon,
  className,
}: {
  title?: string
  description?: string
  icon?: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/5 bg-white/[0.02] p-10 flex flex-col items-center gap-3 text-center",
        className
      )}
    >
      {icon ? (
        <div className="text-[var(--color-text-muted)]">{icon}</div>
      ) : (
        <svg className="h-10 w-10 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 7h18M3 12h18M3 17h18" />
        </svg>
      )}
      <p className="font-medium text-[var(--color-text-secondary)]">{title}</p>
      <p className="text-sm text-[var(--color-text-muted)]">{description}</p>
    </div>
  )
}

// ─── PageHeader ───────────────────────────────────────────────────────────────
export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children?: React.ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">{title}</h1>
        {subtitle && (
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{subtitle}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
    </div>
  )
}

// ─── SectionCard ──────────────────────────────────────────────────────────────
export function SectionCard({
  title,
  subtitle,
  children,
  className,
  headerAction,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
}) {
  return (
    <div className={cn("premium-card p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-[var(--color-text-primary)]">{title}</h3>
          {subtitle && <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{subtitle}</p>}
        </div>
        {headerAction}
      </div>
      {children}
    </div>
  )
}

// ─── Badge ─────────────────────────────────────────────────────────────────────
const badgeVariants: Record<string, string> = {
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
  error: "bg-red-500/15 text-red-400 border-red-500/25",
  warning: "bg-amber-500/15 text-amber-400 border-amber-500/25",
  info: "bg-sky-500/15 text-sky-400 border-sky-500/25",
  neutral: "bg-white/5 text-[var(--color-text-secondary)] border-white/10",
  purple: "bg-violet-500/15 text-violet-400 border-violet-500/25",
}

export function Badge({
  variant = "neutral",
  children,
  className,
}: {
  variant?: keyof typeof badgeVariants
  children: React.ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        badgeVariants[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

// ─── StatusDot ────────────────────────────────────────────────────────────────
const dotColors: Record<string, string> = {
  active: "bg-emerald-400",
  completed: "bg-sky-400",
  failed: "bg-red-400",
  pending: "bg-amber-400",
  processing: "bg-violet-400",
}

export function StatusDot({ status }: { status: string }) {
  const color = dotColors[status.toLowerCase()] ?? "bg-gray-400"
  return <span className={cn("inline-block h-2 w-2 rounded-full", color)} />
}
