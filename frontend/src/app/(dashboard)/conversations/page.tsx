"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useConversations } from "@/services/conversations/queries"
import { PageHeader, SkeletonCard, ErrorState, EmptyState, Badge, StatusDot, PageShell, GLASS_CARD_CLASSES } from "@/components/ui/dashboard-primitives"
import { cn } from "@/lib/utils"
import { Search, Filter, MessageSquare, Clock, ChevronRight } from "lucide-react"

const CHANNEL_OPTIONS = ["all", "web", "telegram", "voice", "api"]
const STATUS_OPTIONS = ["all", "active", "resolved", "pending", "escalated"]

function ConversationRow({ conv }: { conv: any }) {
  const statusColor: Record<string, any> = {
    active: "success",
    resolved: "info",
    pending: "warning",
    escalated: "error",
  }
  return (
    <div className={cn(GLASS_CARD_CLASSES, "flex items-center gap-4 p-4 hover:bg-[var(--color-surface-hover)] cursor-pointer group")}>
      <div className="w-9 h-9 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0">
        <MessageSquare className="h-4 w-4 text-indigo-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-[var(--color-text-primary)] truncate">
            {conv.title || conv.id?.slice(0, 16) + "…"}
          </span>
          <Badge variant={statusColor[conv.status] ?? "neutral"} className="shrink-0">
            {conv.status}
          </Badge>
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          {conv.channel && (
            <span className="text-xs text-[var(--color-text-muted)]">{conv.channel}</span>
          )}
          <span className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
            <Clock className="h-3 w-3" />
            {new Date(conv.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)] transition-colors" />
    </div>
  )
}

export default function ConversationsPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""

  const [search, setSearch] = React.useState("")
  const [status, setStatus] = React.useState("all")
  const [channel, setChannel] = React.useState("all")
  const [debouncedSearch, setDebouncedSearch] = React.useState("")

  React.useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search), 350)
    return () => clearTimeout(id)
  }, [search])

  const filters = React.useMemo(() => ({
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(status !== "all" && { status }),
    ...(channel !== "all" && { channel }),
    limit: 25,
  }), [debouncedSearch, status, channel])

  const { data, isLoading, error, refetch } = useConversations(workspaceId, filters)
  const conversations = data?.data ?? []

  return (
    <PageShell variant="wide">
      <PageHeader title="Conversation Explorer" subtitle="Search and filter all workspace conversations" />

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
            className="ap-focus w-full pl-9 pr-3 py-2 rounded-xl bg-[var(--color-background)] border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-500/50 transition-colors"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="ap-focus px-3 py-2 rounded-xl bg-[var(--color-background)] border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-secondary)] focus:outline-none focus:border-indigo-500/50"
        >
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s === "all" ? "All Statuses" : s}</option>)}
        </select>
        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          className="ap-focus px-3 py-2 rounded-xl bg-[var(--color-background)] border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-secondary)] focus:outline-none focus:border-indigo-500/50"
        >
          {CHANNEL_OPTIONS.map((c) => <option key={c} value={c}>{c === "all" ? "All Channels" : c}</option>)}
        </select>
      </div>

      {/* Results */}
      <div className="space-y-2">
        {isLoading ? (
          Array(6).fill(0).map((_, i) => <SkeletonCard key={i} className="h-16" />)
        ) : error ? (
          <ErrorState message="Failed to load conversations." onRetry={refetch} />
        ) : conversations.length === 0 ? (
          <EmptyState
            title="No conversations found"
            description={debouncedSearch ? "Try adjusting your search or filters." : "Conversations will appear here as they occur."}
            icon={<MessageSquare className="h-10 w-10" />}
          />
        ) : (
          <>
            <p className="text-xs text-[var(--color-text-muted)] mb-3">
              Showing {conversations.length} of {data?.total ?? conversations.length} conversations
            </p>
            {conversations.map((conv: any) => <ConversationRow key={conv.id} conv={conv} />)}
          </>
        )}
      </div>
    </PageShell>
  )
}
