"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { CreditCard, CheckCircle2, AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { ErrorBoundary } from "@/components/ui/error-boundary"
import { SkeletonCard, PageShell } from "@/components/ui/dashboard-primitives"

function BillingPageContent() {
  const { data: limits, isLoading: limitsLoading, isError: limitsError } = useQuery({
    queryKey: ["limits"],
    queryFn: async () => {
      const res: any = await api.get("/api/limits")
      return res.data
    }
  })

  if (limitsLoading) {
    return (
      <div className="space-y-4">
        <SkeletonCard className="h-32" />
        <SkeletonCard className="h-64" />
      </div>
    )
  }

  if (limitsError) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
        <h3 className="text-red-400 font-medium">Failed to load billing limits</h3>
      </div>
    )
  }

  const usagePercent = limits ? Math.round((limits.current_usage / limits.max_limit) * 100) : 0

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Billing & Usage</h2>
          <p className="text-sm text-neutral-400 mt-1">
            Manage your subscription plan and monitor API usage.
          </p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700 text-white" disabled>
          Upgrade Plan (Coming Soon)
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current Plan Card */}
        <div className="col-span-1 md:col-span-1 bg-neutral-900 border border-indigo-500/30 rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4">
            <span className="inline-flex items-center rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-xs font-medium text-indigo-300">
              Active
            </span>
          </div>
          <h3 className="text-lg font-medium text-white flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-indigo-400" />
            {limits?.tier ? limits.tier.charAt(0).toUpperCase() + limits.tier.slice(1) : "Pro"} Plan
          </h3>
          <p className="text-sm text-neutral-400 mt-2">
            You are currently on the {limits?.tier || "pro"} tier.
          </p>
          <div className="mt-6 space-y-2">
            <div className="flex items-center gap-2 text-sm text-neutral-300">
              <CheckCircle2 className="h-4 w-4 text-green-400" />
              <span>Unlimited Teammates</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-neutral-300">
              <CheckCircle2 className="h-4 w-4 text-green-400" />
              <span>{limits?.max_limit.toLocaleString() || 1000} API Requests / mo</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-neutral-300">
              <CheckCircle2 className="h-4 w-4 text-green-400" />
              <span>Priority Support</span>
            </div>
          </div>
        </div>

        {/* Usage Card */}
        <div className="col-span-1 md:col-span-2 bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <h3 className="text-lg font-medium text-white mb-6">Current API Usage</h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-3xl font-bold text-white">
                  {limits?.current_usage.toLocaleString() || 0}
                </div>
                <div className="text-sm text-neutral-400">
                  of {limits?.max_limit.toLocaleString() || 1000} included requests
                </div>
              </div>
              <div className="text-sm font-medium text-indigo-400">
                {usagePercent}% Used
              </div>
            </div>

            <div className="h-3 w-full bg-neutral-800 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all ${usagePercent > 90 ? 'bg-red-500' : 'bg-indigo-500'}`}
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
            
            {usagePercent > 90 && (
              <div className="flex items-start gap-2 text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                <AlertCircle className="h-5 w-5 shrink-0" />
                <p>You are approaching your API limit. Please upgrade your plan to avoid service interruption.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BillingPage() {
  return (
    <PageShell variant="standard">
      <ErrorBoundary>
        <BillingPageContent />
      </ErrorBoundary>
    </PageShell>
  )
}
