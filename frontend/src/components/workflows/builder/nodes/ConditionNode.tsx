import React from "react"
import { Handle, Position, NodeProps } from "@xyflow/react"
import { GitBranch } from "lucide-react"

export function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`w-[240px] rounded-xl border p-3 shadow-sm bg-[var(--color-bg-primary)] ${
        selected ? "border-amber-500 ring-1 ring-amber-500/20" : "border-white/10"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="h-2 w-2 !bg-amber-500"
      />
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
          <GitBranch className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Condition
          </h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            {data.config?.condition_type || "If / Else"}
          </p>
        </div>
      </div>
      
      {/* True Handle */}
      <div className="relative mt-2">
        <p className="text-[10px] text-emerald-400 text-center absolute -bottom-6 left-1/4">True</p>
        <Handle
          type="source"
          id="true"
          position={Position.Bottom}
          style={{ left: "25%" }}
          className="h-2 w-2 !bg-emerald-500"
        />
      </div>

      {/* False Handle */}
      <div className="relative">
        <p className="text-[10px] text-red-400 text-center absolute -bottom-4 right-1/4">False</p>
        <Handle
          type="source"
          id="false"
          position={Position.Bottom}
          style={{ left: "75%" }}
          className="h-2 w-2 !bg-red-500"
        />
      </div>
    </div>
  )
}
