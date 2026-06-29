'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { useReducedMotion } from 'framer-motion'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  as?: React.ElementType
  style?: React.CSSProperties
}

export function GlassCard({
  children,
  className,
  hover = true,
  as: Tag = 'div',
  style,
}: GlassCardProps) {
  const prefersReduced = useReducedMotion()

  return (
    <Tag
      className={cn(
        'ap-glass-card',
        hover && !prefersReduced && 'ap-glass-card-hover',
        className
      )}
      style={style}
    >
      {children}
    </Tag>
  )
}

