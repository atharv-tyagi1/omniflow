"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"
import { ApiKeysTable } from "@/components/api-management/ApiKeysTable"
import { 
  CreateApiKeyModal, 
  RotateApiKeyModal, 
  RevokeApiKeyModal 
} from "@/components/api-management/ApiKeyModals"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function ApiManagementPage() {
  const isEnabled = hasCapability("apiKeys")
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false)
  const [rotateKeyId, setRotateKeyId] = React.useState<string | null>(null)
  const [revokeKeyId, setRevokeKeyId] = React.useState<string | null>(null)

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">API Management</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your API keys and webhook integrations.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="API Management Portal Coming Soon"
          description="We are currently building the API Key generation and rotation service. This will be available in a future phase."
          dependency="GET /api/public/v1/apikeys"
          status="Missing"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">API Management</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your API keys and webhook integrations.
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create API Key
        </Button>
      </div>
      
      <ApiKeysTable 
        onRotate={(id) => setRotateKeyId(id)}
        onRevoke={(id) => setRevokeKeyId(id)}
      />

      <CreateApiKeyModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
      />
      
      <RotateApiKeyModal 
        keyId={rotateKeyId} 
        onClose={() => setRotateKeyId(null)} 
      />
      
      <RevokeApiKeyModal 
        keyId={revokeKeyId} 
        onClose={() => setRevokeKeyId(null)} 
      />
    </div>
  )
}

