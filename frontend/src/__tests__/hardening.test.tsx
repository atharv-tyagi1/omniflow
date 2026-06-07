/// <reference types="@testing-library/jest-dom" />
import * as React from "react"
import { render, screen, act } from "@testing-library/react"
import { AuthGuard } from "@/components/layout/AuthGuard"
import { PermissionGuard } from "@/components/layout/PermissionGuard"
import { DashboardWidget } from "@/components/dashboard/DashboardWidget"
import { AuthContext } from "@/context/AuthContext"
import { fetchApi, handleZodError, ApiError } from "@/lib/api-client"
import { trackEvent } from "@/lib/telemetry"
import { z, ZodError } from "zod"

// Mock modules
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
  usePathname: jest.fn(),
}))

jest.mock("@/lib/telemetry", () => ({
  trackEvent: jest.fn(),
}))

describe("Phase 14.5 Frontend Hardening", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // 1. AuthGuard
  describe("AuthGuard", () => {
    it("renders loading state when auth is loading", () => {
      render(
        <AuthContext.Provider value={{ isAuthenticated: false, isLoading: true, user: null, workspace: null }}>
          <AuthGuard><div>Protected Content</div></AuthGuard>
        </AuthContext.Provider>
      )
      expect(screen.getByText("Authenticating...")).toBeInTheDocument()
      expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
    })

    it("redirects unauthenticated users and prevents flash of content", () => {
      const routerPushMock = jest.fn()
      require("next/navigation").useRouter.mockReturnValue({ push: routerPushMock })

      render(
        <AuthContext.Provider value={{ isAuthenticated: false, isLoading: false, user: null, workspace: null }}>
          <AuthGuard><div>Protected Content</div></AuthGuard>
        </AuthContext.Provider>
      )
      
      expect(routerPushMock).toHaveBeenCalledWith("/login")
      expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
    })
  })

  // 2. PermissionGuard
  describe("PermissionGuard", () => {
    it("blocks access and renders AccessDeniedState when check fails", () => {
      const mockUser = { id: "u1", name: "User", email: "user@test.com", role: "viewer", workspaces: [] }
      const mockCheck = jest.fn(() => false)

      render(
        <AuthContext.Provider value={{ isAuthenticated: true, isLoading: false, user: mockUser as any, workspace: null }}>
          <PermissionGuard checkPermission={mockCheck} featureName="Secure Area">
            <div>Secret Data</div>
          </PermissionGuard>
        </AuthContext.Provider>
      )

      expect(screen.getByText("Access Denied")).toBeInTheDocument()
      expect(screen.queryByText("Secret Data")).not.toBeInTheDocument()
      expect(trackEvent).toHaveBeenCalledWith("permission_denied", { feature: "Secure Area", role: "viewer" })
    })
  })

  // 3. Widget Error Isolation
  describe("Widget Error Isolation", () => {
    it("catches synchronous render crashes in children and emits telemetry", () => {
      // Suppress console.error for expected React boundary logs
      const spy = jest.spyOn(console, "error").mockImplementation(() => {})
      
      const CrashingComponent = () => {
        throw new Error("Synthetic crash")
      }

      render(
        <DashboardWidget title="Fragile Widget">
          <CrashingComponent />
        </DashboardWidget>
      )

      // The global ErrorBoundary renders "Something went wrong" instead of the child component
      expect(screen.getByText("Something went wrong")).toBeInTheDocument()
      
      // Telemetry must be emitted
      expect(trackEvent).toHaveBeenCalledWith(
        "widget_failure", 
        expect.objectContaining({ error: "Synthetic crash" })
      )

      spy.mockRestore()
    })
  })

  // 4. Zod Validation
  describe("Zod Validation Safety", () => {
    it("sanitizes ZodError into ApiError to prevent internal leaks", () => {
      const schema = z.object({ value: z.string() })
      
      try {
        const data = schema.parse({ value: 123 })
      } catch (error) {
        expect(() => handleZodError(error)).toThrow(ApiError)
        expect(() => handleZodError(error)).toThrow(/Invalid response format/)
      }
    })
  })

  // 5. Capability Short Circuit
  describe("Capability Registry Short Circuit", () => {
    it("prevents fetchApi from running if required capability is disabled", async () => {
      // For this test, assume businessInsights is disabled in registry
      jest.mock("@/lib/api-capabilities/registry", () => ({
        hasCapability: (key: string) => key !== "businessInsights"
      }))

      await expect(
        fetchApi("/api/v1/test", { requiredCapability: "businessInsights" })
      ).rejects.toThrow("Feature disabled: businessInsights")
    })
  })
})
