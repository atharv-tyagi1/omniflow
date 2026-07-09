import * as React from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { GLASS_CARD_CLASSES, PerformanceBoundary } from "@/components/ui/dashboard-primitives"
import { cn } from "@/lib/utils"

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
}

export function Modal({ isOpen, onClose, title, description, children }: ModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Content */}
      <div className={cn(
        GLASS_CARD_CLASSES, 
        "relative z-50 w-full max-w-[95vw] md:max-w-md max-h-[85vh] overflow-hidden flex flex-col p-0",
        "mt-auto md:mt-0 mb-0 md:mb-auto rounded-b-none md:rounded-[var(--radius-card)]", // mobile stacking vs desktop
        "animate-in fade-in zoom-in-95 slide-in-from-bottom-10 md:slide-in-from-bottom-0 duration-200"
      )}>
        <div className="flex items-start justify-between p-6 pb-4 border-b border-white/5 shrink-0">
          <div>
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
              {title}
            </h2>
            {description && (
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                {description}
              </p>
            )}
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 -mt-2 -mr-2" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="p-6 pt-4 overflow-y-auto">
          <PerformanceBoundary degradeGlass={false}>
            {children}
          </PerformanceBoundary>
        </div>
      </div>
    </div>
  )
}
