"use client"

import * as React from "react"
import { EmptyState } from "@/components/ui/empty-state"
import { hasCapability } from "@/lib/api-capabilities/registry"
import { useDocuments, useDeleteDocument, knowledgeKeys } from "@/services/knowledge/queries"
import { useQueryClient } from "@tanstack/react-query"

export default function KnowledgeBasePage() {
  const isEnabled = hasCapability("knowledgeDocuments")
  const { data: documents, isLoading, isError } = useDocuments()
  const deleteMutation = useDeleteDocument()
  const queryClient = useQueryClient()

  const [isUploading, setIsUploading] = React.useState(false)
  const [uploadError, setUploadError] = React.useState<string | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

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

  const handleUploadClick = () => {
    setUploadError(null)
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("name", file.name)

      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null
      const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") : null

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/knowledge/upload`,
        {
          method: "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(workspaceId ? { "x-workspace-id": workspaceId } : {}),
          },
          body: formData,
        }
      )

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || "Upload failed")
      }

      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents() })
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
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
        <div className="flex flex-col items-end gap-1">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.pdf,.md,.csv,.json,.docx"
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            onClick={handleUploadClick}
            disabled={isUploading}
            className="px-4 py-2 bg-[var(--color-primary-start)] text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
          >
            {isUploading ? "Uploading..." : "Upload Document"}
          </button>
          {uploadError && (
            <p className="text-xs text-red-500 max-w-xs text-right">{uploadError}</p>
          )}
        </div>
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
                <tr
                  key={doc.id}
                  className="border-b border-[var(--color-border-subtle)] last:border-0 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <td className="p-4 text-sm font-medium">{doc.name}</td>
                  <td className="p-4 text-sm text-[var(--color-text-muted)] uppercase">
                    {doc.file_type.split("/").pop() || doc.file_type}
                  </td>
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
