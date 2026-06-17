import { ZodError } from "zod"
import { hasCapability, CapabilityKeys } from "@/lib/api-capabilities/registry"

interface FetchOptions extends RequestInit {
  params?: Record<string, string>
  requiredCapability?: CapabilityKeys
}

export class ApiError extends Error {
  constructor(public status: number, public message: string, public code?: string) {
    super(message)
    this.name = "ApiError"
  }
}

export class RateLimitError extends ApiError {
  constructor(public retryAfterSeconds: number) {
    super(429, "Too many requests. Please try again shortly.", "RATE_LIMIT")
    this.name = "RateLimitError"
  }
}

export async function fetchApi<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, requiredCapability, ...init } = options

  if (requiredCapability && !hasCapability(requiredCapability)) {
    throw new ApiError(503, `Feature disabled: ${requiredCapability}`, "CAPABILITY_DISABLED")
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const url = new URL(`${baseUrl}${endpoint}`)
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.append(key, value)
    })
  }

  const headers = new Headers(init.headers)
  headers.set("Content-Type", "application/json")
  
  const token = localStorage.getItem("access_token")
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  try {
    const response = await fetch(url.toString(), {
      ...init,
      headers,
    })

    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After")
      const retryAfterSeconds = retryAfter ? parseInt(retryAfter, 10) : 30
      throw new RateLimitError(retryAfterSeconds)
    }

    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json()
      } catch {
        errorData = { message: response.statusText }
      }
      throw new ApiError(response.status, errorData.detail || errorData.message || "API request failed", errorData.code)
    }

    if (response.status === 204) {
      return null as any // Return null for 204 NO CONTENT
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new Error(`Network error: ${(error as Error).message}`)
  }
}

export function handleZodError(error: unknown): never {
  if (error instanceof ZodError) {
    // Sanitize the internal zod error payload
    const issues = error.issues.map((e: any) => `${e.path.join(".")}: ${e.message}`).join(", ")
    throw new ApiError(422, `Invalid response format: ${issues}`, "VALIDATION_ERROR")
  }
  throw error
}
