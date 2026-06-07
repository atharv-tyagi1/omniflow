"use client"

import * as React from "react"
import { ResponsiveContainer } from "recharts"
import { cn } from "@/lib/utils"

export interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactElement
  minHeight?: number
}

export function ChartContainer({ children, minHeight = 300, className, ...props }: ChartContainerProps) {
  return (
    <div 
      className={cn("w-full", className)} 
      style={{ minHeight }}
      {...props}
    >
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  )
}
