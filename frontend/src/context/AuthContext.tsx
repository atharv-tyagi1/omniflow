"use client"

import * as React from "react"
import { api } from "@/lib/api"
import { useRouter } from "next/navigation"

export interface User {
  id: string
  full_name: string
  email: string
  role: string
  workspace_id: string
  status: string
}

export interface Workspace {
  id: string
  name: string
}

export interface AuthContextType {
  user: User | null
  workspace: Workspace | null
  isAuthenticated: boolean
  isLoading: boolean
  checkSession: () => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [state, setState] = React.useState<{
    user: User | null
    workspace: Workspace | null
    isAuthenticated: boolean
    isLoading: boolean
  }>({
    user: null,
    workspace: null,
    isAuthenticated: false,
    isLoading: true
  })

  const checkSession = React.useCallback(async () => {
    try {
      // The backend returns { data: User } inside a success_response envelope
      const response: any = await api.get('/api/v1/auth/me')
      if (response && response.data) {
        setState({
          user: response.data,
          workspace: response.data.workspace_id ? { id: response.data.workspace_id, name: "Workspace" } : null,
          isAuthenticated: true,
          isLoading: false
        })
      } else {
        throw new Error("Invalid response format")
      }
    } catch (error) {
      setState({
        user: null,
        workspace: null,
        isAuthenticated: false,
        isLoading: false
      })
    }
  }, [])

  const logout = React.useCallback(async () => {
    try {
      await api.post('/api/v1/auth/logout', {})
    } catch (e) {
      // Ignore errors on logout
    } finally {
      localStorage.removeItem("access_token")
      setState({
        user: null,
        workspace: null,
        isAuthenticated: false,
        isLoading: false
      })
      router.push("/login")
    }
  }, [router])

  React.useEffect(() => {
    checkSession()
  }, [checkSession])

  return (
    <AuthContext.Provider value={{ ...state, checkSession, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = React.useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
