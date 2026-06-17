import { ReactNode } from "react"
import { Shield } from "lucide-react"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="h-12 w-12 bg-indigo-500/20 text-indigo-400 rounded-xl flex items-center justify-center mb-4">
            <Shield className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold text-neutral-50 tracking-tight">OmniFlow</h1>
          <p className="text-sm text-neutral-400 mt-2">
            AI-Powered Customer Operations
          </p>
        </div>
        
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 sm:p-8 shadow-xl">
          {children}
        </div>
      </div>
    </div>
  )
}
