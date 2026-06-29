'use client'

import * as React from 'react'
import { useAuth } from '@/context/AuthContext'
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '@/services/api-keys/queries'
import { GlassTable } from '@/components/agents/glass/GlassTable'
import { GlassCard } from '@/components/agents/glass/GlassCard'
import { GlassEmptyState } from '@/components/agents/glass/GlassEmptyState'
import { GlassErrorState } from '@/components/agents/glass/GlassErrorState'
import { StatusChip } from '@/components/agents/glass/StatusChip'
import { Key, Plus, Copy, Trash2, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = React.useState(false)
  const copy = () => {
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={copy}
      className="ap-focus p-1 rounded hover:bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
      aria-label={copied ? 'Copied!' : 'Copy key prefix'}
    >
      {copied
        ? <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
        : <Copy className="h-3.5 w-3.5" />}
    </button>
  )
}

function RevokeButton({ keyId, onRevoke }: { keyId: string; onRevoke: () => void }) {
  const [confirming, setConfirming] = React.useState(false)
  const { mutate: revoke, isPending } = useRevokeApiKey(keyId)

  if (confirming) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--color-text-muted)]">Sure?</span>
        <button
          onClick={() => revoke(undefined, { onSuccess: onRevoke })}
          disabled={isPending}
          className="ap-focus text-xs font-medium text-red-400 hover:text-red-300 transition-colors"
          aria-label="Confirm revoke"
        >
          {isPending ? 'Revoking…' : 'Yes, revoke'}
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="ap-focus text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          aria-label="Cancel revoke"
        >
          Cancel
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="ap-focus p-1 rounded hover:bg-red-500/10 text-[var(--color-text-muted)] hover:text-red-400 transition-colors"
      aria-label="Revoke API key"
    >
      <Trash2 className="h-3.5 w-3.5" />
    </button>
  )
}

// Create Modal
function CreateKeyModal({ onClose, onCreated }: { onClose: () => void; onCreated: (raw: string) => void }) {
  const [name, setName] = React.useState('')
  const [scopes, setScopes] = React.useState<string[]>(['agents:read'])
  const { mutate: create, isPending } = useCreateApiKey()

  const SCOPE_OPTIONS = ['agents:read', 'agents:write', 'runs:read', 'knowledge:read', 'webhooks:write']

  const toggleScope = (s: string) =>
    setScopes((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    create({ name, scopes } as any, {
      onSuccess: (data: any) => {
        onCreated(data?.key || data?.data?.key || '***')
        onClose()
      },
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Create API Key"
    >
      <div className="ap-glass-card w-full max-w-md p-6 mx-4">
        <h3 className="text-base font-bold text-[var(--color-text-primary)] mb-4">Create API Key</h3>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[var(--color-text-secondary)] block mb-1.5" htmlFor="key-name">
              Key Name
            </label>
            <input
              id="key-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. Production Integration"
              className="ap-focus w-full rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
            />
          </div>
          <div>
            <p className="text-xs font-medium text-[var(--color-text-secondary)] mb-2">Scopes</p>
            <div className="space-y-2">
              {SCOPE_OPTIONS.map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer text-sm text-[var(--color-text-secondary)]">
                  <input
                    type="checkbox"
                    checked={scopes.includes(s)}
                    onChange={() => toggleScope(s)}
                    className="ap-focus rounded"
                    aria-label={`Scope: ${s}`}
                  />
                  <code className="text-xs font-mono text-[var(--color-primary-start)]">{s}</code>
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="ap-focus flex-1 px-4 py-2 rounded-lg text-sm border border-[var(--color-border-subtle)] text-[var(--color-text-secondary)] hover:border-[var(--color-border-strong)] transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={isPending || !name}
              className="ap-focus flex-1 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 disabled:opacity-50 transition-opacity">
              {isPending ? 'Creating…' : 'Create Key'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function ApiKeysPage() {
  const { workspace } = useAuth()
  const { data, isLoading, error, refetch } = useApiKeys(workspace?.id || '')
  const [isCreateOpen, setIsCreateOpen] = React.useState(false)
  const [newKey, setNewKey] = React.useState<string | null>(null)

  const keys = (data as any)?.data?.items ?? (data as any)?.items ?? []

  const columns = [
    { key: 'name', header: 'Name', render: (r: any) => <span className="font-medium text-[var(--color-text-primary)] text-sm">{r.name}</span> },
    { key: 'prefix', header: 'Key Prefix', render: (r: any) => (
      <div className="flex items-center gap-1">
        <code className="text-xs font-mono text-[var(--color-text-secondary)]">{r.key_prefix || r.prefix || '****'}…</code>
        <CopyButton value={r.key_prefix || r.prefix || ''} />
      </div>
    )},
    { key: 'scopes', header: 'Scopes', render: (r: any) => (
      <div className="flex flex-wrap gap-1">
        {(r.scopes || []).map((s: string) => (
          <code key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">{s}</code>
        ))}
      </div>
    )},
    { key: 'status', header: 'Status', render: (r: any) => <StatusChip status={r.status || 'active'} compact /> },
    { key: 'created_at', header: 'Created', render: (r: any) => <span className="text-xs text-[var(--color-text-muted)]">{r.created_at ? fmtDate(r.created_at) : '—'}</span> },
    { key: 'actions', header: '', render: (r: any) => <RevokeButton keyId={r.id} onRevoke={refetch} /> },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[var(--color-text-primary)]">API Keys</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Manage API keys for workspace integrations</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="ap-focus flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 shadow-[0_0_16px_rgba(99,102,241,0.25)] hover:shadow-[0_0_24px_rgba(99,102,241,0.4)] hover:-translate-y-0.5 transition-all"
          aria-label="Create a new API key"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Create Key
        </button>
      </div>

      {/* New key notice */}
      {newKey && (
        <GlassCard className="p-4 border-emerald-500/30 bg-emerald-500/5">
          <p className="text-sm font-semibold text-emerald-400 mb-1">⚠ Copy your key now — it won't be shown again.</p>
          <div className="flex items-center gap-2">
            <code className="text-xs font-mono text-[var(--color-text-primary)] bg-[var(--color-surface-elevated)] px-2 py-1 rounded flex-1 truncate">{newKey}</code>
            <CopyButton value={newKey} />
            <button onClick={() => setNewKey(null)} className="ap-focus text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">Dismiss</button>
          </div>
        </GlassCard>
      )}

      {error ? (
        <GlassErrorState message={(error as Error).message} onRetry={refetch} />
      ) : (
        <GlassTable
          caption="API keys"
          columns={columns as any}
          data={keys}
          isLoading={isLoading}
          getRowKey={(r: any) => r.id}
          emptyState={
            <GlassEmptyState
              title="No API keys yet"
              description="Create your first API key to integrate with the Agent Platform."
              icon={<Key className="h-10 w-10" />}
              action={
                <button
                  onClick={() => setIsCreateOpen(true)}
                  className="ap-focus flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600"
                >
                  <Plus className="h-4 w-4" /> Create Key
                </button>
              }
            />
          }
        />
      )}

      {isCreateOpen && (
        <CreateKeyModal
          onClose={() => setIsCreateOpen(false)}
          onCreated={(k) => setNewKey(k)}
        />
      )}
    </div>
  )
}
