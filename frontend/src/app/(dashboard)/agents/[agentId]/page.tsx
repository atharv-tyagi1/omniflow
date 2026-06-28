"use client"

import * as React from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useAgent } from "@/services/agents/queries"
import { useUpdateAgentVersion } from "@/services/agents/mutations"
import { useAuth } from "@/context/AuthContext"
import { ArrowLeft, Save, Bot, Code, Settings } from "lucide-react"

export default function AgentBuilderPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.agentId as string
  const { workspace } = useAuth()
  
  const { data: agent, isLoading } = useAgent(workspace?.id, agentId)
  const updateVersion = useUpdateAgentVersion()

  const [systemPrompt, setSystemPrompt] = React.useState("")
  const [welcomePrompt, setWelcomePrompt] = React.useState("")
  const [provider, setProvider] = React.useState("gemini")
  const [modelName, setModelName] = React.useState("gemini-2.0-flash")
  const [temperature, setTemperature] = React.useState("0.7")
  
  // Populate form when agent loads
  React.useEffect(() => {
    if (agent && agent.versions && agent.versions.length > 0) {
      // Find published version, or fallback to latest
      const activeVersion = agent.versions.find(v => v.is_published) || agent.versions[0]
      if (activeVersion.prompt) {
        setSystemPrompt(activeVersion.prompt.system_prompt || "")
        setWelcomePrompt(activeVersion.prompt.welcome_prompt || "")
      }
      if (activeVersion.model) {
        setProvider(activeVersion.model.provider || "gemini")
        setModelName(activeVersion.model.model_name || "gemini-2.0-flash")
        setTemperature(activeVersion.model.config?.temperature?.toString() || "0.7")
      }
    }
  }, [agent])

  const handleSave = async () => {
    if (!workspace) return
    
    try {
      await updateVersion.mutateAsync({
        workspaceId: workspace.id,
        agentId,
        data: {
          prompt: {
            system_prompt: systemPrompt,
            welcome_prompt: welcomePrompt,
            fallback_prompt: "I'm sorry, I cannot process this request right now."
          },
          model: {
            provider,
            model_name: modelName,
            config: {
              temperature: parseFloat(temperature),
              max_tokens: 1024
            }
          },
          publish: true
        }
      })
      alert("Agent configuration saved and published successfully!")
    } catch (err: any) {
      alert("Failed to save: " + err.message)
    }
  }

  if (isLoading) {
    return <div className="p-8 animate-pulse text-[var(--color-text-muted)]">Loading Agent Builder...</div>
  }

  if (!agent) {
    return <div className="p-8">Agent not found</div>
  }

  return (
    <div className="max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-6">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/agents')}
            className="p-2 hover:bg-[var(--color-surface-hover)] rounded-full text-[var(--color-text-muted)] transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] flex items-center gap-2">
              <Bot className="h-6 w-6 text-[var(--color-primary-start)]" />
              {agent.name}
            </h1>
            <p className="text-[var(--color-text-muted)] text-sm mt-1">
              Category ID: <code className="bg-[var(--color-surface-hover)] px-1 py-0.5 rounded text-xs">{agent.category}</code>
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={() => router.push('/agents')}>Cancel</Button>
          <Button onClick={handleSave} disabled={updateVersion.isPending}>
            <Save className="h-4 w-4 mr-2" />
            {updateVersion.isPending ? "Saving..." : "Save & Publish"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Prompts */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden shadow-sm">
            <div className="bg-[var(--color-surface-elevated)] px-4 py-3 border-b border-[var(--color-border-subtle)] flex items-center gap-2 font-medium">
              <Code className="h-4 w-4 text-[var(--color-text-muted)]" />
              Agent Prompts
            </div>
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold flex justify-between">
                  System Prompt
                  <span className="text-[var(--color-text-muted)] font-normal text-xs">Required</span>
                </label>
                <p className="text-xs text-[var(--color-text-muted)] mb-2">
                  Defines the persona, constraints, and behavior of the agent. This is passed as a system message to the LLM.
                </p>
                <textarea
                  className="w-full h-48 p-3 bg-[var(--color-surface-hover)] border border-[var(--color-border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-start)] font-mono text-sm resize-y"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="e.g. You are a helpful billing assistant. Only answer questions related to invoices and pricing..."
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold flex justify-between">
                  Welcome Message
                  <span className="text-[var(--color-text-muted)] font-normal text-xs">Optional</span>
                </label>
                <p className="text-xs text-[var(--color-text-muted)] mb-2">
                  The initial greeting the agent sends when a user starts a conversation.
                </p>
                <input
                  type="text"
                  className="w-full p-2 bg-[var(--color-surface-hover)] border border-[var(--color-border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-start)] text-sm"
                  value={welcomePrompt}
                  onChange={(e) => setWelcomePrompt(e.target.value)}
                  placeholder="e.g. Hi there! How can I help you with your billing today?"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Model Settings */}
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden shadow-sm">
            <div className="bg-[var(--color-surface-elevated)] px-4 py-3 border-b border-[var(--color-border-subtle)] flex items-center gap-2 font-medium">
              <Settings className="h-4 w-4 text-[var(--color-text-muted)]" />
              Model Configuration
            </div>
            <div className="p-6 space-y-6">
              
              <div className="space-y-2">
                <label className="text-sm font-semibold">AI Provider</label>
                <select 
                  className="w-full p-2 bg-[var(--color-surface-hover)] border border-[var(--color-border-subtle)] rounded-lg text-sm"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold">Model Name</label>
                <select 
                  className="w-full p-2 bg-[var(--color-surface-hover)] border border-[var(--color-border-subtle)] rounded-lg text-sm"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                >
                  {provider === 'gemini' && (
                    <>
                      <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                      <option value="gemini-2.0-pro-exp-02-05">Gemini 2.0 Pro</option>
                    </>
                  )}
                  {provider === 'openai' && (
                    <>
                      <option value="gpt-4o">GPT-4o</option>
                      <option value="gpt-4o-mini">GPT-4o Mini</option>
                    </>
                  )}
                  {provider === 'anthropic' && (
                    <>
                      <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                    </>
                  )}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold flex justify-between">
                  Temperature
                  <span className="text-xs text-[var(--color-text-muted)]">{temperature}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full accent-[var(--color-primary-start)]"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                />
                <div className="flex justify-between text-xs text-[var(--color-text-muted)]">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
