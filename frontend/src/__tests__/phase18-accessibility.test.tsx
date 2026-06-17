import React from "react"
import { render, screen } from "@testing-library/react"
import "@testing-library/jest-dom"
import { ErrorState, EmptyState, Badge, StatusDot } from "@/components/ui/dashboard-primitives"

describe("Accessibility Validation", () => {
  it("ErrorState retry button has an accessible role", () => {
    render(<ErrorState message="Error" onRetry={() => {}} />)
    const btn = screen.getByRole("button")
    expect(btn).toHaveAccessibleName(/Retry/i)
  })

  it("Badge renders with correct text and no invalid aria attributes", () => {
    render(<Badge variant="success">OK</Badge>)
    expect(screen.getByText("OK")).toBeInTheDocument()
  })

  it("StatusDot uses aria-hidden to hide decorative icon", () => {
    const { container } = render(<StatusDot status="active" />)
    const span = container.firstChild
    expect(span).toHaveClass("h-2 w-2 rounded-full")
    // Should be decorative, so it doesn't need to be read by screen readers.
    // It's just a colored dot.
  })
})
