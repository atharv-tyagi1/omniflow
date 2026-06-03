# OmniFlow V2 Liquid Glass Design System

## Brand
OmniFlow is an AI-native customer operations platform. The design should feel ultra-premium, modern, and alive inspired by Apple iOS 26 Liquid Glass aesthetic combined with the clean precision of Vercel, Linear, and Stripe dashboards.

## Design Philosophy: Liquid Glass
Liquid Glass combines the optical qualities of real-world glass with system fluidity:
- Frosted Glass Panels: All cards, sidebars, modals use backdrop-filter blur 40px saturate 180% with semi-transparent white backgrounds rgba(255,255,255,0.72)
- Dynamic Refraction: Subtle gradient overlays that shift based on position, giving the illusion of light bending through glass
- Soft Depth Layering: Multiple layers of translucent surfaces stacked with subtle shadows 0 8px 32px rgba(0,0,0,0.06)
- Morphing Borders: Borders use rgba(255,255,255,0.5) with 1px width, creating a frosted edge effect
- Ambient Color Bleed: Background gradient blobs soft purple, blue, pink that subtly bleed through the glass panels
- Smooth Transitions: All interactive elements have 300ms cubic-bezier transitions

## Color Palette Light Theme
- Background: Soft warm white gradient F8F9FC to EEF0F6 with ambient color blobs
- Surface Glass: rgba(255,255,255,0.72) with backdrop blur
- Surface Elevated Glass: rgba(255,255,255,0.85) with stronger blur
- Primary: Indigo 6366F1 for buttons, active states, chart accents
- Secondary: Violet 8B5CF6 for AI indicators, secondary actions
- Success: Emerald 10B981 for positive metrics, resolved states
- Info: Sky Blue 0EA5E9 for informational and links
- Warning: Amber F59E0B for caution states
- Error: Rose EF4444 for negative states
- Text Primary: 0F172A slate-900
- Text Secondary: 64748B slate-500
- Text Muted: 94A3B8 slate-400

## Layout
- Fixed left sidebar 260px with frosted glass background, logo at top, grouped navigation with icons
- Top header bar with glass effect, search with shortcut, notifications, user avatar
- Main content area with generous padding 32px, max-width 1440px centered
- Card grid system using CSS Grid with 24px gaps
- All cards have rounded corners 16px, glass background, and soft shadow

## Typography
- Font: Inter all weights from 400 to 800
- Display Hero: 36-48px, font-weight 800, letter-spacing -0.02em
- Headings: 18-24px, font-weight 700
- Body: 14-15px, font-weight 400
- Labels Captions: 12px, font-weight 500, uppercase tracking 0.05em

## Interactive Elements
- Skeleton Loaders: Pulsating gradient shimmer effect with animation
- Tooltips: Glass-styled tooltip with backdrop blur, subtle shadow, 200ms fade-in
- Hover Effects: Cards lift 4px with shadow expansion on hover using transform and box-shadow transition
- Micro-animations: Staggered fade-in for card grids, number counting animation for KPIs
- Active States: Primary color glow ring 0 0 0 3px rgba(99,102,241,0.2)

## Components
- KPI Cards: Glass panel with icon in colored circle, large bold number, trend arrow with percentage, mini sparkline SVG
- Charts: Clean line and bar charts with glass card containers, subtle grid, gradient fills under lines
- Data Tables: Glass rows with hover highlight, status pill badges, avatar and name columns
- Navigation Items: Icon and label, active state has indigo background pill with subtle glow
- Search Bar: Wide glass input with icon prefix, keyboard shortcut badge
- Buttons: Primary filled indigo, Secondary glass translucent, Ghost text-only
- Status Badges: Pill-shaped with tinted glass backgrounds matching status colors
