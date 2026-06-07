"use client"

import React, { Component, ErrorInfo, ReactNode } from "react"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "./button"

interface Props {
  children?: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo)
    try {
      // Lazy load to avoid circular deps if any
      const { trackEvent } = require("@/lib/telemetry")
      trackEvent("widget_failure", { error: error.message, componentStack: errorInfo.componentStack })
    } catch (e) {
      // Ignore
    }
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center space-y-4 rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface)]">
          <div className="rounded-full bg-[var(--color-error)]/10 p-4">
            <AlertCircle className="h-8 w-8 text-[var(--color-error)]" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Something went wrong</h2>
            <p className="text-sm text-[var(--color-text-muted)] max-w-md mx-auto">
              {this.state.error?.message || "An unexpected error occurred while rendering this component."}
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Try again
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}
