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
import { PageShell } from "@/components/ui/dashboard-primitives"

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

  if (isLoading) return <div className="text-neutral-400">Loading workspace...</div>
  if (isError) return <div className="text-red-400">Failed to load workspace.</div>

  const isOwnerOrAdmin = user?.role === "owner" || user?.role === "admin"

  return (
    <PageShell variant="standard">
      <div>
        <h3 className="text-lg font-medium text-white">Workspace Settings</h3>
        <p className="text-sm text-neutral-400">Manage your organization's workspace preferences.</p>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
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
            <label className="text-sm font-medium text-neutral-200">Workspace Name</label>
            <input
              {...register("name")}
              disabled={!isOwnerOrAdmin}
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            />
            {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200">Timezone</label>
            <select
              {...register("timezone")}
              disabled={!isOwnerOrAdmin}
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
              <option value="America/Los_Angeles">America/Los_Angeles</option>
              <option value="Europe/London">Europe/London</option>
            </select>
          </div>

          {isOwnerOrAdmin && (
            <Button type="submit" disabled={updateMutation.isPending} className="bg-indigo-600 hover:bg-indigo-700 text-white">
              {updateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Save Workspace
            </Button>
          )}
          {!isOwnerOrAdmin && (
            <p className="text-xs text-neutral-500">Only workspace administrators can edit these settings.</p>
          )}
        </form>
      </div>
    </PageShell>
  )
}
