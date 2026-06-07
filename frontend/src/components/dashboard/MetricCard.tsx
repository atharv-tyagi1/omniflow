import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { ArrowDownIcon, ArrowUpIcon, MinusIcon } from "lucide-react"

export interface MetricCardProps {
  title: string
  value: string | number
  trend?: number
  trendLabel?: string
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({
  title,
  value,
  trend,
  trendLabel,
  icon,
  className,
}: MetricCardProps) {
  const isPositive = trend && trend > 0
  const isNegative = trend && trend < 0
  const isNeutral = trend === 0 || trend === undefined

  return (
    <Card className={cn("premium-card overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-sm font-medium text-[var(--color-text-muted)]">
          {title}
        </CardTitle>
        {icon && <div className="text-[var(--color-text-muted)]">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">
          {value}
        </div>
        {(trend !== undefined || trendLabel) && (
          <div className="mt-1 flex items-center text-xs">
            {isPositive && <ArrowUpIcon className="mr-1 h-3 w-3 text-[var(--color-success)]" />}
            {isNegative && <ArrowDownIcon className="mr-1 h-3 w-3 text-[var(--color-error)]" />}
            {isNeutral && <MinusIcon className="mr-1 h-3 w-3 text-[var(--color-text-muted)]" />}
            
            <span
              className={cn(
                "font-medium",
                isPositive && "text-[var(--color-success)]",
                isNegative && "text-[var(--color-error)]",
                isNeutral && "text-[var(--color-text-muted)]"
              )}
            >
              {trend !== undefined ? `${Math.abs(trend)}%` : null}
            </span>
            <span className="ml-1.5 text-[var(--color-text-muted)]">
              {trendLabel || "from last period"}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
