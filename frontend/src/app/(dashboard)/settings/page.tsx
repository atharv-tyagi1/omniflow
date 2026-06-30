"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { api } from "@/lib/api"
import { PageShell, SectionCard, PageHeader } from "@/components/ui/dashboard-primitives"
import { ThemeToggle } from "@/components/ui/theme-toggle"

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

  if (!user) return <div className="text-[var(--color-text-muted)]">Loading profile...</div>

  return (
    <PageShell variant="standard">
      <PageHeader 
        title="General Information"
        subtitle="Update your personal account details."
      />
      
      <SectionCard title="Profile Details" className="max-w-2xl">
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
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Full Name</label>
            <input
              {...register("full_name")}
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-indigo-500"
            />
            {errors.full_name && <p className="text-xs text-red-400">{errors.full_name.message}</p>}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]">Email Address</label>
            <input
              {...register("email")}
              type="email"
              disabled
              className="ap-focus w-full px-3 py-2 bg-[var(--color-surface-elevated)] border border-[var(--color-border-subtle)] rounded-lg text-sm text-[var(--color-text-muted)] cursor-not-allowed"
            />
            <p className="text-xs text-[var(--color-text-muted)]">Email addresses cannot be changed directly.</p>
          </div>

          <Button type="submit" disabled={isSubmitting} className="ap-focus primary-gradient-bg text-white border-none shadow-[0_0_12px_rgba(99,102,241,0.25)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200">
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Save Changes
          </Button>
        </form>
      </SectionCard>
      <SectionCard title="Appearance" className="max-w-2xl mt-6">
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-[var(--color-text-secondary)]">Theme Preference</label>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <span className="text-xs text-[var(--color-text-muted)]">Choose your preferred visual mode across the platform.</span>
          </div>
        </div>
      </SectionCard>
    </PageShell>
  )
}
