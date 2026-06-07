class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message)
    this.name = "ApiError"
  }
}

class RateLimitError extends ApiError {
  constructor(public retryAfterSeconds: number) {
    super(429, "Too many requests. Please try again shortly.")
    this.name = "RateLimitError"
  }
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  
  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  }
  
  // Future: inject Auth JWT here when implemented
  
  const url = `${baseUrl}${endpoint}`
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
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
      throw new ApiError(response.status, errorData.detail || errorData.message || "API request failed", errorData)
    }

    // Handle empty 204 responses
    if (response.status === 204) {
      return null
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new Error(`Network error: ${(error as Error).message}`)
  }
}
