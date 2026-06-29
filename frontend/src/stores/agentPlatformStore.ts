import { create } from 'zustand'

export type RunStatusFilter = 'all' | 'success' | 'failed' | 'running' | 'cancelled'

interface AgentPlatformState {
  // Selection
  selectedAgentId: string | null
  selectedTabIndex: number // 0=Overview,1=Agents,2=Runs,3=Knowledge,4=API Keys,5=Settings

  // Runs page filters
  runStatusFilter: RunStatusFilter
  runSearchText: string

  // Agents page filters
  agentSearchText: string
  agentCategoryFilter: string | null

  // Actions
  setSelectedAgent: (id: string | null) => void
  setTab: (index: number) => void
  setRunFilter: (status: RunStatusFilter) => void
  setRunSearch: (text: string) => void
  setAgentSearch: (text: string) => void
  setAgentCategory: (category: string | null) => void
  reset: () => void
}

const initialState = {
  selectedAgentId: null,
  selectedTabIndex: 0,
  runStatusFilter: 'all' as RunStatusFilter,
  runSearchText: '',
  agentSearchText: '',
  agentCategoryFilter: null,
}

export const useAgentPlatformStore = create<AgentPlatformState>((set) => ({
  ...initialState,

  setSelectedAgent: (id) => set({ selectedAgentId: id }),
  setTab: (index) => set({ selectedTabIndex: index }),
  setRunFilter: (status) => set({ runStatusFilter: status }),
  setRunSearch: (text) => set({ runSearchText: text }),
  setAgentSearch: (text) => set({ agentSearchText: text }),
  setAgentCategory: (category) => set({ agentCategoryFilter: category }),

  // Called during workspace switch Phase 2
  reset: () => set({ ...initialState }),
}))
