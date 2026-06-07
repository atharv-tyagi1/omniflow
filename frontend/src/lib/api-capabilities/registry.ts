import capabilities from "@/config/capabilities.json"

export type CapabilityKeys = keyof typeof capabilities

export const apiCapabilities: Record<CapabilityKeys, boolean> = capabilities

export function hasCapability(feature: CapabilityKeys): boolean {
  return !!apiCapabilities[feature]
}
