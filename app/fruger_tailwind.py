"""Shared Tailwind class strings for FastUI pages (Architectural Monolith — DESIGN.md).

Requires ``tailwind.config`` in :mod:`app.fastui_html` (``fruger`` palette + ``font-display``).
"""

# --- Navbar ---
NAVBAR = "sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8 h-14 bg-fruger-panel text-fruger-on shadow-sm border-b border-fruger-container"

# --- Layout (full viewport width; horizontal padding only) ---
PAGE = (
    "min-h-screen w-full max-w-none bg-fruger-surface px-4 sm:px-6 lg:px-8 py-8 pb-24 space-y-4 "
    "text-fruger-on antialiased"
)
PAGE_NARROW = (
    "min-h-screen w-full max-w-none bg-fruger-surface px-4 sm:px-6 lg:px-8 py-8 pb-24 space-y-3 "
    "text-fruger-on antialiased"
)

# --- Footer ---
FOOTER = "mt-16 pt-12 pb-12 border-t border-fruger-container text-xs text-fruger-muted flex items-center justify-center text-center"

# --- Type ---
H1 = "font-display text-3xl font-extrabold tracking-tight text-fruger-on"
H2 = "font-display text-lg font-bold text-fruger-on mt-6 mb-2"
BODY = "text-fruger-muted leading-relaxed"
LINK = "text-fruger-accent font-semibold hover:underline"

# --- Surfaces (no 1px “template” borders; tonal lift) ---
CARD = (
    "block rounded-md bg-fruger-panel p-8 transition-colors hover:bg-fruger-container"
)
HERO = "rounded-md bg-gradient-to-br from-fruger to-fruger-dark text-white p-8 mb-6"
STAT_TILE = "rounded-md bg-fruger-panel p-6 shadow-fruger-float"
TABLE_WRAP = "rounded-md bg-fruger-panel shadow-fruger-float overflow-hidden"
EMPTY_STATE = (
    "rounded-md bg-fruger-surfaceLow px-6 py-10 text-center text-sm text-fruger-muted"
)

# --- Controls ---
OUTLINE_BTN = (
    "inline-flex items-center rounded-md bg-fruger-panel px-3 py-2 text-xs font-semibold "
    "text-fruger-on shadow-fruger-float hover:bg-fruger-container transition-colors"
)

# --- Media / embeds ---
IMG = "max-w-full rounded-md shadow-fruger-float"
IFRAME = "w-full rounded-md shadow-fruger-float min-h-[400px]"
IFRAME_TALL = "w-full rounded-md shadow-fruger-float min-h-[480px]"
IFRAME_ACTIONS = "w-full rounded-md shadow-fruger-float min-h-[420px]"

# --- Alerts (soft) ---
WARN_SOFT = "rounded-md bg-amber-50 px-4 py-3 text-amber-950"
ERROR_PANEL = "rounded-md bg-fruger-surfaceLow px-4 py-3 text-fruger-on"
