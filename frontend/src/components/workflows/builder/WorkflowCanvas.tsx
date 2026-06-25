import React, { useCallback, useState } from "react"
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"

import { TriggerNode } from "./nodes/TriggerNode"
import { ActionNode } from "./nodes/ActionNode"
import { ConditionNode } from "./nodes/ConditionNode"
import { ConfigPanel } from "./ConfigPanel"
import { useSaveDraft } from "@/services/workflows/builder"

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  condition: ConditionNode,
}

interface WorkflowCanvasProps {
  workspaceId: string
  workflowId: string
  initialNodes: Node[]
  initialEdges: Edge[]
}

export function WorkflowCanvas({ workspaceId, workflowId, initialNodes, initialEdges }: WorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  
  const saveDraftMutation = useSaveDraft(workspaceId, workflowId)

  // Auto-save debounced
  React.useEffect(() => {
    const timer = setTimeout(() => {
      saveDraftMutation.mutate({ nodes, edges })
    }, 1000)
    return () => clearTimeout(timer)
  }, [nodes, edges])

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id)
  }

  const handleUpdateNodeConfig = (id: string, data: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return { ...node, data }
        }
        return node
      })
    )
  }

  const addNode = (type: string) => {
    const newNode: Node = {
      id: crypto.randomUUID(),
      type,
      position: { x: 250, y: 250 },
      data: { config: {} },
    }
    setNodes((nds) => nds.concat(newNode))
  }

  return (
    <div className="w-full h-full relative bg-[var(--color-bg-secondary)] overflow-hidden">
      {/* Top Bar / Toolbar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-[var(--color-bg-primary)] border border-white/10 rounded-full px-4 py-2 flex gap-4 shadow-lg">
        <button onClick={() => addNode('trigger')} className="text-sm text-violet-400 hover:text-violet-300 font-medium">
          + Trigger
        </button>
        <button onClick={() => addNode('condition')} className="text-sm text-amber-400 hover:text-amber-300 font-medium">
          + Condition
        </button>
        <button onClick={() => addNode('action')} className="text-sm text-emerald-400 hover:text-emerald-300 font-medium">
          + Action
        </button>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={() => setSelectedNodeId(null)}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls className="!bg-[var(--color-bg-primary)] !border-white/10 !fill-[var(--color-text-primary)]" />
        <MiniMap 
          className="!bg-[var(--color-bg-primary)] !border-white/10" 
          maskColor="rgba(0,0,0,0.5)"
          nodeColor="rgba(139, 92, 246, 0.5)"
        />
        <Background gap={12} size={1} />
      </ReactFlow>

      {selectedNodeId && (
        <ConfigPanel 
          selectedNode={nodes.find(n => n.id === selectedNodeId)} 
          onClose={() => setSelectedNodeId(null)} 
          onUpdate={handleUpdateNodeConfig} 
        />
      )}
    </div>
  )
}
