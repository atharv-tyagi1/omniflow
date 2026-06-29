import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/context/AuthContext"
import { ThemeProvider } from "@/context/ThemeProvider"
import { QueryProvider } from "@/context/QueryProvider"
import { Toaster } from "@/components/ui/toaster"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "OmniFlow | AI Customer Operations",
  description: "Next-generation customer operations platform powered by agentic AI",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      {/* Anti-flash: apply theme class before first paint to prevent FOIC */}
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var t = localStorage.getItem('omniflow-theme') || 'dark';
                if (t === 'system') {
                  t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }
                document.documentElement.classList.add(t);
              } catch(e) {
                document.documentElement.classList.add('dark');
              }
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem storageKey="omniflow-theme">
          <QueryProvider>
            <AuthProvider>
              {children}
              <Toaster />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
