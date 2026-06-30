"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Mail } from "lucide-react"

export default function ForgotPasswordPage() {
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
        <h2 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">Reset password</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Enter your email and we'll send you a link to reset your password.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text-secondary)]" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              placeholder="name@example.com"
              className="ap-focus w-full px-3 py-2 bg-[var(--color-background)] border border-[var(--color-border-strong)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-500"
            />
          </div>

          <Button type="submit" className="ap-focus w-full primary-gradient-bg text-white border-none shadow-[0_0_12px_rgba(99,102,241,0.25)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200">
            Send Reset Link
          </Button>
          
          <div className="text-center mt-4">
            <Link href="/login" className="ap-focus text-sm text-indigo-400 hover:text-indigo-300 transition-colors rounded-sm">
              Back to login
            </Link>
          </div>
        </form>
      ) : (
        <div className="space-y-4 text-center">
          <div className="flex justify-center">
            <div className="h-12 w-12 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center">
              <Mail className="h-6 w-6" />
            </div>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            If an account exists for that email, we have sent a password reset link.
          </p>
          <div className="pt-4">
            <Link href="/login" className="ap-focus rounded-lg block">
              <Button className="w-full border border-[var(--color-border-strong)] bg-transparent text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]">
                Return to Login
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
