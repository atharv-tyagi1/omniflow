import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import CanvasLayout from "@/components/CanvasLayout";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OmniFlow | Premium Operations",
  description: "AI-native customer operations platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full antialiased theme-light`}
      suppressHydrationWarning
    >
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
      </head>
      <body className="min-h-full flex flex-col bg-[#E5E7EB] text-[#1E293B] overflow-hidden selection:bg-[#4F7CFF]/30">
        <AuthProvider>
          <CanvasLayout>
            {children}
          </CanvasLayout>
        </AuthProvider>
      </body>
    </html>
  );
}
