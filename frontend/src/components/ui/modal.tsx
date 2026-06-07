import * as React from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"

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
      <div className="relative z-50 w-full max-w-md p-6 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] shadow-xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-start justify-between mb-4">
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
        
        {children}
      </div>
    </div>
  )
}
