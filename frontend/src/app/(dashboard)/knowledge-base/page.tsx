"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/services/knowledge/queries"

export default function KnowledgeBasePage() {
  const isEnabled = hasCapability("knowledgeDocuments")
  const { data: documents, isLoading, isError } = useDocuments()
  const deleteMutation = useDeleteDocument()
  const uploadMutation = useUploadDocument()
  
  const [isUploading, setIsUploading] = React.useState(false)

  if (!isEnabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Knowledge Base</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your agent knowledge documents and training datasets.
          </p>
        </div>
        <EmptyState 
          variant="coming-soon" 
          title="Knowledge Base Unavailable"
          description="You do not have the required permissions or capabilities enabled for this feature."
          dependency="GET /api/v1/knowledge/documents"
          status="Missing"
        />
      </div>
    )
  }

  const handleSimulateUpload = () => {
    setIsUploading(true)
    uploadMutation.mutate({
      name: `Document ${new Date().toISOString()}`,
      file_type: "text/plain",
      file_url: "s3://mock-bucket/mock-doc.txt"
    }, {
      onSettled: () => setIsUploading(false)
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Knowledge Base</h1>
          <p className="text-[var(--color-text-muted)]">
            Manage your agent knowledge documents and training datasets.
          </p>
        </div>
        <button 
          onClick={handleSimulateUpload}
          disabled={isUploading}
          className="px-4 py-2 bg-[var(--color-primary-start)] text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
        >
          {isUploading ? "Uploading..." : "Upload Document"}
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12 text-[var(--color-text-muted)]">Loading knowledge documents...</div>
      )}

      {isError && (
        <div className="flex justify-center py-12 text-red-500">Failed to load knowledge documents.</div>
      )}

      {!isLoading && !isError && (!documents || documents.length === 0) && (
        <EmptyState 
          title="No Documents Found"
          description="Upload your first document to start training your agents with custom knowledge."
          dependency="GET /api/v1/knowledge/documents"
          status="Empty"
        />
      )}

      {!isLoading && !isError && documents && documents.length > 0 && (
        <div className="border border-[var(--color-border-subtle)] rounded-xl overflow-hidden bg-[var(--color-surface)]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--color-surface-elevated)] border-b border-[var(--color-border-subtle)]">
                <th className="p-4 font-medium text-sm text-[var(--color-text-muted)]">Document Name</th>
                <th className="p-4 font-medium text-sm text-[var(--color-text-muted)]">Type</th>
                <th className="p-4 font-medium text-sm text-[var(--color-text-muted)]">Status</th>
                <th className="p-4 font-medium text-sm text-[var(--color-text-muted)] text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-[var(--color-border-subtle)] last:border-0 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <td className="p-4 text-sm font-medium">{doc.name}</td>
                  <td className="p-4 text-sm text-[var(--color-text-muted)] uppercase">{doc.file_type.split("/").pop() || doc.file_type}</td>
                  <td className="p-4 text-sm">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      {doc.status}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-right">
                    <button 
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      className="text-red-500 hover:text-red-600 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
