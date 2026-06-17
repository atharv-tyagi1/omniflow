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
        <h2 className="text-2xl font-bold tracking-tight text-white">Reset password</h2>
        <p className="text-sm text-neutral-400">
          Enter your email and we'll send you a link to reset your password.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-200" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              placeholder="name@example.com"
              className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
            Send Reset Link
          </Button>
          
          <div className="text-center mt-4">
            <Link href="/login" className="text-sm text-neutral-400 hover:text-white transition-colors">
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
          <p className="text-sm text-neutral-300">
            If an account exists for that email, we have sent a password reset link.
          </p>
          <div className="pt-4">
            <Link href="/login">
              <Button variant="outline" className="w-full">
                Return to Login
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
