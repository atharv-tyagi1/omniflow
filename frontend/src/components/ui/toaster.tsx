"use client"

import * as React from "react"
import { useToastStore } from "@/hooks/use-toast"
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from "lucide-react"
import { cn } from "@/lib/utils"

const icons = {
  success: <CheckCircle2 className="h-5 w-5 text-green-400" />,
  error: <AlertCircle className="h-5 w-5 text-red-400" />,
  warning: <AlertTriangle className="h-5 w-5 text-yellow-400" />,
  info: <Info className="h-5 w-5 text-blue-400" />
}

export function Toaster() {
  const { toasts, removeToast } = useToastStore()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "flex items-start p-4 rounded-xl shadow-lg border backdrop-blur-md",
            "bg-neutral-900/90 border-neutral-800",
            "animate-in slide-in-from-bottom-5 fade-in duration-300"
          )}
          role="alert"
        >
          <div className="shrink-0 mr-3 mt-0.5">{icons[toast.type]}</div>
          <div className="flex-1">
            {toast.title && <h4 className="text-sm font-semibold text-white">{toast.title}</h4>}
            <p className="text-sm text-neutral-300 mt-1">{toast.description}</p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="shrink-0 ml-4 text-neutral-500 hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
