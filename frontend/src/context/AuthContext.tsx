"use client"

import * as React from "react"

export interface User {
  id: string
  name: string
  email: string
  role: string
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
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

// MOCK CONSTANTS FOR DEVELOPMENT
const MOCK_USER: User = {
  id: "usr_mock123",
  name: "Developer",
  email: "dev@omniflow.com",
  role: "admin"
}

// Ensure this matches the backend test DB UUID or typical test workspace
const MOCK_WORKSPACE: Workspace = {
  id: "00000000-0000-0000-0000-000000000000",
  name: "OmniFlow Dev Workspace"
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = React.useState<AuthContextType>({
    user: null,
    workspace: null,
    isAuthenticated: false,
    isLoading: true
  })

  React.useEffect(() => {
    // CRITICAL PRODUCTION GUARD
    const isProd = process.env.NODE_ENV === "production"
    const devAuthEnabled = process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true"

    if (isProd && devAuthEnabled) {
      throw new Error("FATAL: DEV_AUTH_ENABLED=true is not permitted in production builds.")
    }

    if (devAuthEnabled || process.env.NODE_ENV === "development") {
      setState({
        user: MOCK_USER,
        workspace: MOCK_WORKSPACE,
        isAuthenticated: true,
        isLoading: false
      })
    } else {
      // Future: Real JWT verification flow
      setState({
        user: null,
        workspace: null,
        isAuthenticated: false,
        isLoading: false
      })
    }
  }, [])

  return (
    <AuthContext.Provider value={state}>
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
