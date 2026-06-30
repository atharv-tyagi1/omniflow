import { ReactNode } from "react"
import { GLASS_CARD_CLASSES } from "@/components/ui/dashboard-primitives"
import { cn } from "@/lib/utils"
import { Shield } from "lucide-react"
import { ThemeToggle } from "@/components/ui/theme-toggle"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--color-background)] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Background Glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-violet-600/20 blur-[120px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md space-y-8 relative z-10">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="h-12 w-12 bg-gradient-to-br from-indigo-500 to-violet-600 shadow-[0_0_12px_rgba(99,102,241,0.4)] text-white rounded-xl flex items-center justify-center mb-4">
            <span className="text-xl font-bold leading-none">O</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">OmniFlow</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-2">
            AI-Powered Customer Operations
          </p>
        </div>
        
        <div className={cn(GLASS_CARD_CLASSES, "p-6 sm:p-8")}>
          {children}
        </div>
      </div>
    </div>
  )
}
