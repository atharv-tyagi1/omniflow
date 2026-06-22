"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function ReportsPage() {
  const isEnabled = hasCapability("businessReports")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Executive Reports</h1>
          <p className="text-[var(--color-text-muted)]">
            Generate and schedule high-level operational reports.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Reports Module Unavailable"
          description="You do not have the required permissions or capabilities enabled for this feature."
          dependency="GET /api/v1/reports"
          status="Missing"
        />
      </div>
    )
  }

  const plannedReports = [
    {
      title: "Agent Performance Summary",
      description: "Weekly digest of CSAT, resolution rates, and conversation volume by agent.",
      frequency: "Weekly",
      status: "Not Implemented (Backend Missing)",
      apiRoute: "GET /api/v1/reports/agent-performance"
    },
    {
      title: "Knowledge Base Gap Analysis",
      description: "Identifies topics where agents frequently fail to resolve user queries due to missing documentation.",
      frequency: "Monthly",
      status: "Not Implemented (Backend Missing)",
      apiRoute: "GET /api/v1/reports/kb-gaps"
    },
    {
      title: "Customer Sentiment Trends",
      description: "Deep dive into customer sentiment shifts across product lines.",
      frequency: "Quarterly",
      status: "Not Implemented (Backend Missing)",
      apiRoute: "GET /api/v1/reports/sentiment"
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Executive Reports</h1>
        <p className="text-[var(--color-text-muted)]">
          Generate and schedule high-level operational reports.
        </p>
      </div>
      
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/10 mb-8">
        <h3 className="text-sm font-medium text-red-800 dark:text-red-400 mb-1 flex items-center">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          Implementation Gap
        </h3>
        <p className="text-sm text-red-700 dark:text-red-300">
          The reporting engine backend is not yet implemented. The reports listed below are planned but currently unavailable.
        </p>
      </div>

      <div className="grid gap-4">
        {plannedReports.map((report, idx) => (
          <div key={idx} className="border border-[var(--color-border-strong)] rounded-xl p-5 bg-[var(--color-surface)] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-lg">{report.title}</h3>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">{report.description}</p>
              <div className="flex items-center gap-4 mt-3">
                <span className="text-xs px-2 py-1 bg-[var(--color-surface-hover)] rounded text-[var(--color-text-secondary)] font-medium">
                  {report.frequency}
                </span>
                <code className="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-hover)] px-2 py-1 rounded">
                  {report.apiRoute}
                </code>
              </div>
            </div>
            <div className="flex-shrink-0">
              <span className="inline-flex items-center px-2.5 py-1.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
                {report.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
