# Peacock One design system

Neo-Brutalist system adapted from the product UI direction.

## Palette

| Token    | Hex       | Use                                       |
| -------- | --------- | ----------------------------------------- |
| Yellow   | `#ffe17c` | Primary surfaces, header, auth background |
| Charcoal | `#171e19` | Sidebar, dark sections                    |
| Sage     | `#b7c6c2` | Accents, icon boxes, secondary panels     |
| White    | `#ffffff` | Cards, inputs                             |
| Black    | `#000000` | Borders, text, shadows, primary buttons   |

Supporting only: `#272727`, `#f4f4f5`, `#ffbc2e`, `#ff5f57`, `#28c840`, `#febc2e`.

## Typography

- **Headings:** Cabinet Grotesk, extrabold (800), tracking-tighter
- **Body:** Satoshi, medium (500)

Loaded from Fontshare in `app/layout.tsx`.

## Rules

- Borders: **2px solid black** on interactive and card surfaces
- Shadows: hard only — `4px 4px 0 #000`, `8px 8px 0 #000`, `12px 12px 0 #000` (no blur)
- Buttons: max radius `0.75rem` (12px); hover presses with `translate(4px, 4px)` and reduced shadow
- Yellow surfaces use the `bg-dot-pattern` utility (32×32 radial dots at 10% opacity)
- No soft shadows and no decorative gradients (dot pattern excepted)
