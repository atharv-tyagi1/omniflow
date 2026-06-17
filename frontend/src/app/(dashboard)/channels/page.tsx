"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { fetchApi } from "@/lib/api-client"
import { useQuery } from "@tanstack/react-query"
import { PageHeader, SectionCard, Badge, ErrorState, SkeletonCard, PageShell } from "@/components/ui/dashboard-primitives"
import { Send, PhoneCall, RefreshCw, CheckCircle, Clock, AlertTriangle, Mic, Volume2, Activity } from "lucide-react"

function useTelegramHealth(workspaceId: string) {
  return useQuery({
    queryKey: ["telegram", "health", workspaceId],
    queryFn: async () => fetchApi<any>(`/api/v1/telegram/health`).catch(() => null),
    enabled: !!workspaceId,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  })
}

function StatRow({ label, value, icon }: { label: string; value: any; icon: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <div className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
        <span className="text-[var(--color-text-muted)]">{icon}</span>
        {label}
      </div>
      <span className="text-sm font-semibold text-[var(--color-text-primary)]">{value ?? "—"}</span>
    </div>
  )
}

export default function ChannelsPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""

  const { data: telegramHealth, isLoading: tgLoading, error: tgError, refetch } = useTelegramHealth(workspaceId)

  const tgStatus = telegramHealth?.webhook_configured ? "configured" : telegramHealth ? "not configured" : "unknown"

  return (
    <PageShell variant="wide">
      <PageHeader title="Channel Observability" subtitle="Telegram & Voice channel health and traffic">
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Telegram */}
        <SectionCard
          title="Telegram"
          subtitle="Webhook status & message traffic"
          headerAction={
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  tgStatus === "configured" ? "bg-emerald-400 animate-pulse" : "bg-red-400"
                }`}
              />
              <Badge variant={tgStatus === "configured" ? "success" : "error"}>
                {tgStatus}
              </Badge>
            </div>
          }
        >
          {tgLoading ? (
            <div className="space-y-2">
              {Array(4).fill(0).map((_, i) => <SkeletonCard key={i} className="h-10" />)}
            </div>
          ) : (
            <div>
              <StatRow label="Webhook Status" value={tgStatus} icon={<Send className="h-3.5 w-3.5" />} />
              <StatRow label="Bot Name" value={telegramHealth?.bot_username ?? "—"} icon={<CheckCircle className="h-3.5 w-3.5" />} />
              <StatRow label="Webhook URL" value={telegramHealth?.webhook_url ? "Set" : "Not set"} icon={<Activity className="h-3.5 w-3.5" />} />
              <StatRow label="Last Checked" value={new Date().toLocaleTimeString()} icon={<Clock className="h-3.5 w-3.5" />} />
            </div>
          )}
          {tgError && <ErrorState message="Failed to fetch Telegram health." className="mt-3" />}
        </SectionCard>

        {/* Voice */}
        <SectionCard
          title="Voice"
          subtitle="Voice request lifecycle & artifact tracking"
          headerAction={
            <Badge variant="neutral">
              Public API
            </Badge>
          }
        >
          <div>
            <StatRow
              label="Voice Requests"
              value="Tracked via VoiceInteraction"
              icon={<PhoneCall className="h-3.5 w-3.5" />}
            />
            <StatRow
              label="Transcription"
              value="Gemini Flash"
              icon={<Mic className="h-3.5 w-3.5" />}
            />
            <StatRow
              label="TTS Engine"
              value="gTTS"
              icon={<Volume2 className="h-3.5 w-3.5" />}
            />
            <StatRow
              label="Artifact Lifecycle"
              value="30-day retention"
              icon={<Clock className="h-3.5 w-3.5" />}
            />
            <StatRow
              label="Idempotency"
              value="Enabled"
              icon={<CheckCircle className="h-3.5 w-3.5" />}
            />
            <StatRow
              label="Async Processing"
              value="PublicAsyncJob queue"
              icon={<Activity className="h-3.5 w-3.5" />}
            />
          </div>
          <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex gap-2 text-xs text-amber-300">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
            <span>Voice analytics dashboard will aggregate from VoiceInteraction table once data accumulates.</span>
          </div>
        </SectionCard>
      </div>
    </PageShell>
  )
}
