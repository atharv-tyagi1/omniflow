"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useIntelTopics, useIntelIntents, useIntelSentiment } from "@/services/intel/queries"
import { DonutChart, HorizontalBarChart, MultiLineChart } from "@/components/charts/Charts"
import { SkeletonChart, ErrorState, EmptyState, PageHeader, SectionCard } from "@/components/ui/dashboard-primitives"

type RangeDays = 7 | 30 | 90

export default function IntelligencePage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  const [days, setDays] = React.useState<RangeDays>(30)

  const { data: topics, isLoading: topicsLoading, error: topicsError, refetch: refetchTopics } = useIntelTopics(workspaceId, days)
  const { data: intents, isLoading: intentsLoading, error: intentsError, refetch: refetchIntents } = useIntelIntents(workspaceId, days)
  const { data: sentiment, isLoading: sentimentLoading, error: sentimentError } = useIntelSentiment(workspaceId, days)

  // Transform topics for chart
  const topicsChartData = React.useMemo(() => {
    if (!topics) return []
    return topics.map((t: any) => ({ name: t.topic, count: t.count }))
  }, [topics])

  // Transform intents for pie chart
  const intentsChartData = React.useMemo(() => {
    if (!intents) return []
    return intents.map((i: any) => ({ name: i.intent, value: i.count }))
  }, [intents])

  // Transform sentiment trend for multi-line chart
  const sentimentChartData = React.useMemo(() => {
    if (!sentiment) return []
    return Object.entries(sentiment).map(([date, values]: [string, any]) => ({
      date: date.slice(5),
      positive: values.positive ?? 0,
      negative: values.negative ?? 0,
      neutral: values.neutral ?? 0,
    }))
  }, [sentiment])

  const rangeOptions: RangeDays[] = [7, 30, 90]

  return (
    <div className="space-y-6">
      <PageHeader title="Conversation Intelligence" subtitle="Intent, sentiment & topic analysis">
        <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
          {rangeOptions.map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                days === d
                  ? "bg-[var(--color-primary-start)] text-white"
                  : "text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </PageHeader>

      {/* Intent + Topics Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard title="Intent Distribution" subtitle={`Past ${days} days`}>
          {intentsLoading ? (
            <SkeletonChart className="h-[260px]" />
          ) : intentsError ? (
            <ErrorState message="Failed to load intent data." onRetry={refetchIntents} />
          ) : intentsChartData.length > 0 ? (
            <DonutChart data={intentsChartData} nameKey="name" valueKey="value" />
          ) : (
            <EmptyState title="No intent data" description="Intent analysis will appear as conversations are analyzed." />
          )}
        </SectionCard>

        <SectionCard title="Top Topics" subtitle={`Past ${days} days`}>
          {topicsLoading ? (
            <SkeletonChart className="h-[260px]" />
          ) : topicsError ? (
            <ErrorState message="Failed to load topics." onRetry={refetchTopics} />
          ) : topicsChartData.length > 0 ? (
            <HorizontalBarChart data={topicsChartData} nameKey="name" valueKey="count" />
          ) : (
            <EmptyState title="No topic data" description="Topics are detected from conversation content." />
          )}
        </SectionCard>
      </div>

      {/* Sentiment Trend */}
      <SectionCard title="Sentiment Trend" subtitle={`Past ${days} days — positive, negative, neutral`}>
        {sentimentLoading ? (
          <SkeletonChart className="h-[280px]" />
        ) : sentimentError ? (
          <ErrorState message="Failed to load sentiment data." />
        ) : sentimentChartData.length > 0 ? (
          <MultiLineChart
            data={sentimentChartData}
            lines={[
              { key: "positive", label: "Positive", color: "#10b981" },
              { key: "negative", label: "Negative", color: "#ef4444" },
              { key: "neutral", label: "Neutral", color: "#6366f1" },
            ]}
          />
        ) : (
          <EmptyState title="No sentiment data" description="Sentiment trend data accumulates over time." />
        )}
      </SectionCard>
    </div>
  )
}
