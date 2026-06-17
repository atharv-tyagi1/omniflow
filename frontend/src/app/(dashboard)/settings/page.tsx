"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { api } from "@/lib/api"
import { PageShell } from "@/components/ui/dashboard-primitives"

const profileSchema = z.object({
  full_name: z.string().min(1, "Name is required."),
  email: z.string().email("Invalid email address.")
})

export default function GeneralSettingsPage() {
  const { user, checkSession } = useAuth()
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting }
  } = useForm<z.infer<typeof profileSchema>>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || "",
      email: user?.email || ""
    }
  })

  React.useEffect(() => {
    if (user) {
      reset({ full_name: user.full_name, email: user.email })
    }
  }, [user, reset])

  const onSubmit = async (data: z.infer<typeof profileSchema>) => {
    setSuccessMsg(null)
    setErrorMsg(null)
    try {
      await api.put('/api/v1/users/me', data)
      await checkSession() // reload user
      setSuccessMsg("Profile updated successfully.")
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update profile.")
    }
  }

  if (!user) return <div className="text-neutral-400">Loading profile...</div>

  return (
    <PageShell variant="standard">
      <div>
        <h3 className="text-lg font-medium text-white">General Information</h3>
        <p className="text-sm text-neutral-400">Update your personal account details.</p>
      </div>
      
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
          {successMsg && (
            <div className="p-3 bg-green-900/30 border border-green-500/50 rounded-lg text-sm text-green-200">
              {successMsg}
            </div>
          )}
          {errorMsg && (
            <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-sm text-red-200">
              {errorMsg}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200">Full Name</label>
            <input
              {...register("full_name")}
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white focus:ring-2 focus:ring-indigo-500"
            />
            {errors.full_name && <p className="text-xs text-red-400">{errors.full_name.message}</p>}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200">Email Address</label>
            <input
              {...register("email")}
              type="email"
              disabled
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-neutral-500 cursor-not-allowed"
            />
            <p className="text-xs text-neutral-500">Email addresses cannot be changed directly.</p>
          </div>

          <Button type="submit" disabled={isSubmitting} className="bg-indigo-600 hover:bg-indigo-700 text-white">
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Save Changes
          </Button>
        </form>
      </div>
    </PageShell>
  )
}
