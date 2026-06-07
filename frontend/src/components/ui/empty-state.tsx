import * as React from "react"
import { cn } from "@/lib/utils"
import { Inbox, FileText, AlertCircle, Sparkles, ServerCrash } from "lucide-react"

export type EmptyStateVariant = "no-conversations" | "no-reports" | "no-insights" | "coming-soon" | "error" | "generic"

export interface EmptyStateProps {
  variant?: EmptyStateVariant
  title?: string
  description?: string
  action?: React.ReactNode
  className?: string
  dependency?: string
  status?: string
}

export function EmptyState({ variant = "generic", title, description, action, className, dependency, status }: EmptyStateProps) {
  const defaults = {
    "no-conversations": {
      icon: <Inbox className="h-10 w-10 text-[var(--color-text-muted)]" />,
      title: "No conversations found",
      description: "There are no conversations matching your current filters or date range.",
    },
    "no-reports": {
      icon: <FileText className="h-10 w-10 text-[var(--color-text-muted)]" />,
      title: "No reports generated",
      description: "There are no executive reports available for the selected period.",
    },
    "no-insights": {
      icon: <Sparkles className="h-10 w-10 text-[var(--color-text-muted)]" />,
      title: "No insights available",
      description: "The Business Analyst has not generated any insights for this workspace yet.",
    },
    "coming-soon": {
      icon: <AlertCircle className="h-10 w-10 text-[var(--color-info)]" />,
      title: "Coming Soon",
      description: "This feature is currently under development and will be available in a future update.",
    },
    "error": {
      icon: <ServerCrash className="h-10 w-10 text-[var(--color-error)]" />,
      title: "Something went wrong",
      description: "We encountered an error loading this data. Please try again later.",
    },
    "generic": {
      icon: <Inbox className="h-10 w-10 text-[var(--color-text-muted)]" />,
      title: "No data available",
      description: "There is nothing to display here right now.",
    },
  }

  const current = defaults[variant]

  return (
    <div
      className={cn(
        "flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--color-border-strong)] bg-[var(--color-surface)]/50 p-8 text-center animate-in fade-in-50",
        className
      )}
    >
      <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-surface-elevated)] mb-4">
          {current.icon}
        </div>
        <h3 className="mt-4 text-lg font-semibold text-[var(--color-text-primary)]">
          {title || current.title}
        </h3>
        <p className="mb-4 mt-2 text-sm text-[var(--color-text-muted)]">
          {description || current.description}
        </p>
        
        {dependency && (
          <div className="mt-4 p-4 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border-subtle)] text-left w-full max-w-sm">
            <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Dependency Constraint</div>
            <code className="text-xs bg-black/20 px-2 py-1 rounded text-[var(--color-info)] break-all">{dependency}</code>
            {status && (
              <div className="mt-2 flex items-center space-x-2">
                <div className="h-2 w-2 rounded-full bg-[var(--color-warning)] animate-pulse" />
                <span className="text-xs font-medium text-[var(--color-text-muted)]">Status: {status}</span>
              </div>
            )}
          </div>
        )}

        {action && <div className="mt-6">{action}</div>}
      </div>
    </div>
  )
}
