import * as React from "react"
import { useRouter } from "next/navigation"
import { Modal } from "@/components/ui/modal"
import { Button } from "@/components/ui/button"
import { useCreateAgent } from "@/services/agents/mutations"
import { useAuth } from "@/context/AuthContext"

interface CreateAgentModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CreateAgentModal({ isOpen, onClose }: CreateAgentModalProps) {
  const router = useRouter()
  const { workspace } = useAuth()
  const createAgent = useCreateAgent()
  
  const [name, setName] = React.useState("")
  const [category, setCategory] = React.useState("")
  const [error, setError] = React.useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!workspace) return
    setError("")

    try {
      const newAgent = await createAgent.mutateAsync({
        workspaceId: workspace.id,
        data: {
          name,
          category,
          is_active: true
        }
      })
      
      onClose()
      // Redirect to the agent builder page
      router.push(`/agents/${newAgent.id}`)
    } catch (err: any) {
      setError(err.message || "Failed to create agent")
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Custom Agent"
      description="Define a new AI agent for your workspace. You can configure its prompts and models on the next screen."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 text-sm text-red-500 bg-red-50 dark:bg-red-950/50 rounded-lg">
            {error}
          </div>
        )}
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Agent Name</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-start)]"
            placeholder="e.g. Billing Assistant"
          />
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Category / ID (Unique)</label>
          <input
            type="text"
            required
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full p-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-start)]"
            placeholder="e.g. billing-agent"
          />
          <p className="text-xs text-[var(--color-text-muted)]">
            This ID is used for routing and analytics.
          </p>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={createAgent.isPending}>
            {createAgent.isPending ? "Creating..." : "Create & Configure"}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
