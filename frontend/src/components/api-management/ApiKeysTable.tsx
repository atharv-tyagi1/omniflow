"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useApiKeys } from "@/services/api-keys/queries"
import { format } from "date-fns"
import { MoreHorizontal, Key, RefreshCw, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiKey } from "@/services/api-keys/schemas"

interface ApiKeysTableProps {
  onRotate: (keyId: string) => void
  onRevoke: (keyId: string) => void
}

export function ApiKeysTable({ onRotate, onRevoke }: ApiKeysTableProps) {
  const { workspace } = useAuth()
  const { data, isLoading, error } = useApiKeys(workspace?.id || "")

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 border border-red-500/20 bg-red-500/10 text-red-500 rounded-lg">
        Error loading API keys.
      </div>
    )
  }

  const keys = data?.items || []

  if (keys.length === 0) {
    return (
      <div className="p-12 text-center border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)]">
        <Key className="mx-auto h-12 w-12 text-[var(--color-text-muted)] mb-4" />
        <h3 className="text-lg font-medium text-[var(--color-text-primary)]">No API Keys</h3>
        <p className="text-[var(--color-text-muted)] mt-1">
          Create an API key to start integrating with OmniFlow.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <table className="w-full text-sm text-left">
        <thead className="bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] text-xs uppercase">
          <tr>
            <th className="px-6 py-4 font-medium">Name</th>
            <th className="px-6 py-4 font-medium">Prefix</th>
            <th className="px-6 py-4 font-medium">Status</th>
            <th className="px-6 py-4 font-medium">Created</th>
            <th className="px-6 py-4 font-medium">Last Used</th>
            <th className="px-6 py-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-border)]">
          {keys.map((apiKey: ApiKey) => (
            <tr key={apiKey.id} className="hover:bg-[var(--color-surface-hover)] transition-colors">
              <td className="px-6 py-4 font-medium text-[var(--color-text-primary)]">
                {apiKey.name}
              </td>
              <td className="px-6 py-4 text-[var(--color-text-muted)] font-mono">
                {apiKey.prefix}••••••••
              </td>
              <td className="px-6 py-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  apiKey.status === 'active' 
                    ? 'bg-green-500/10 text-green-500' 
                    : 'bg-red-500/10 text-red-500'
                }`}>
                  {apiKey.status}
                </span>
              </td>
              <td className="px-6 py-4 text-[var(--color-text-muted)]">
                {format(new Date(apiKey.created_at), 'MMM d, yyyy')}
              </td>
              <td className="px-6 py-4 text-[var(--color-text-muted)]">
                {apiKey.last_used_at ? format(new Date(apiKey.last_used_at), 'MMM d, yyyy HH:mm') : 'Never'}
              </td>
              <td className="px-6 py-4 text-right">
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={apiKey.status === 'revoked'}
                    onClick={() => onRotate(apiKey.id)}
                    title="Rotate Key"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-500 hover:text-red-600 hover:bg-red-50"
                    disabled={apiKey.status === 'revoked'}
                    onClick={() => onRevoke(apiKey.id)}
                    title="Revoke Key"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
