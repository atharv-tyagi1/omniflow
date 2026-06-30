"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function ResetPasswordPage() {
  const router = useRouter()
  const [submitted, setSubmitted] = React.useState(false)

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Placeholder logic since endpoint does not exist yet.
    setSubmitted(true)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">Choose a new password</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Enter your new password below to reset your account credentials.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]" htmlFor="password">
              New Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]" htmlFor="confirm_password">
              Confirm Password
            </label>
            <input
              id="confirm_password"
              type="password"
              required
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-500"
            />
          </div>

          <Button type="submit" className="ap-focus w-full primary-gradient-bg text-white border-none shadow-[0_0_12px_rgba(99,102,241,0.25)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200">
            Reset Password
          </Button>
        </form>
      ) : (
        <div className="space-y-4 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            Your password has been successfully reset.
          </p>
          <div className="pt-4">
            <Link href="/login" className="ap-focus rounded-lg block">
              <Button className="ap-focus w-full primary-gradient-bg text-white border-none shadow-[0_0_12px_rgba(99,102,241,0.25)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200">
                Proceed to Login
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
