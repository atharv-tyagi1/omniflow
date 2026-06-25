import React from "react"
import { Handle, Position, NodeProps } from "@xyflow/react"
import { Zap } from "lucide-react"

export function ActionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`w-[240px] rounded-xl border p-3 shadow-sm bg-[var(--color-bg-primary)] ${
        selected ? "border-emerald-500 ring-1 ring-emerald-500/20" : "border-white/10"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="h-2 w-2 !bg-emerald-500"
      />
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
          <Zap className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Action
          </h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            {data.config?.action_type || "Execute"}
          </p>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-2 w-2 !bg-emerald-500"
      />
    </div>
  )
}
