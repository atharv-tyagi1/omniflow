"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useCustomers } from "@/services/customers/queries"
import { PageHeader, SkeletonCard, ErrorState, EmptyState, Badge, PageShell, GLASS_CARD_CLASSES } from "@/components/ui/dashboard-primitives"
import { cn } from "@/lib/utils"
import { Search, Users, Mail, Phone, Calendar } from "lucide-react"

function CustomerCard({ customer }: { customer: any }) {
  return (
    <div className={cn(GLASS_CARD_CLASSES, "p-5 hover:border-[var(--color-border-strong)] cursor-pointer group")}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/30 flex items-center justify-center shrink-0 text-sm font-semibold text-indigo-300">
          {(customer.name || customer.email || "?").charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-[var(--color-text-primary)] truncate">
            {customer.name || "Unknown"}
          </p>
          {customer.email && (
            <div className="flex items-center gap-1 mt-0.5 text-xs text-[var(--color-text-muted)]">
              <Mail className="h-3 w-3 shrink-0" />
              <span className="truncate">{customer.email}</span>
            </div>
          )}
          {customer.phone && (
            <div className="flex items-center gap-1 mt-0.5 text-xs text-[var(--color-text-muted)]">
              <Phone className="h-3 w-3 shrink-0" />
              <span>{customer.phone}</span>
            </div>
          )}
        </div>
      </div>
      {customer.external_id && (
        <div className="mt-3 pt-3 border-t border-[var(--color-border-subtle)]">
          <span className="text-xs text-[var(--color-text-muted)]">ID: {customer.external_id}</span>
        </div>
      )}
      {customer.created_at && (
        <div className="flex items-center gap-1 mt-2 text-xs text-[var(--color-text-muted)]">
          <Calendar className="h-3 w-3" />
          <span>Customer since {new Date(customer.created_at).toLocaleDateString()}</span>
        </div>
      )}
    </div>
  )
}

export default function CustomersPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  const [search, setSearch] = React.useState("")
  const [debouncedSearch, setDebouncedSearch] = React.useState("")

  React.useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search), 350)
    return () => clearTimeout(id)
  }, [search])

  const params = React.useMemo(() => ({
    ...(debouncedSearch && { search: debouncedSearch }),
    limit: "24",
  }), [debouncedSearch])

  const { data: customers, isLoading, error, refetch } = useCustomers(workspaceId, params)
  const list: any[] = Array.isArray(customers) ? customers : []

  return (
    <PageShell variant="wide">
      <PageHeader title="Customer Insights" subtitle="Browse and explore customer profiles">
        <Badge variant="neutral">{list.length} loaded</Badge>
      </PageHeader>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search customers…"
          className="ap-focus w-full pl-9 pr-3 py-2 rounded-xl bg-[var(--color-background)] border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-500/50 transition-colors"
        />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array(8).fill(0).map((_, i) => <SkeletonCard key={i} className="h-36" />)}
        </div>
      ) : error ? (
        <ErrorState message="Failed to load customers." onRetry={refetch} />
      ) : list.length === 0 ? (
        <EmptyState
          title="No customers found"
          description="Customers appear here as they interact via any channel."
          icon={<Users className="h-10 w-10" />}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {list.map((c: any) => <CustomerCard key={c.id} customer={c} />)}
        </div>
      )}
    </PageShell>
  )
}
