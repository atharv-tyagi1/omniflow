import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthContext } from "@/context/AuthContext"

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
  usePathname: jest.fn(() => "/overview"),
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

const { fetchApi } = require("@/lib/api-client")
const { ApiError } = require("@/lib/api-client")

const MOCK_WORKSPACE = { id: "ws-test", name: "WS Test" }
const MOCK_USER = { id: "u1", name: "User", email: "u@u.com", role: "admin" }

function makeQC() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
    },
  })
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = makeQC()
  return (
    <AuthContext.Provider value={{ user: MOCK_USER, workspace: MOCK_WORKSPACE, isAuthenticated: true, isLoading: false }}>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </AuthContext.Provider>
  )
}

describe("API Integration Failures", () => {
  const OverviewPage = require("@/app/(dashboard)/overview/page").default

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("handles 401 Unauthorized securely", async () => {
    const error = new ApiError(401, "Unauthorized")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
      expect(screen.queryByText(/Unauthorized/i)).not.toBeInTheDocument()
    })
  })

  it("handles 403 Forbidden securely", async () => {
    const error = new ApiError(403, "Forbidden")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
      expect(screen.queryByText(/Forbidden/i)).not.toBeInTheDocument()
    })
  })

  it("handles 404 Missing Endpoint without crashing", async () => {
    const error = new ApiError(404, "Not Found")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it("handles 422 Validation Error gracefully", async () => {
    const error = new ApiError(422, "Validation Error")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it("handles 429 Rate Limit", async () => {
    const error = new ApiError(429, "Too Many Requests")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it("handles 500 Backend Failure", async () => {
    const error = new ApiError(500, "Internal Server Error")
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
      expect(screen.queryByText(/Internal Server/i)).not.toBeInTheDocument()
    })
  })

  it("handles network timeout or abort", async () => {
    const error = new Error("Timeout") as any
    error.code = "VALIDATION_ERROR"
    fetchApi.mockRejectedValue(error)
    render(<OverviewPage />, { wrapper: Wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })
})
