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
        <h2 className="text-2xl font-bold tracking-tight text-white">Choose a new password</h2>
        <p className="text-sm text-neutral-400">
          Enter your new password below to reset your account credentials.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200" htmlFor="password">
              New Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200" htmlFor="confirm_password">
              Confirm Password
            </label>
            <input
              id="confirm_password"
              type="password"
              required
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
            Reset Password
          </Button>
        </form>
      ) : (
        <div className="space-y-4 text-center">
          <p className="text-sm text-neutral-300">
            Your password has been successfully reset.
          </p>
          <div className="pt-4">
            <Link href="/login">
              <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                Proceed to Login
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
