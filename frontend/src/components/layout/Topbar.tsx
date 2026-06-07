"use client"

import * as React from "react"
import { Search, Bell, Menu } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface TopbarProps {
  onMenuClick?: () => void
  className?: string
}

export function Topbar({ onMenuClick, className }: TopbarProps) {
  const { user, workspace } = useAuth()

  return (
    <header className={cn("sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-[var(--color-border-strong)] bg-[var(--color-surface)]/80 px-4 backdrop-blur-md", className)}>
      <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuClick} aria-label="Toggle Menu">
        <Menu className="h-5 w-5" />
      </Button>
      
      <div className="flex flex-1 items-center gap-4">
        <div className="hidden md:flex flex-col">
          <span className="text-sm font-semibold leading-none">{workspace?.name || "Select Workspace"}</span>
          <span className="text-xs text-[var(--color-text-muted)] leading-none mt-1">Free Tier</span>
        </div>

        <form className="ml-auto hidden md:flex relative w-full max-w-sm items-center">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-[var(--color-text-muted)]" />
          <input
            type="search"
            placeholder="Search resources, topics..."
            className="h-9 w-full rounded-md border border-[var(--color-border-strong)] bg-[var(--color-background)] pl-9 pr-4 text-sm outline-none placeholder:text-[var(--color-text-muted)] focus:ring-2 focus:ring-[var(--color-primary-start)]"
          />
        </form>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 flex h-2 w-2 rounded-full bg-[var(--color-error)]"></span>
        </Button>
        <div className="h-8 w-8 rounded-full bg-[var(--color-surface-elevated)] flex items-center justify-center border border-[var(--color-border-strong)] cursor-pointer">
          <span className="text-xs font-semibold">{user?.name?.charAt(0) || "U"}</span>
        </div>
      </div>
    </header>
  )
}
