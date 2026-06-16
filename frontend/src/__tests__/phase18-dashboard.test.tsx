/**
 * Phase 18 – Dashboard Component Tests
 * Tests cover: rendering, loading states, error states, empty states
 */
import React from "react"
import { render, screen } from "@testing-library/react"
import "@testing-library/jest-dom"
import {
  Skeleton,
  SkeletonCard,
  ErrorState,
  EmptyState,
  PageHeader,
  SectionCard,
  Badge,
  StatusDot,
} from "@/components/ui/dashboard-primitives"

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    const { container } = render(<Skeleton />)
    expect(container.firstChild).toHaveClass("animate-pulse")
  })
})

describe("SkeletonCard", () => {
  it("renders three skeleton rows", () => {
    const { container } = render(<SkeletonCard />)
    const skeletons = container.querySelectorAll(".animate-pulse")
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })
})

describe("ErrorState", () => {
  it("renders the error message", () => {
    render(<ErrorState message="Something broke" />)
    expect(screen.getByText("Something broke")).toBeInTheDocument()
  })

  it("renders a retry button when onRetry is provided", () => {
    const onRetry = jest.fn()
    render(<ErrorState message="Error" onRetry={onRetry} />)
    const btn = screen.getByRole("button", { name: /retry/i })
    expect(btn).toBeInTheDocument()
    btn.click()
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it("does not render retry button when no onRetry", () => {
    render(<ErrorState message="Error" />)
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })
})

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="Nothing here" description="Add some data." />)
    expect(screen.getByText("Nothing here")).toBeInTheDocument()
    expect(screen.getByText("Add some data.")).toBeInTheDocument()
  })
})

describe("PageHeader", () => {
  it("renders title", () => {
    render(<PageHeader title="Dashboard Title" />)
    expect(screen.getByText("Dashboard Title")).toBeInTheDocument()
  })

  it("renders subtitle when provided", () => {
    render(<PageHeader title="Title" subtitle="Subtitle text" />)
    expect(screen.getByText("Subtitle text")).toBeInTheDocument()
  })

  it("renders children as actions", () => {
    render(
      <PageHeader title="Title">
        <button>Action</button>
      </PageHeader>
    )
    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument()
  })
})

describe("SectionCard", () => {
  it("renders title and children", () => {
    render(
      <SectionCard title="Section Title">
        <p>Card content</p>
      </SectionCard>
    )
    expect(screen.getByText("Section Title")).toBeInTheDocument()
    expect(screen.getByText("Card content")).toBeInTheDocument()
  })
})

describe("Badge", () => {
  it("renders with neutral variant by default", () => {
    const { container } = render(<Badge>Label</Badge>)
    expect(screen.getByText("Label")).toBeInTheDocument()
    expect(container.firstChild).toHaveClass("border")
  })

  it("applies success variant classes", () => {
    const { container } = render(<Badge variant="success">OK</Badge>)
    expect(container.firstChild).toHaveClass("text-emerald-400")
  })

  it("applies error variant classes", () => {
    const { container } = render(<Badge variant="error">Fail</Badge>)
    expect(container.firstChild).toHaveClass("text-red-400")
  })
})

describe("StatusDot", () => {
  it("renders green dot for active status", () => {
    const { container } = render(<StatusDot status="active" />)
    expect(container.firstChild).toHaveClass("bg-emerald-400")
  })

  it("renders red dot for failed status", () => {
    const { container } = render(<StatusDot status="failed" />)
    expect(container.firstChild).toHaveClass("bg-red-400")
  })

  it("falls back to gray for unknown status", () => {
    const { container } = render(<StatusDot status="unknown-status" />)
    expect(container.firstChild).toHaveClass("bg-gray-400")
  })
})
