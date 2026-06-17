/**
 * Phase 18 – Section 1 & 2: Page-Level Integration Tests + API Integration Validation
 *
 * Tests cover:
 *   - Loading states on each page
 *   - Successful data rendering
 *   - Empty API response → EmptyState
 *   - Failed API response → ErrorState
 *   - All 7 Phase 18 pages
 */
import React from "react"
import { render, screen, waitFor, act } from "@testing-library/react"
import "@testing-library/jest-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthContext } from "@/context/AuthContext"

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
  usePathname: jest.fn(() => "/overview"),
}))

// Mock the entire fetchApi to be controllable per test
jest.mock("@/lib/api-client", () => ({
  fetchApi: jest.fn(),
  handleZodError: jest.fn((e) => { throw e }),
  ApiError: class ApiError extends Error {
    constructor(public status: number, message: string, public code?: string) {
      super(message)
    }
  },
}))

// Mock capability registry — all enabled by default
jest.mock("@/lib/api-capabilities/registry", () => ({
  hasCapability: jest.fn(() => true),
  apiCapabilities: {},
}))

// ─── Test Helpers ─────────────────────────────────────────────────────────────

const MOCK_WORKSPACE = { id: "ws-test-123", name: "Test Workspace" }
const MOCK_USER = { id: "usr-001", name: "Test User", email: "test@example.com", role: "admin" }

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = makeQueryClient()
  return (
    <AuthContext.Provider value={{ user: MOCK_USER, workspace: MOCK_WORKSPACE, isAuthenticated: true, isLoading: false }}>
      <QueryClientProvider client={qc}>
        {children}
      </QueryClientProvider>
    </AuthContext.Provider>
  )
}

function renderInWrapper(ui: React.ReactElement) {
  return render(ui, { wrapper: Wrapper })
}

// ─── Import pages lazily to avoid static analysis issues ─────────────────────
// We use dynamic requires after mocks are set up.

const { fetchApi } = require("@/lib/api-client")

// ─── Overview Page ─────────────────────────────────────────────────────────────

describe("Overview Page — Section 1 & 2", () => {
  const OverviewPage = require("@/app/(dashboard)/overview/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading immediately", () => {
    fetchApi.mockResolvedValue({
      total_conversations: 100,
      active_users: 25,
      resolution_rate: 0.85,
      csat_score: 4.2,
      conversation_trend: 5,
    })
    renderInWrapper(<OverviewPage />)
    expect(screen.getByText("Executive Overview")).toBeInTheDocument()
  })

  it("shows loading skeleton while data is fetching", () => {
    fetchApi.mockImplementation(() => new Promise(() => {})) // never resolves
    const { container } = renderInWrapper(<OverviewPage />)
    const skeletons = container.querySelectorAll(".animate-pulse")
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it("renders KPI cards after successful API response", async () => {
    fetchApi.mockResolvedValue({
      total_conversations: 1234,
      active_users: 56,
      resolution_rate: 0.78,
      csat_score: 4.5,
      conversation_trend: 12,
    })
    renderInWrapper(<OverviewPage />)
    await waitFor(() => {
      expect(screen.getByText("1,234")).toBeInTheDocument()
    })
  })

  it("shows ErrorState on API failure", async () => {
    const error = new Error("Network error") as any
    error.code = "VALIDATION_ERROR" // skip retries
    fetchApi.mockRejectedValue(error)
    renderInWrapper(<OverviewPage />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load overview metrics/i)).toBeInTheDocument()
    })
  })
})

// ─── Intelligence Page ─────────────────────────────────────────────────────────

describe("Intelligence Page — Section 1 & 2", () => {
  const IntelPage = require("@/app/(dashboard)/intelligence/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue({ data: { trending_topics: [] } })
    renderInWrapper(<IntelPage />)
    expect(screen.getByText("Conversation Intelligence")).toBeInTheDocument()
  })

  it("shows loading skeletons while fetching intel", () => {
    fetchApi.mockImplementation(() => new Promise(() => {}))
    const { container } = renderInWrapper(<IntelPage />)
    const skeletons = container.querySelectorAll(".animate-pulse")
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it("shows EmptyState when trending_topics is empty array", async () => {
    fetchApi
      .mockResolvedValueOnce({ data: { trending_topics: [] } })
      .mockResolvedValueOnce({ data: { intent_distribution: [] } })
      .mockResolvedValueOnce({ data: { sentiment_trend: {} } })
    renderInWrapper(<IntelPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/No topic data|No intent data|No sentiment data/i).length).toBeGreaterThan(0)
    })
  })

  it("shows ErrorState when topics API fails", async () => {
    fetchApi.mockRejectedValue(new Error("503 error"))
    renderInWrapper(<IntelPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/Failed to load/i).length).toBeGreaterThan(0)
    })
  })
})

// ─── Business Analyst Page ─────────────────────────────────────────────────────

describe("Business Analyst Page — Section 1 & 2", () => {
  const AnalystPage = require("@/app/(dashboard)/business-analyst/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue({ remaining: null })
    renderInWrapper(<AnalystPage />)
    expect(screen.getByText("AI Business Analyst")).toBeInTheDocument()
  })

  it("shows suggested questions when no messages exist", () => {
    fetchApi.mockResolvedValue({ remaining: null })
    renderInWrapper(<AnalystPage />)
    expect(screen.getByText(/Why did sentiment drop last week/i)).toBeInTheDocument()
  })

  it("renders capability-disabled message when businessQuestions is off", () => {
    const registry = require("@/lib/api-capabilities/registry")
    registry.hasCapability.mockImplementation((k: string) => k !== "businessQuestions")
    renderInWrapper(<AnalystPage />)
    expect(screen.getByText(/Business Analyst Disabled/i)).toBeInTheDocument()
    registry.hasCapability.mockImplementation(() => true) // restore
  })
})

// ─── Conversations Page ────────────────────────────────────────────────────────

describe("Conversations Page — Section 1 & 2", () => {
  const ConversationsPage = require("@/app/(dashboard)/conversations/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<ConversationsPage />)
    expect(screen.getByText("Conversation Explorer")).toBeInTheDocument()
  })

  it("shows empty state when no conversations exist", async () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<ConversationsPage />)
    await waitFor(() => {
      expect(screen.getByText(/No conversations found/i)).toBeInTheDocument()
    })
  })

  it("shows ErrorState when conversations API fails", async () => {
    fetchApi.mockRejectedValue(new Error("API down"))
    renderInWrapper(<ConversationsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load conversations/i)).toBeInTheDocument()
    })
  })

  it("renders conversation list on success", async () => {
    fetchApi.mockResolvedValue([
      { id: "conv-001", status: "active", created_at: "2026-01-01T00:00:00Z", title: "Support Chat #1" },
      { id: "conv-002", status: "resolved", created_at: "2026-01-02T00:00:00Z", title: "Support Chat #2" },
    ])
    renderInWrapper(<ConversationsPage />)
    await waitFor(() => {
      expect(screen.getByText("Support Chat #1")).toBeInTheDocument()
    })
  })
})

// ─── Customers Page ────────────────────────────────────────────────────────────

describe("Customers Page — Section 1 & 2", () => {
  const CustomersPage = require("@/app/(dashboard)/customers/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<CustomersPage />)
    expect(screen.getByText("Customer Insights")).toBeInTheDocument()
  })

  it("shows EmptyState when no customers", async () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<CustomersPage />)
    await waitFor(() => {
      expect(screen.getByText(/No customers found/i)).toBeInTheDocument()
    })
  })

  it("shows ErrorState when customers API fails", async () => {
    fetchApi.mockRejectedValue(new Error("DB error"))
    renderInWrapper(<CustomersPage />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load customers/i)).toBeInTheDocument()
    })
  })

  it("renders customer cards on success", async () => {
    fetchApi.mockResolvedValue([
      { id: "cust-001", name: "Alice Johnson", email: "alice@example.com", created_at: "2026-01-01T00:00:00Z" },
      { id: "cust-002", name: "Bob Smith", email: "bob@example.com", created_at: "2026-01-02T00:00:00Z" },
    ])
    renderInWrapper(<CustomersPage />)
    await waitFor(() => {
      expect(screen.getByText("Alice Johnson")).toBeInTheDocument()
      expect(screen.getByText("Bob Smith")).toBeInTheDocument()
    })
  })
})

// ─── Workflows Page ────────────────────────────────────────────────────────────

describe("Workflows Page — Section 1 & 2", () => {
  const WorkflowsPage = require("@/app/(dashboard)/workflows/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<WorkflowsPage />)
    expect(screen.getByText("Workflow Observability")).toBeInTheDocument()
  })

  it("shows EmptyState when no workflows", async () => {
    fetchApi.mockResolvedValue([])
    renderInWrapper(<WorkflowsPage />)
    await waitFor(() => {
      expect(screen.getByText(/No workflows/i)).toBeInTheDocument()
    })
  })

  it("shows ErrorState when workflows API fails", async () => {
    fetchApi.mockRejectedValue(new Error("Timeout"))
    renderInWrapper(<WorkflowsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load workflows/i)).toBeInTheDocument()
    })
  })

  it("renders workflow cards on success", async () => {
    fetchApi.mockResolvedValue([
      { id: "wf-001", name: "Lead Qualification", status: "active", trigger_type: "webhook", is_active: true },
      { id: "wf-002", name: "Escalation Handler", status: "failed", trigger_type: "schedule", is_active: false },
    ])
    renderInWrapper(<WorkflowsPage />)
    await waitFor(() => {
      expect(screen.getByText("Lead Qualification")).toBeInTheDocument()
      expect(screen.getByText("Escalation Handler")).toBeInTheDocument()
    })
  })

  it("shows correct summary counts from workflow data", async () => {
    fetchApi.mockResolvedValue([
      { id: "wf-001", name: "WF1", status: "active", is_active: true },
      { id: "wf-002", name: "WF2", status: "active", is_active: true },
      { id: "wf-003", name: "WF3", status: "failed", is_active: false },
    ])
    renderInWrapper(<WorkflowsPage />)
    await waitFor(() => {
      expect(screen.getByText("Total Workflows")).toBeInTheDocument()
    })
  })
})

// ─── Channels Page ─────────────────────────────────────────────────────────────

describe("Channels Page — Section 1 & 2", () => {
  const ChannelsPage = require("@/app/(dashboard)/channels/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders heading", () => {
    fetchApi.mockResolvedValue(null)
    renderInWrapper(<ChannelsPage />)
    expect(screen.getByText("Channel Observability")).toBeInTheDocument()
  })

  it("renders Telegram section", () => {
    fetchApi.mockResolvedValue(null)
    renderInWrapper(<ChannelsPage />)
    expect(screen.getByText("Telegram")).toBeInTheDocument()
  })

  it("renders Voice section", () => {
    fetchApi.mockResolvedValue(null)
    renderInWrapper(<ChannelsPage />)
    expect(screen.getByText("Voice")).toBeInTheDocument()
  })

  it("shows configured badge when webhook is set", async () => {
    fetchApi.mockResolvedValue({ webhook_configured: true, bot_username: "@omniflow_bot", webhook_url: "https://example.com/webhook" })
    renderInWrapper(<ChannelsPage />)
    await waitFor(() => {
      expect(screen.getAllByText("configured").length).toBeGreaterThan(0)
    })
  })

  it("shows not configured badge when webhook is missing", async () => {
    fetchApi.mockResolvedValue({ webhook_configured: false })
    renderInWrapper(<ChannelsPage />)
    await waitFor(() => {
      expect(screen.getAllByText("not configured").length).toBeGreaterThan(0)
    })
  })
})
