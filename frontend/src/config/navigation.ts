import { 
  LayoutDashboard, 
  BarChart3, 
  MessageSquare, 
  Lightbulb, 
  FileText, 
  Bot, 
  Key, 
  BookOpen, 
  Settings, 
  Users, 
  CreditCard 
} from "lucide-react"

export type NavItem = {
  title: string
  href: string
  icon: any
  capability?: string // maps to API Capability Registry
}

export type NavGroup = {
  title: string
  items: NavItem[]
}

export const navigationConfig: NavGroup[] = [
  {
    title: "Operations",
    items: [
      {
        title: "Overview",
        href: "/overview",
        icon: LayoutDashboard,
      },
      {
        title: "Analytics",
        href: "/analytics",
        icon: BarChart3,
      },
      {
        title: "Conversation Intel",
        href: "/intelligence",
        icon: MessageSquare,
      },
    ]
  },
  {
    title: "Intelligence",
    items: [
      {
        title: "Business Analyst",
        href: "/business-analyst",
        icon: Lightbulb,
        capability: "businessInsights"
      },
      {
        title: "Executive Reports",
        href: "/reports",
        icon: FileText,
        capability: "businessReports"
      },
    ]
  },
  {
    title: "Platform",
    items: [
      {
        title: "AI Agents",
        href: "/agents",
        icon: Bot,
        capability: "agentMetrics"
      },
      {
        title: "Knowledge Base",
        href: "/knowledge-base",
        icon: BookOpen,
      },
      {
        title: "API Management",
        href: "/api-management",
        icon: Key,
        capability: "apiKeys"
      },
    ]
  },
  {
    title: "Administration",
    items: [
      {
        title: "Workspace Settings",
        href: "/settings",
        icon: Settings,
      },
      {
        title: "Team Members",
        href: "/team",
        icon: Users,
      },
      {
        title: "Billing",
        href: "/billing",
        icon: CreditCard,
      },
    ]
  }
]
