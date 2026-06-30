"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Shield, LayoutDashboard, Bell, CreditCard, Puzzle } from "lucide-react"
import { PageShell, PageHeader } from "@/components/ui/dashboard-primitives"

const settingsNav = [
  { title: "General", href: "/settings", icon: LayoutDashboard },
  { title: "Workspace", href: "/settings/workspace", icon: LayoutDashboard },
  { title: "Security", href: "/settings/security", icon: Shield },
  { title: "Integrations", href: "/settings/integrations", icon: Puzzle },
  { title: "Notifications", href: "/settings/notifications", icon: Bell },
]

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <PageShell variant="standard">
      <div className="flex flex-col h-full w-full">
        <PageHeader 
          title="Settings"
          subtitle="Manage your account and workspace preferences."
        />

      <div className="flex flex-col md:flex-row gap-8">
        <aside className="w-full md:w-64 shrink-0">
          <nav className="flex flex-col space-y-1">
            {settingsNav.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-indigo-500/10 text-indigo-400"
                      : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)]"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.title}
                </Link>
              )
            })}
          </nav>
        </aside>
        
        <main className="flex-1 max-w-4xl">
          {children}
        </main>
      </div>
      </div>
    </PageShell>
  )
}
