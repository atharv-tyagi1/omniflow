import * as React from "react"
import { cn } from "@/lib/utils"

export type PageShellVariant = "standard" | "wide" | "full-height"

interface PageShellProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: PageShellVariant
  children: React.ReactNode
}

export function PageShell({ variant = "standard", className, children, ...props }: PageShellProps) {
  if (variant === "full-height") {
    return (
      <div 
        className={cn("flex-1 flex flex-col h-[calc(100vh-3.5rem)] min-w-0 overflow-hidden", className)} 
        data-layout-shell="PageShell"
        data-shell-variant={variant}
        {...props}
      >
        {children}
      </div>
    )
  }

  // standard and wide variants use a scrolling container naturally within the AppShell
  return (
    <div 
      className={cn(
        "mx-auto w-full min-w-0 p-4 md:p-8 space-y-6",
        variant === "standard" ? "max-w-5xl" : "max-w-7xl",
        className
      )}
      data-layout-shell="PageShell"
      data-shell-variant={variant}
      role="main"
      {...props}
    >
      {children}
    </div>
  )
}
