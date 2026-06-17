"use client"

import * as React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Shield, Mail, Trash2, MoreVertical } from "lucide-react"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"
import { ErrorBoundary } from "@/components/ui/error-boundary"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard, PageShell } from "@/components/ui/dashboard-primitives"

function TeamPageContent() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const { data: members, isLoading, isError, error } = useQuery({
    queryKey: ["workspace", "members"],
    queryFn: async () => {
      const res: any = await api.get("/api/v1/workspaces/members")
      return res.data
    }
  })

  const roleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string, role: string }) => {
      const res: any = await api.put(`/api/v1/users/${userId}/role`, { role })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace", "members"] })
    }
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SkeletonCard className="h-16" />
        <SkeletonCard className="h-16" />
        <SkeletonCard className="h-16" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
        <h3 className="text-red-400 font-medium">Failed to load team members</h3>
        <p className="text-sm text-red-300 mt-1">{(error as any).message || "An unexpected error occurred."}</p>
      </div>
    )
  }

  const isOwnerOrAdmin = user?.role === "owner" || user?.role === "admin"

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Team Members</h2>
          <p className="text-sm text-neutral-400 mt-1">
            Manage your workspace members and their roles.
          </p>
        </div>
        {isOwnerOrAdmin && (
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white" disabled>
            Invite Member (Coming Soon)
          </Button>
        )}
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-neutral-950 text-neutral-400 border-b border-neutral-800">
              <tr>
                <th className="px-6 py-4 font-medium">User</th>
                <th className="px-6 py-4 font-medium">Role</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {members?.map((member: any) => (
                <tr key={member.id} className="hover:bg-neutral-800/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                        {member.full_name?.charAt(0) || member.email?.charAt(0) || "U"}
                      </div>
                      <div>
                        <div className="font-medium text-neutral-200">{member.full_name || "Unknown"}</div>
                        <div className="text-xs text-neutral-500">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {isOwnerOrAdmin && member.id !== user?.id && member.role !== "owner" ? (
                      <select
                        className="bg-neutral-950 border border-neutral-800 rounded px-2 py-1 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        value={member.role}
                        onChange={(e) => roleMutation.mutate({ userId: member.id, role: e.target.value })}
                        disabled={roleMutation.isPending}
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                      </select>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs font-medium text-neutral-300 capitalize">
                        {member.role}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-neutral-400" disabled>
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!members || members.length === 0) && (
            <EmptyState 
              title="No members found" 
              description="It looks like you're the only one here." 
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default function TeamPage() {
  return (
    <PageShell variant="standard">
      <ErrorBoundary>
        <TeamPageContent />
      </ErrorBoundary>
    </PageShell>
  )
}
