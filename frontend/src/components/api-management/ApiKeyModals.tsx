import * as React from "react"
import { Modal } from "@/components/ui/modal"
import { Button } from "@/components/ui/button"
import { useCreateApiKey, useRotateApiKey, useRevokeApiKey } from "@/services/api-keys/queries"
import { Check, Copy } from "lucide-react"

interface CreateModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CreateApiKeyModal({ isOpen, onClose }: CreateModalProps) {
  const [name, setName] = React.useState("")
  const [secret, setSecret] = React.useState<string | null>(null)
  const [copied, setCopied] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  
  const createMutation = useCreateApiKey()

  const handleCreate = async () => {
    if (!name.trim()) return
    setError(null)
    try {
      const res = await createMutation.mutateAsync({
        name: name.trim(),
        scopes: ["all"] // In a real app, this would be selectable
      })
      if (res?.key_secret) {
        setSecret(res.key_secret)
      }
    } catch (err: any) {
      setError(err.message || "Failed to create API key")
    }
  }

  const handleCopy = () => {
    if (secret) {
      navigator.clipboard.writeText(secret)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleClose = () => {
    setName("")
    setSecret(null)
    setCopied(false)
    setError(null)
    onClose()
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={secret ? () => {} : handleClose}
      title="Create API Key"
      description={secret ? "Your API Key is ready" : "Create a new API key for integrating with OmniFlow."}
    >
      {secret ? (
        <div className="space-y-4 mt-4">
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-lg text-sm">
            Please copy this key now. For security reasons, you will not be able to see it again.
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 p-2 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-md font-mono text-sm break-all">
              {secret}
            </div>
            <Button variant="outline" size="icon" onClick={handleCopy}>
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="flex justify-end pt-4">
            <Button onClick={handleClose}>Done</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4 mt-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-primary)]">Key Name</label>
            <input 
              type="text" 
              className="w-full p-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Production Backend"
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                if (error) setError(null)
              }}
            />
          </div>
          {error && (
            <div className="text-sm text-red-500 bg-red-500/10 p-2 rounded-md border border-red-500/20">
              {error}
            </div>
          )}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={handleClose} disabled={createMutation.isPending}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreate} 
              disabled={!name.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? "Creating..." : "Create Key"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}

interface RotateModalProps {
  keyId: string | null
  onClose: () => void
}

export function RotateApiKeyModal({ keyId, onClose }: RotateModalProps) {
  const [secret, setSecret] = React.useState<string | null>(null)
  const [copied, setCopied] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  
  // We cannot call useRotateApiKey conditionally, so we pass a dummy ID if null. 
  // It won't be executed unless keyId is valid anyway.
  const rotateMutation = useRotateApiKey(keyId || "")

  const handleRotate = async () => {
    if (!keyId) return
    setError(null)
    try {
      const res = await rotateMutation.mutateAsync({ reason: "Manual rotation" })
      if (res?.new_key_secret) {
        setSecret(res.new_key_secret)
      }
    } catch (err: any) {
      setError(err.message || "Failed to rotate API key")
    }
  }

  const handleCopy = () => {
    if (secret) {
      navigator.clipboard.writeText(secret)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleClose = () => {
    setSecret(null)
    setCopied(false)
    setError(null)
    onClose()
  }

  return (
    <Modal 
      isOpen={!!keyId} 
      onClose={secret ? () => {} : handleClose}
      title="Rotate API Key"
    >
      {secret ? (
        <div className="space-y-4 mt-4">
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-lg text-sm">
            Your new API Key. The old key is now permanently revoked.
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 p-2 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-md font-mono text-sm break-all">
              {secret}
            </div>
            <Button variant="outline" size="icon" onClick={handleCopy}>
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="flex justify-end pt-4">
            <Button onClick={handleClose}>Done</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4 mt-4">
          <p className="text-[var(--color-text-muted)] text-sm">
            Are you sure you want to rotate this key? The current key will immediately stop working. 
            Any applications using the current key will need to be updated with the new one.
          </p>
          {error && (
            <div className="text-sm text-red-500 bg-red-500/10 p-2 rounded-md border border-red-500/20">
              {error}
            </div>
          )}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={handleClose} disabled={rotateMutation.isPending}>
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={handleRotate} 
              disabled={rotateMutation.isPending}
            >
              {rotateMutation.isPending ? "Rotating..." : "Rotate Key"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}

interface RevokeModalProps {
  keyId: string | null
  onClose: () => void
}

export function RevokeApiKeyModal({ keyId, onClose }: RevokeModalProps) {
  const [error, setError] = React.useState<string | null>(null)
  const revokeMutation = useRevokeApiKey(keyId || "")

  const handleRevoke = async () => {
    if (!keyId) return
    setError(null)
    try {
      await revokeMutation.mutateAsync()
      onClose()
    } catch (err: any) {
      setError(err.message || "Failed to revoke API key")
    }
  }

  return (
    <Modal 
      isOpen={!!keyId} 
      onClose={onClose}
      title="Revoke API Key"
    >
      <div className="space-y-4 mt-4">
        <p className="text-[var(--color-text-muted)] text-sm">
          Are you sure you want to revoke this API key? This action cannot be undone. 
          Any integrations using this key will immediately stop working.
        </p>
        {error && (
          <div className="text-sm text-red-500 bg-red-500/10 p-2 rounded-md border border-red-500/20">
            {error}
          </div>
        )}
        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={onClose} disabled={revokeMutation.isPending}>
            Cancel
          </Button>
          <Button 
            variant="destructive"
            onClick={handleRevoke} 
            disabled={revokeMutation.isPending}
          >
            {revokeMutation.isPending ? "Revoking..." : "Revoke Key"}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
