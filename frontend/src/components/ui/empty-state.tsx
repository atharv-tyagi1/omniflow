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
}

export function EmptyState({ variant = "generic", title, description, action, className }: EmptyStateProps) {
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
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  )
}
