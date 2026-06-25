import React from "react"
import { X, Save } from "lucide-react"

interface ConfigPanelProps {
  selectedNode: any
  onClose: () => void
  onUpdate: (id: string, data: any) => void
}

export function ConfigPanel({ selectedNode, onClose, onUpdate }: ConfigPanelProps) {
  const [config, setConfig] = React.useState<any>(selectedNode?.data?.config || {})

  React.useEffect(() => {
    setConfig(selectedNode?.data?.config || {})
  }, [selectedNode])

  if (!selectedNode) return null

  const handleSave = () => {
    onUpdate(selectedNode.id, {
      ...selectedNode.data,
      config,
    })
  }

  const renderFields = () => {
    switch (selectedNode.type) {
      case "trigger":
        return (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[var(--color-text-muted)] block mb-1">Trigger Type</label>
              <select 
                className="w-full bg-white/5 border border-white/10 rounded-md p-2 text-sm text-[var(--color-text-primary)] outline-none"
                value={config.trigger_type || "webhook"}
                onChange={e => setConfig({...config, trigger_type: e.target.value})}
              >
                <option value="webhook">Webhook</option>
                <option value="schedule">Schedule</option>
                <option value="event">Internal Event</option>
              </select>
            </div>
            {config.trigger_type === "webhook" && (
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-1">Webhook Secret</label>
                <input 
                  type="text"
                  className="w-full bg-white/5 border border-white/10 rounded-md p-2 text-sm text-[var(--color-text-primary)] outline-none"
                  value={config.secret || ""}
                  onChange={e => setConfig({...config, secret: e.target.value})}
                  placeholder="Leave blank for unauthenticated"
                />
              </div>
            )}
          </div>
        )
      case "action":
        return (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[var(--color-text-muted)] block mb-1">Action Type</label>
              <select 
                className="w-full bg-white/5 border border-white/10 rounded-md p-2 text-sm text-[var(--color-text-primary)] outline-none"
                value={config.action_type || "webhook"}
                onChange={e => setConfig({...config, action_type: e.target.value})}
              >
                <option value="webhook">Outbound Webhook</option>
                <option value="add_tag">Add Tag</option>
                <option value="send_email">Send Email</option>
              </select>
            </div>
            {config.action_type === "webhook" && (
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-1">URL</label>
                <input 
                  type="text"
                  className="w-full bg-white/5 border border-white/10 rounded-md p-2 text-sm text-[var(--color-text-primary)] outline-none"
                  value={config.url || ""}
                  onChange={e => setConfig({...config, url: e.target.value})}
                  placeholder="https://..."
                />
              </div>
            )}
          </div>
        )
      case "condition":
        return (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[var(--color-text-muted)] block mb-1">Condition Logic</label>
              <textarea 
                className="w-full bg-white/5 border border-white/10 rounded-md p-2 text-sm text-[var(--color-text-primary)] outline-none min-h-[100px]"
                value={config.expression || ""}
                onChange={e => setConfig({...config, expression: e.target.value})}
                placeholder="payload.amount > 100"
              />
            </div>
          </div>
        )
      default:
        return <p className="text-sm text-[var(--color-text-muted)]">No configuration available for this node.</p>
    }
  }

  return (
    <div className="w-[320px] bg-[var(--color-bg-primary)] border-l border-white/10 flex flex-col h-full absolute right-0 top-0 shadow-2xl">
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h2 className="font-semibold text-sm text-[var(--color-text-primary)]">
          Configure {selectedNode.type.charAt(0).toUpperCase() + selectedNode.type.slice(1)}
        </h2>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-md">
          <X className="h-4 w-4 text-[var(--color-text-muted)]" />
        </button>
      </div>

      <div className="p-4 flex-1 overflow-y-auto">
        {renderFields()}
      </div>

      <div className="p-4 border-t border-white/10">
        <button 
          onClick={handleSave}
          className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Save className="h-4 w-4" />
          Apply Configuration
        </button>
      </div>
    </div>
  )
}
