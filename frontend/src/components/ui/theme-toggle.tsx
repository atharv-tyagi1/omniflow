"use client"

import * as React from "react"
import { Moon, Sun, Laptop } from "lucide-react"
import { useTheme } from "next-themes"

import { cn } from "@/lib/utils"

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  // Avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className={cn("flex items-center gap-1 bg-[var(--color-surface-elevated)] p-1 rounded-lg border border-[var(--color-border-subtle)]", className)}>
        <div className="w-6 h-6 rounded-md" />
        <div className="w-6 h-6 rounded-md" />
        <div className="w-6 h-6 rounded-md" />
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-1 bg-[var(--color-surface-elevated)] p-1 rounded-lg border border-[var(--color-border-subtle)]", className)}>
      <button
        onClick={() => setTheme("light")}
        className={cn(
          "ap-focus p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors",
          theme === "light" && "bg-white/10 dark:bg-white/10 bg-black/10 text-[var(--color-text-primary)] shadow-sm"
        )}
        title="Light theme"
        aria-label="Switch to light theme"
      >
        <Sun className="h-4 w-4" />
      </button>
      <button
        onClick={() => setTheme("system")}
        className={cn(
          "ap-focus p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors",
          theme === "system" && "bg-white/10 dark:bg-white/10 bg-black/10 text-[var(--color-text-primary)] shadow-sm"
        )}
        title="System theme"
        aria-label="Switch to system theme"
      >
        <Laptop className="h-4 w-4" />
      </button>
      <button
        onClick={() => setTheme("dark")}
        className={cn(
          "ap-focus p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors",
          theme === "dark" && "bg-white/10 dark:bg-white/10 bg-black/10 text-[var(--color-text-primary)] shadow-sm"
        )}
        title="Dark theme"
        aria-label="Switch to dark theme"
      >
        <Moon className="h-4 w-4" />
      </button>
    </div>
  )
}
