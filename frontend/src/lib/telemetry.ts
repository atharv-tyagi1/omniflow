export type TelemetryEventName = 
  | "page_load"
  | "route_transition"
  | "api_failure"
  | "widget_failure"
  | "permission_denied"
  | "capability_blocked"

export interface TelemetryPayload {
  [key: string]: string | number | boolean | undefined
}

export function trackEvent(name: TelemetryEventName, payload?: TelemetryPayload) {
  const isProd = process.env.NODE_ENV === "production"
  
  const event = {
    event: name,
    timestamp: new Date().toISOString(),
    ...payload,
  }

  // Vendor-neutral emission logic
  // In a real environment, this would post to a telemetry collector endpoint
  // Here we use console out for visibility and tests
  
  if (!isProd) {
    console.debug(`[Telemetry] ${name}`, event)
  }
  
  // Future: fetchApi("/api/internal/v1/telemetry", { method: "POST", body: JSON.stringify(event) })
}
