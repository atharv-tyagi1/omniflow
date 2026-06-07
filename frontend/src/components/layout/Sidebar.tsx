"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { navigationConfig } from "@/config/navigation"
import { hasCapability, CapabilityKeys } from "@/lib/api-capabilities/registry"

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname()

  return (
    <aside className={cn("flex w-64 flex-col liquid-glass-sidebar border-r border-[var(--color-border-strong)]", className)}>
      <div className="flex h-14 items-center px-4 border-b border-[var(--color-border-strong)]">
        <Link href="/overview" className="flex items-center space-x-2 font-bold text-lg tracking-tight primary-gradient-text">
          <div className="h-6 w-6 rounded-md bg-[var(--color-primary-start)] flex items-center justify-center">
            <span className="text-white text-xs leading-none">O</span>
          </div>
          <span>OmniFlow</span>
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto py-4 canvas-scroll">
        <nav className="grid gap-4 px-2">
          {navigationConfig.map((group, index) => {
            // Filter items by capability early
            const visibleItems = group.items.filter(item => 
              !item.capability || hasCapability(item.capability as CapabilityKeys)
            )

            if (visibleItems.length === 0) return null

            return (
              <div key={index} className="space-y-1 px-2">
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                  {group.title}
                </h4>
                <div className="grid gap-1">
                  {visibleItems.map((item, itemIndex) => {
                    const isActive = pathname?.startsWith(item.href) || false
                    return (
                      <Link
                        key={itemIndex}
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring",
                          isActive
                            ? "bg-[var(--color-surface-elevated)] text-[var(--color-primary-start)]"
                            : "text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)]/50 hover:text-[var(--color-text-primary)]"
                        )}
                        aria-current={isActive ? "page" : undefined}
                      >
                        <item.icon className="h-4 w-4" />
                        {item.title}
                      </Link>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </nav>
      </div>
      <div className="p-4 border-t border-[var(--color-border-strong)] text-xs text-[var(--color-text-muted)]">
        v2.0.0-beta
      </div>
    </aside>
  )
}
