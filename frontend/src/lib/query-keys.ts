export const queryKeys = {
  analytics: {
    overview: (workspaceId: string, params: any) => ["analytics", "overview", workspaceId, params] as const,
    conversations: (workspaceId: string, params: any) => ["analytics", "conversations", workspaceId, params] as const,
    sales: (workspaceId: string, params: any) => ["analytics", "sales", workspaceId, params] as const,
    support: (workspaceId: string, params: any) => ["analytics", "support", workspaceId, params] as const,
    customerCare: (workspaceId: string, params: any) => ["analytics", "customerCare", workspaceId, params] as const,
    handoffs: (workspaceId: string, params: any) => ["analytics", "handoffs", workspaceId, params] as const,
    trends: (workspaceId: string, metric: string, params: any) => ["analytics", "trends", workspaceId, metric, params] as const,
  },
  intel: {
    topics: (workspaceId: string, params: any) => ["intel", "topics", workspaceId, params] as const,
    sentiment: (workspaceId: string, params: any) => ["intel", "sentiment", workspaceId, params] as const,
    anomalies: (workspaceId: string, params: any) => ["intel", "anomalies", workspaceId, params] as const,
  },
  business: {
    insights: (workspaceId: string) => ["business", "insights", workspaceId] as const,
    recommendations: (workspaceId: string) => ["business", "recommendations", workspaceId] as const,
    reports: (workspaceId: string) => ["business", "reports", workspaceId] as const,
    reportDetail: (workspaceId: string, id: string) => ["business", "reports", workspaceId, id] as const,
  },
  agents: {
    list: (workspaceId: string) => ["agents", "list", workspaceId] as const,
    metrics: (workspaceId: string) => ["agents", "metrics", workspaceId] as const,
  },
  apiKeys: {
    list: (workspaceId: string, params?: any) => ["apiKeys", "list", workspaceId, params] as const,
  },
  knowledge: {
    documents: (workspaceId: string) => ["knowledge", "documents", workspaceId] as const,
    datasets: (workspaceId: string) => ["knowledge", "datasets", workspaceId] as const,
  }
}
