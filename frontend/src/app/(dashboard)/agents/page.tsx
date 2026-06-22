"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"

export default function AgentsPage() {
  const isEnabled = hasCapability("agentMetrics")

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">AI Agents</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your autonomous customer service agents.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Agents Module Unavailable"
          description="You do not have the required permissions or capabilities enabled for this feature."
          dependency="GET /api/v1/agents"
          status="Missing"
        />
      </div>
    )
  }

  const systemAgents = [
    {
      id: "sales-agent",
      name: "Sales Bot",
      description: "Handles pre-sales inquiries, product questions, and lead qualification.",
      status: "Active",
      features: ["Lead Scoring", "Product Recommendations"],
      type: "System"
    },
    {
      id: "support-agent",
      name: "Support Bot",
      description: "Resolves technical issues, troubleshooting, and general inquiries.",
      status: "Active",
      features: ["Knowledge Base RAG", "Ticket Creation"],
      type: "System"
    },
    {
      id: "customer-care-agent",
      name: "Customer Care Bot",
      description: "Manages post-sales support, billing questions, and account management.",
      status: "Active",
      features: ["Sentiment Analysis", "Escalation Routing"],
      type: "System"
    }
  ]

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">AI Agents</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your autonomous customer service agents.
          </p>
        </div>
        <button 
          disabled
          className="px-4 py-2 bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] rounded-lg font-medium cursor-not-allowed opacity-70"
          title="Custom agents coming soon"
        >
          + Create Custom Agent
        </button>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Active System Agents</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {systemAgents.map((agent) => (
            <div key={agent.id} className="border border-[var(--color-border-strong)] rounded-xl p-5 bg-[var(--color-surface)] shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-lg">{agent.name}</h3>
                  <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">{agent.type}</span>
                </div>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                  {agent.status}
                </span>
              </div>
              <p className="text-sm text-[var(--color-text-muted)] mb-6 flex-grow">{agent.description}</p>
              
              <div className="space-y-2 mb-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Key Capabilities</h4>
                <ul className="text-sm space-y-1">
                  {agent.features.map((feature, i) => (
                    <li key={i} className="flex items-center text-[var(--color-text-secondary)]">
                      <span className="mr-2 text-[var(--color-primary-start)]">•</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-4 border-t border-[var(--color-border-subtle)] flex gap-2">
                <button className="flex-1 px-3 py-1.5 bg-[var(--color-surface-elevated)] border border-[var(--color-border-subtle)] rounded text-sm font-medium hover:bg-[var(--color-surface-hover)] transition-colors">
                  Configure (Coming Soon)
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-12 p-6 rounded-xl border border-dashed border-[var(--color-border-strong)] bg-[var(--color-surface-hover)]">
        <h3 className="text-lg font-semibold mb-2 flex items-center">
          <span className="mr-2">🚧</span> Advanced Capabilities (Coming Soon)
        </h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-4">
          The following features require the next version of the AI orchestration engine to be deployed.
        </p>
        <ul className="list-disc list-inside text-sm text-[var(--color-text-secondary)] space-y-2 ml-2">
          <li>Custom Agent Creation via Dashboard</li>
          <li>Agent Persona & Prompt Tuning UI</li>
          <li>Multi-Agent Orchestration Visualizer</li>
          <li>Bring Your Own LLM Model Selection</li>
        </ul>
      </div>
    </div>
  )
}
