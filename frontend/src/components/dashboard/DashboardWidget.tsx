import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface DashboardWidgetProps {
  title: string
  description?: string
  loading?: boolean
  error?: Error | null
  onRetry?: () => void
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
}

export function DashboardWidget({
  title,
  description,
  loading = false,
  error = null,
  onRetry,
  children,
  className,
  headerAction
}: DashboardWidgetProps) {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {headerAction && <div>{headerAction}</div>}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3 mt-4">
            <Skeleton className="h-[125px] w-full rounded-xl" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-4">
            <div className="rounded-full bg-[var(--color-error)]/10 p-3">
              <AlertCircle className="h-6 w-6 text-[var(--color-error)]" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-[var(--color-text-primary)]">Widget failed to load</p>
              <p className="text-xs text-[var(--color-text-muted)] max-w-xs">{error.message || "An unexpected error occurred."}</p>
            </div>
            {onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
                <RefreshCw className="mr-2 h-3 w-3" />
                Retry
              </Button>
            )}
          </div>
        ) : (
          <div className="mt-4">{children}</div>
        )}
      </CardContent>
    </Card>
  )
}
