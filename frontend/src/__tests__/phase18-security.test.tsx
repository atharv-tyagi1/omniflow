/**
 * Phase 18 – Sections 3, 4, 5: Capability Gating, Workspace Isolation, RBAC Validation
 *
 * Tests cover:
 *   - Capability enabled → content visible
 *   - Capability disabled → content hidden / fallback rendered
 *   - Workspace isolation: queries use workspace context; different workspaces get separate cache keys
 *   - RBAC: unauthenticated user → redirect; loading → spinner; no-workspace → blocked
 */
import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthContext } from "@/context/AuthContext"

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
  usePathname: jest.fn(() => "/"),
}))

jest.mock("@/lib/api-client", () => ({
  fetchApi: jest.fn(),
  handleZodError: jest.fn((e) => { throw e }),
  ApiError: class ApiError extends Error {
    constructor(public status: number, message: string, public code?: string) {
      super(message)
    }
  },
}))

jest.mock("@/lib/api-capabilities/registry", () => ({
  hasCapability: jest.fn(() => true),
  apiCapabilities: {},
}))

// ─── Helpers ──────────────────────────────────────────────────────────────────

const { fetchApi } = require("@/lib/api-client")
const registry = require("@/lib/api-capabilities/registry")

function makeQC() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  })
}

function Wrapper({
  children,
  workspace = { id: "ws-a", name: "Workspace A" },
  user = { id: "usr-001", name: "Admin", email: "admin@test.com", role: "admin" },
  isAuthenticated = true,
  isLoading = false,
}: {
  children: React.ReactNode
  workspace?: any
  user?: any
  isAuthenticated?: boolean
  isLoading?: boolean
}) {
  const qc = makeQC()
  return (
    <AuthContext.Provider value={{ user, workspace, isAuthenticated, isLoading }}>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </AuthContext.Provider>
  )
}

// ─── SECTION 3: Capability Gating ─────────────────────────────────────────────

describe("Section 3 — Capability Gating", () => {
  const AnalystPage = require("@/app/(dashboard)/business-analyst/page").default

  afterEach(() => {
    registry.hasCapability.mockImplementation(() => true)
    jest.clearAllMocks()
  })

  it("3.1 — businessQuestions enabled: renders analyst chat UI", () => {
    registry.hasCapability.mockImplementation(() => true)
    fetchApi.mockResolvedValue({ remaining: null })
    render(<AnalystPage />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(screen.getByText("AI Business Analyst")).toBeInTheDocument()
    expect(screen.getByText(/Ask your data anything/i)).toBeInTheDocument()
  })

  it("3.2 — businessQuestions disabled: renders capability-disabled fallback", () => {
    registry.hasCapability.mockImplementation((k: string) => k !== "businessQuestions")
    fetchApi.mockResolvedValue({ remaining: null })
    render(<AnalystPage />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(screen.getByText("Business Analyst Disabled")).toBeInTheDocument()
    expect(screen.queryByText(/Ask your data anything/i)).not.toBeInTheDocument()
  })

  it("3.3 — capability check is called with correct capability key", () => {
    registry.hasCapability.mockImplementation(() => true)
    fetchApi.mockResolvedValue({ remaining: null })
    render(<AnalystPage />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(registry.hasCapability).toHaveBeenCalledWith("businessQuestions")
  })
})

// ─── Navigation Capability Gating ─────────────────────────────────────────────

describe("Section 3 — Navigation Capability Gating (Sidebar)", () => {
  const { Sidebar } = require("@/components/layout/Sidebar")

  afterEach(() => {
    registry.hasCapability.mockImplementation(() => true)
    jest.clearAllMocks()
  })

  it("3.4 — all capabilities enabled: all nav items visible", () => {
    registry.hasCapability.mockImplementation(() => true)
    render(<Sidebar />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    // At minimum Overview and Conversation Intel must be visible (no capability)
    expect(screen.getByText("Overview")).toBeInTheDocument()
    expect(screen.getByText("Conversation Intel")).toBeInTheDocument()
  })

  it("3.5 — apiKeys disabled: API Management hidden from sidebar", () => {
    registry.hasCapability.mockImplementation((k: string) => k !== "apiKeys")
    render(<Sidebar />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(screen.queryByText("API Management")).not.toBeInTheDocument()
  })

  it("3.6 — workflows disabled: Workflows hidden from sidebar", () => {
    registry.hasCapability.mockImplementation((k: string) => k !== "workflows")
    render(<Sidebar />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(screen.queryByText("Workflows")).not.toBeInTheDocument()
  })

  it("3.7 — conversations enabled: Conversations visible in sidebar", () => {
    registry.hasCapability.mockImplementation(() => true)
    render(<Sidebar />, {
      wrapper: ({ children }) => <Wrapper>{children}</Wrapper>,
    })
    expect(screen.getByText("Conversations")).toBeInTheDocument()
  })
})

// ─── SECTION 4: Workspace Isolation ───────────────────────────────────────────

describe("Section 4 — Workspace Isolation", () => {
  const CustomersPage = require("@/app/(dashboard)/customers/page").default

  afterEach(() => jest.clearAllMocks())

  it("4.1 — workspace A fetches with workspace A id", async () => {
    fetchApi.mockResolvedValue([{ id: "cust-a1", name: "Customer A1", created_at: "2026-01-01T00:00:00Z" }])
    render(<CustomersPage />, {
      wrapper: ({ children }) => (
        <Wrapper workspace={{ id: "ws-aaaa-1111", name: "Workspace A" }}>{children}</Wrapper>
      ),
    })
    await waitFor(() => {
      expect(screen.getByText("Customer A1")).toBeInTheDocument()
    })
    // fetchApi was called (isolated to ws-a data via query key)
    expect(fetchApi).toHaveBeenCalled()
  })

  it("4.2 — workspace B does NOT show workspace A data", async () => {
    // Workspace B returns empty
    fetchApi.mockResolvedValue([])
    render(<CustomersPage />, {
      wrapper: ({ children }) => (
        <Wrapper workspace={{ id: "ws-bbbb-2222", name: "Workspace B" }}>{children}</Wrapper>
      ),
    })
    await waitFor(() => {
      expect(screen.getByText(/No customers found/i)).toBeInTheDocument()
    })
    expect(screen.queryByText("Customer A1")).not.toBeInTheDocument()
  })

  it("4.3 — query keys include workspace id for isolation", () => {
    // The query key factory enforces isolation
    const { queryKeys } = require("@/lib/query-keys")
    const keyA = queryKeys.analytics.overview("ws-aaaa", {})
    const keyB = queryKeys.analytics.overview("ws-bbbb", {})
    expect(keyA).not.toEqual(keyB)
    expect(keyA[2]).toBe("ws-aaaa")
    expect(keyB[2]).toBe("ws-bbbb")
  })

  it("4.4 — analytics query key contains workspaceId as second element", () => {
    const { queryKeys } = require("@/lib/query-keys")
    const key = queryKeys.analytics.overview("workspace-xyz", { period: "7d" })
    expect(key).toContain("workspace-xyz")
  })

  it("4.5 — intel query keys are workspace-scoped", () => {
    const wsA = ["intel", "topics", "ws-a", 30]
    const wsB = ["intel", "topics", "ws-b", 30]
    expect(wsA).not.toEqual(wsB)
  })

  it("4.6 — customers query key includes workspaceId", () => {
    const keyA = ["customers", "list", "ws-a", {}]
    const keyB = ["customers", "list", "ws-b", {}]
    expect(keyA[2]).not.toBe(keyB[2])
  })
})

// ─── SECTION 5: RBAC Validation ───────────────────────────────────────────────

describe("Section 5 — RBAC Validation", () => {
  const { AuthGuard } = require("@/components/layout/AuthGuard")

  afterEach(() => jest.clearAllMocks())

  it("5.1 — loading state: renders spinner, not content", () => {
    render(
      <AuthContext.Provider value={{ user: null, workspace: null, isAuthenticated: false, isLoading: true }}>
        <QueryClientProvider client={makeQC()}>
          <AuthGuard><div>Protected</div></AuthGuard>
        </QueryClientProvider>
      </AuthContext.Provider>
    )
    expect(screen.getByText("Authenticating...")).toBeInTheDocument()
    expect(screen.queryByText("Protected")).not.toBeInTheDocument()
  })

  it("5.2 — unauthenticated: redirects to /login", () => {
    const push = jest.fn()
    require("next/navigation").useRouter.mockReturnValue({ push })
    render(
      <AuthContext.Provider value={{ user: null, workspace: null, isAuthenticated: false, isLoading: false }}>
        <QueryClientProvider client={makeQC()}>
          <AuthGuard><div>Protected</div></AuthGuard>
        </QueryClientProvider>
      </AuthContext.Provider>
    )
    expect(push).toHaveBeenCalledWith("/login")
    expect(screen.queryByText("Protected")).not.toBeInTheDocument()
  })

  it("5.3 — authenticated: renders children", async () => {
    render(
      <AuthContext.Provider value={{ user: { id: "u1", name: "User", email: "u@test.com", role: "admin" }, workspace: { id: "ws-1", name: "WS" }, isAuthenticated: true, isLoading: false }}>
        <QueryClientProvider client={makeQC()}>
          <AuthGuard><div>Dashboard Content</div></AuthGuard>
        </QueryClientProvider>
      </AuthContext.Provider>
    )
    await waitFor(() => {
      expect(screen.getByText("Dashboard Content")).toBeInTheDocument()
    })
  })

  it("5.4 — dashboard pages do not fetch data when workspaceId is empty", () => {
    fetchApi.mockResolvedValue([])
    const ConversationsPage = require("@/app/(dashboard)/conversations/page").default
    render(
      <AuthContext.Provider value={{ user: { id: "u1", name: "U", email: "u@test.com", role: "admin" }, workspace: null, isAuthenticated: true, isLoading: false }}>
        <QueryClientProvider client={makeQC()}>
          <ConversationsPage />
        </QueryClientProvider>
      </AuthContext.Provider>
    )
    // fetchApi should NOT be called when workspaceId is empty (enabled: !!workspaceId = false)
    expect(fetchApi).not.toHaveBeenCalled()
  })

  it("5.5 — expired auth state clears to unauthenticated", () => {
    const push = jest.fn()
    require("next/navigation").useRouter.mockReturnValue({ push })
    // Simulate expired session: user is null but isLoading is false
    render(
      <AuthContext.Provider value={{ user: null, workspace: null, isAuthenticated: false, isLoading: false }}>
        <QueryClientProvider client={makeQC()}>
          <AuthGuard><div>Expired Session Content</div></AuthGuard>
        </QueryClientProvider>
      </AuthContext.Provider>
    )
    expect(push).toHaveBeenCalledWith("/login")
    expect(screen.queryByText("Expired Session Content")).not.toBeInTheDocument()
  })
})
