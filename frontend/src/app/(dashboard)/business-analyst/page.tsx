"use client"

import * as React from "react"
import { useAnalystQuery, useAnalystLimits } from "@/services/analyst/queries"
import { PageHeader, ErrorState, SectionCard, PageShell } from "@/components/ui/dashboard-primitives"
import { hasCapability } from "@/lib/api-capabilities/registry"
import { Send, Bot, User, AlertCircle, Loader2, Sparkles } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  error?: boolean
  timestamp: Date
}

const SUGGESTED_QUESTIONS = [
  "Why did sentiment drop last week?",
  "What are the top customer complaints?",
  "Which products generate most support volume?",
  "Which customers appear at risk of churning?",
  "What is the average resolution time trend?",
]

export default function BusinessAnalystPage() {
  const isEnabled = hasCapability("businessQuestions")
  const [messages, setMessages] = React.useState<Message[]>([])
  const [input, setInput] = React.useState("")
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const inputRef = React.useRef<HTMLTextAreaElement>(null)

  const { mutate: ask, isPending } = useAnalystQuery()
  const { data: limits } = useAnalystLimits()

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const sendMessage = (text: string) => {
    if (!text.trim() || isPending) return
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text.trim(), timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setInput("")

    ask(text.trim(), {
      onSuccess: (data) => {
        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.error ? `Error: ${data.error}` : data.response || "No response returned.",
          error: !!data.error,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMsg])
      },
      onError: (err: any) => {
        const errMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Request failed: ${err.message}`,
          error: true,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errMsg])
      },
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  if (!isEnabled) {
    return (
      <PageShell variant="standard">
        <PageHeader title="AI Business Analyst" subtitle="Natural language business intelligence" />
        <div className="premium-card p-10 flex flex-col items-center gap-4 text-center">
          <Sparkles className="h-10 w-10 text-violet-400" />
          <p className="font-semibold text-[var(--color-text-secondary)]">Business Analyst Disabled</p>
          <p className="text-sm text-[var(--color-text-muted)] max-w-md">
            The businessQuestions capability is currently disabled in the capability registry.
          </p>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell variant="full-height">
      <PageHeader title="AI Business Analyst" subtitle="Ask questions about your business data in natural language">
        {limits && (
          <span className="text-xs text-[var(--color-text-muted)]">
            {limits.remaining?.requests_remaining ?? "—"} queries remaining
          </span>
        )}
      </PageHeader>

      <div className="flex-1 flex flex-col gap-4 min-h-0">
        {/* Chat Area */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto space-y-4 canvas-scroll pr-1"
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-6 text-center py-12">
              <div className="p-4 rounded-2xl bg-violet-500/10 border border-violet-500/20">
                <Sparkles className="h-8 w-8 text-violet-400" />
              </div>
              <div>
                <p className="font-semibold text-[var(--color-text-primary)] mb-1">Ask your data anything</p>
                <p className="text-sm text-[var(--color-text-muted)]">Try one of these questions to get started:</p>
              </div>
              <div className="grid gap-2 w-full max-w-xl">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="text-left px-4 py-3 rounded-xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20 text-sm text-[var(--color-text-secondary)] transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === "assistant"
                      ? "bg-violet-500/20 text-violet-400"
                      : "bg-indigo-500/20 text-indigo-400"
                  }`}
                >
                  {msg.role === "assistant" ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                </div>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-indigo-500/20 text-[var(--color-text-primary)] rounded-tr-sm"
                      : msg.error
                      ? "bg-red-500/10 border border-red-500/20 text-red-300 rounded-tl-sm"
                      : "bg-white/[0.04] border border-white/8 text-[var(--color-text-secondary)] rounded-tl-sm"
                  }`}
                >
                  {msg.error && <AlertCircle className="inline h-3.5 w-3.5 mr-1 mb-0.5 text-red-400" />}
                  <span className="whitespace-pre-wrap">{msg.content}</span>
                  <div className="text-[10px] text-[var(--color-text-muted)] mt-1.5 text-right">
                    {msg.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          {isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="bg-white/[0.04] border border-white/8 rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-[var(--color-text-muted)]" />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="liquid-glass rounded-2xl p-3 flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your business data… (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] resize-none focus:outline-none leading-relaxed"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isPending}
            className="p-2 rounded-xl bg-indigo-500/80 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-white shrink-0"
          >
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </PageShell>
  )
}
