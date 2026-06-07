import { User } from "@/context/AuthContext"

// Mock permission mappings for early phase
export function canViewAnalytics(user: User | null): boolean {
  if (!user) return false
  return ["admin", "manager", "analyst"].includes(user.role)
}

export function canViewReports(user: User | null): boolean {
  if (!user) return false
  return ["admin", "manager"].includes(user.role)
}

export function canManageApiKeys(user: User | null): boolean {
  if (!user) return false
  return ["admin"].includes(user.role)
}

export function canViewIntel(user: User | null): boolean {
  if (!user) return false
  return ["admin", "manager", "analyst"].includes(user.role)
}

export function canManageAgents(user: User | null): boolean {
  if (!user) return false
  return ["admin", "manager"].includes(user.role)
}
