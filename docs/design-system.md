# Peacock One design system

Premium operating-system interface for Digital Peacock.

## Identity

- Deep navy / near-black surfaces (`#0b1220`, `#121b2f`)
- Accents: peacock blue, teal, turquoise, restrained violet
- Soft shadows, subtle gradients, professional rounded cards
- Typography: Manrope (display) + Source Sans 3 (body)
- Dark mode default, light mode supported via `next-themes`

## Shell

- Collapsible sidebar with permission-filtered navigation
- Top bar: org switcher, global search, quick create, approvals, notifications, help, profile
- Command palette (`⌘/Ctrl + K`)
- Mobile drawer, breadcrumbs, help/shortcuts modal

## Accessibility

- Semantic landmarks and labels
- Visible focus rings
- Keyboard-accessible menus/dialogs (Radix)
- `prefers-reduced-motion` honored globally
- Chart cards include textual summaries for non-visual interpretation

## Components

Reusable building blocks live under `components/ui` and `components/shared`, including page headers, metric cards, data tables, filters, drawers, dialogs, timelines, panels, and chart cards.
