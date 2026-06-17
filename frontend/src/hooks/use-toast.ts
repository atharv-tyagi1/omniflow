import { create } from "zustand"
import * as React from "react"

export type ToastType = "success" | "error" | "warning" | "info"

export interface Toast {
  id: string
  title?: string
  description: string
  type: ToastType
  duration?: number
}

interface ToastState {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, "id">) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(2, 9)
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }))
    if (toast.duration !== Infinity) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
      }, toast.duration || 5000)
    }
  },
  removeToast: (id) => {
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
  }
}))

export function useToast() {
  const { addToast, removeToast } = useToastStore()

  const toast = React.useCallback(
    ({ title, description, type = "info", duration = 5000 }: Omit<Toast, "id">) => {
      addToast({ title, description, type, duration })
    },
    [addToast]
  )

  return { toast, dismiss: removeToast }
}
