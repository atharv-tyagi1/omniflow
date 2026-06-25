import React from "react"
import { Handle, Position, NodeProps } from "@xyflow/react"
import { Play } from "lucide-react"

export function TriggerNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`w-[240px] rounded-xl border p-3 shadow-sm bg-[var(--color-bg-primary)] ${
        selected ? "border-violet-500 ring-1 ring-violet-500/20" : "border-white/10"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400">
          <Play className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Trigger
          </h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            {data.config?.trigger_type || "Event"}
          </p>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-2 w-2 !bg-violet-500"
      />
    </div>
  )
}
