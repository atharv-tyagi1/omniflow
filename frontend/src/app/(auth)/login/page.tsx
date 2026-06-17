"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { api } from "@/lib/api"

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required.")
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const { checkSession, isAuthenticated, isLoading } = useAuth()
  const [serverError, setServerError] = React.useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema)
  })

  // Redirect if already logged in
  React.useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/overview")
    }
  }, [isLoading, isAuthenticated, router])

  const onSubmit = async (data: LoginFormValues) => {
    setServerError(null)
    try {
      const response: any = await api.post('/api/v1/auth/login', data)
      if (response && response.data && response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token)
        await checkSession() // Update context
        router.push("/overview")
      } else {
        setServerError("Invalid response from server.")
      }
    } catch (err: any) {
      setServerError(err.message || "Invalid credentials.")
    }
  }

  // Prevent flash while checking session
  if (isLoading || isAuthenticated) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-white">Welcome back</h2>
        <p className="text-sm text-neutral-400">
          Enter your email and password to access your account.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {serverError && (
          <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-sm text-red-200">
            {serverError}
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-200" htmlFor="email">
            Email
          </label>
          <input
            {...register("email")}
            id="email"
            type="email"
            placeholder="name@example.com"
            className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isSubmitting}
          />
          {errors.email && (
            <p className="text-sm text-red-400">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-neutral-200" htmlFor="password">
              Password
            </label>
            <Link 
              href="/forgot-password" 
              className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <input
            {...register("password")}
            id="password"
            type="password"
            className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isSubmitting}
          />
          {errors.password && (
            <p className="text-sm text-red-400">{errors.password.message}</p>
          )}
        </div>

        <Button 
          type="submit" 
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" 
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </Button>
      </form>
    </div>
  )
}
