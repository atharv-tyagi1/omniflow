'use client'

import * as React from 'react'
import { GlassCard } from '@/components/agents/glass/GlassCard'
import { GlassEmptyState } from '@/components/agents/glass/GlassEmptyState'
import { BookOpen, FolderOpen } from 'lucide-react'

const MOCK_COLLECTIONS = [
  { id: '1', name: 'Product Documentation', docCount: 124, status: 'indexed' },
  { id: '2', name: 'Support FAQs', docCount: 48, status: 'indexed' },
  { id: '3', name: 'Policy Handbook', docCount: 12, status: 'indexed' },
]

export default function KnowledgePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Knowledge Base</h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
          Document collections available for agent RAG retrieval
        </p>
      </div>

      {/* Upload area — disabled placeholder */}
      <GlassCard className="p-8 flex flex-col items-center justify-center text-center gap-3 opacity-60 select-none">
        <div
          className="h-12 w-12 rounded-xl bg-[var(--color-surface-elevated)] flex items-center justify-center"
          aria-hidden="true"
        >
          <FolderOpen className="h-6 w-6 text-[var(--color-text-muted)]" />
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--color-text-primary)]">Document Upload</p>
          <p className="text-xs text-[var(--color-text-muted)] mt-1 max-w-xs">
            Drag &amp; drop or browse to upload documents.
          </p>
        </div>
        <div
          className="flex items-center gap-2 text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-lg px-3 py-2"
          role="note"
          aria-label="Document upload unavailable"
        >
          <span>⚠</span>
          <span>Upload is not available in this workspace tier. Contact your administrator.</span>
        </div>
        <button
          disabled
          aria-disabled="true"
          aria-label="Document upload unavailable"
          className="mt-1 px-4 py-2 rounded-lg text-xs font-medium border border-[var(--color-border-subtle)] text-[var(--color-text-muted)] cursor-not-allowed opacity-50"
        >
          Upgrade Plan
        </button>
      </GlassCard>

      {/* Collections */}
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">Collections</h3>
        {MOCK_COLLECTIONS.length === 0 ? (
          <GlassCard className="p-0">
            <GlassEmptyState
              title="No collections yet"
              description="Upload documents to create a knowledge collection."
              icon={<BookOpen className="h-10 w-10" />}
            />
          </GlassCard>
        ) : (
          <div className="space-y-3">
            {MOCK_COLLECTIONS.map((col) => (
              <GlassCard key={col.id} className="p-4 flex items-center gap-4">
                <div className="h-9 w-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="h-4 w-4 text-indigo-400" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[var(--color-text-primary)]">{col.name}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">{col.docCount} documents &bull; Indexed</p>
                </div>
                <span className="ap-status-chip ap-status-success text-[10px]" aria-label="Status: Indexed">
                  Indexed
                </span>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
