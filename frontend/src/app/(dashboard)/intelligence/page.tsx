"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { DashboardWidget } from "@/components/dashboard/DashboardWidget"
import { Badge } from "@/components/ui/badge"
import { PermissionGuard } from "@/components/layout/PermissionGuard"
import { canViewIntel } from "@/lib/permissions"

export default function IntelligencePage() {
  const { workspace } = useAuth()
  
  const mockTopics = [
    { name: "Pricing Inquiry", volume: 1450, trend: "+12%" },
    { name: "Account Access", volume: 840, trend: "-5%" },
    { name: "Feature Request: Export", volume: 620, trend: "+45%" },
    { name: "Billing Dispute", volume: 310, trend: "+2%" },
    { name: "API Rate Limits", volume: 180, trend: "+110%" },
  ]

  return (
    <PermissionGuard checkPermission={canViewIntel} featureName="Conversation Intelligence">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Conversation Intel</h1>
          <p className="text-[var(--color-text-muted)]">
            Semantic topic extraction, sentiment analysis, and anomaly detection.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <DashboardWidget title="Top Emerging Topics" description="By conversation volume over 7 days" className="col-span-2">
            <div className="space-y-4">
              {mockTopics.map((topic, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-elevated)]">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-primary-start)]/10 text-[var(--color-primary-start)] text-xs font-bold">
                      #{i + 1}
                    </div>
                    <span className="font-medium text-sm text-[var(--color-text-primary)]">{topic.name}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm font-semibold">{topic.volume}</span>
                    <Badge variant={topic.trend.startsWith("+") ? (parseInt(topic.trend) > 50 ? "destructive" : "success") : "secondary"}>
                      {topic.trend}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </DashboardWidget>

          <DashboardWidget title="Sentiment Overview" description="Aggregated customer sentiment">
            <div className="flex flex-col items-center justify-center h-[300px] space-y-4">
              <div className="text-5xl font-bold text-[var(--color-success)]">78%</div>
              <p className="text-sm text-[var(--color-text-muted)]">Positive Sentiment</p>
              <div className="w-full max-w-[200px] h-2 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden flex">
                <div className="h-full bg-[var(--color-success)] w-[78%]" />
                <div className="h-full bg-[var(--color-warning)] w-[15%]" />
                <div className="h-full bg-[var(--color-error)] w-[7%]" />
              </div>
              <div className="flex justify-between w-full max-w-[200px] text-xs text-[var(--color-text-muted)] mt-2">
                <span>Pos</span>
                <span>Neu</span>
                <span>Neg</span>
              </div>
            </div>
          </DashboardWidget>
        </div>
      </div>
    </PermissionGuard>
  )
}
