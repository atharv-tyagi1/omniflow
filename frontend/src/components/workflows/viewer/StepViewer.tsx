import React from "react"
import { CheckCircle, XCircle, Clock } from "lucide-react"

interface StepViewerProps {
  step: any
}

export function StepViewer({ step }: StepViewerProps) {
  if (!step) return null

  const isError = step.status === "failed"

  return (
    <div className="flex flex-col h-full bg-[var(--color-bg-secondary)] rounded-xl border border-white/10 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[var(--color-bg-primary)]">
        <div className="flex items-center gap-3">
          {isError ? (
            <XCircle className="h-5 w-5 text-red-500" />
          ) : (
            <CheckCircle className="h-5 w-5 text-emerald-500" />
          )}
          <div>
            <h3 className="font-semibold text-[var(--color-text-primary)]">Node ID: {step.node_id.substring(0, 8)}...</h3>
            <p className="text-xs text-[var(--color-text-muted)]">Status: {step.status}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <Clock className="h-3.5 w-3.5" />
          {new Date(step.started_at).toLocaleTimeString()}
        </div>
      </div>

      {/* Payloads */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* Input */}
        <div>
          <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-blue-500"></div>
            Input Payload
          </h4>
          <div className="bg-[#0D0D12] rounded-lg p-4 overflow-x-auto border border-white/5">
            <pre className="text-xs text-blue-300 font-mono">
              {step.input_payload ? JSON.stringify(step.input_payload, null, 2) : "{}"}
            </pre>
          </div>
        </div>

        {/* Output */}
        <div>
          <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
            Output Payload
          </h4>
          <div className="bg-[#0D0D12] rounded-lg p-4 overflow-x-auto border border-white/5">
            <pre className="text-xs text-emerald-300 font-mono">
              {step.output_payload ? JSON.stringify(step.output_payload, null, 2) : "{}"}
            </pre>
          </div>
        </div>

        {/* Error */}
        {step.error_payload && (
          <div>
            <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-red-500"></div>
              Error Details
            </h4>
            <div className="bg-red-950/20 rounded-lg p-4 overflow-x-auto border border-red-500/20">
              <pre className="text-xs text-red-300 font-mono">
                {JSON.stringify(step.error_payload, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
