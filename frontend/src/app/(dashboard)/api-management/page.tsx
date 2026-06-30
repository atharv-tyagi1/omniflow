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
import { PageShell, PageHeader } from "@/components/ui/dashboard-primitives"

export default function ApiManagementPage() {
  const isEnabled = hasCapability("apiKeys")
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false)
  const [rotateKeyId, setRotateKeyId] = React.useState<string | null>(null)
  const [revokeKeyId, setRevokeKeyId] = React.useState<string | null>(null)

  if (!isEnabled) {
    return (
      <PageShell variant="standard">
        <PageHeader 
          title="API Management"
          subtitle="Manage your API keys and webhook integrations."
        />
        <EmptyState 
          variant="coming-soon" 
          title="API Management Portal Coming Soon"
          description="We are currently building the API Key generation and rotation service. This will be available in a future phase."
          dependency="GET /api/public/v1/apikeys"
          status="Missing"
        />
      </PageShell>
    )
  }

  return (
    <PageShell variant="standard">
      <div className="flex items-center justify-between">
        <PageHeader 
          title="API Management"
          subtitle="Manage your API keys and webhook integrations."
        />
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
    </PageShell>
  )
}

