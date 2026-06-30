"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Loader2 } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"
import { PageShell, SectionCard, PageHeader } from "@/components/ui/dashboard-primitives"

const workspaceSchema = z.object({
  name: z.string().min(1, "Workspace name is required."),
  timezone: z.string(),
  branding_colors: z.record(z.string(), z.string()).optional()
})

export default function WorkspaceSettingsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null)
  
  const { data: workspace, isLoading, isError } = useQuery({
    queryKey: ["workspace", "current"],
    queryFn: async () => {
      const res: any = await api.get("/api/v1/workspaces/current")
      return res.data
    }
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors }
  } = useForm<z.infer<typeof workspaceSchema>>({
    resolver: zodResolver(workspaceSchema)
  })

  React.useEffect(() => {
    if (workspace) {
      reset({
        name: workspace.name,
        timezone: workspace.timezone || "UTC",
        branding_colors: workspace.branding_colors
      })
    }
  }, [workspace, reset])

  const updateMutation = useMutation({
    mutationFn: async (data: z.infer<typeof workspaceSchema>) => {
      const res: any = await api.put("/api/v1/workspaces/current", data)
      return res.data
    },
    onSuccess: () => {
      setSuccessMsg("Workspace settings updated.")
      queryClient.invalidateQueries({ queryKey: ["workspace", "current"] })
    }
  })

  const onSubmit = (data: z.infer<typeof workspaceSchema>) => {
    setSuccessMsg(null)
    updateMutation.mutate(data)
  }

  if (isLoading) return <div className="text-[var(--color-text-muted)]">Loading workspace...</div>
  if (isError) return <div className="text-red-400">Failed to load workspace.</div>

  const isOwnerOrAdmin = user?.role === "owner" || user?.role === "admin"

  return (
    <PageShell variant="standard">
      <PageHeader 
        title="Workspace Settings"
        subtitle="Manage your organization's workspace preferences."
      />

      <SectionCard title="Workspace Configuration" className="max-w-2xl">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
          {successMsg && (
            <div className="p-3 bg-green-900/30 border border-green-500/50 rounded-lg text-sm text-green-200">
              {successMsg}
            </div>
          )}
          {updateMutation.isError && (
            <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-sm text-red-200">
              {updateMutation.error.message || "Failed to update workspace."}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Workspace Name</label>
            <input
              {...register("name")}
              disabled={!isOwnerOrAdmin}
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
            {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Timezone</label>
            <select
              {...register("timezone")}
              disabled={!isOwnerOrAdmin}
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
              <option value="America/Los_Angeles">America/Los_Angeles</option>
              <option value="Europe/London">Europe/London</option>
            </select>
          </div>

          {isOwnerOrAdmin && (
            <Button type="submit" disabled={updateMutation.isPending} className="ap-focus primary-gradient-bg text-white border-none shadow-[0_0_12px_rgba(99,102,241,0.25)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200">
              {updateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Save Workspace
            </Button>
          )}
          {!isOwnerOrAdmin && (
            <p className="text-xs text-[var(--color-text-muted)]">Only workspace administrators can edit these settings.</p>
          )}
        </form>
      </SectionCard>
    </PageShell>
  )
}
