"""Shared Tailwind class strings for FastUI pages (Architectural Monolith — DESIGN.md).

Requires ``tailwind.config`` in :mod:`app.fastui_html` (``fruger`` palette + ``font-display``).
"""

# --- Navbar ---
NAVBAR = "flex flex-row items-center justify-between px-4 sm:px-6 lg:px-8 h-14 w-full bg-fruger-panel text-fruger-on shadow-sm border-b border-fruger-container"

# --- Layout (full viewport width; horizontal padding only) ---
PAGE = (
    "min-h-screen w-full max-w-none bg-fruger-surface px-4 sm:px-6 lg:px-8 py-8 pb-24 space-y-4 "
    "text-fruger-on antialiased"
)
PAGE_NARROW = (
    "min-h-screen w-full max-w-none bg-fruger-surface px-4 sm:px-6 lg:px-8 py-8 pb-24 space-y-3 "
    "text-fruger-on antialiased"
)
PAGE_DRIVER = (
    "driver-viewport-page flex-1 min-h-0 min-w-0 flex flex-col w-full max-w-none overflow-hidden "
    "bg-fruger-surface text-fruger-on antialiased p-0 gap-0"
)

# --- Footer ---
FOOTER = "mt-16 pt-12 pb-12 border-t border-fruger-container text-xs text-fruger-muted flex items-center justify-center text-center"

# --- Type ---
H1 = "font-display text-4xl font-extrabold tracking-tight text-fruger-on"
H2 = "font-display text-2xl font-bold text-fruger-on mt-6 mb-2"
BODY = "text-fruger-muted leading-relaxed"
LINK = "text-fruger-accent font-semibold hover:underline"

# --- Surfaces (no 1px “template” borders; tonal lift) ---
CARD = (
    "block rounded-md bg-fruger-panel p-8 transition-colors hover:bg-fruger-container"
)
HERO = "rounded-md bg-gradient-to-br from-fruger to-fruger-dark text-white p-8 mb-6"
STAT_TILE = "rounded-md bg-fruger-panel p-6 shadow-fruger-float"
TABLE_WRAP = (
    "rounded-xl bg-fruger-panel shadow-fruger-float overflow-hidden "
    "border border-fruger-container p-4 sm:p-5"
)
DATA_TABLE = "w-full text-sm fruger-data-table font-variant-numeric tabular-nums"
TABLE_SECTION_TITLE = (
    "font-display text-lg font-bold text-fruger-on mt-8 mb-4 tracking-tight"
)
BREAKDOWN_HEADING = (
    "font-display text-2xl font-bold text-fruger-on mt-12 mb-6 tracking-tight"
)
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
CHART_CARD = (
    "rounded-xl bg-fruger-panel p-3 sm:p-5 shadow-fruger-float "
    "border border-fruger-container overflow-hidden"
)
CHART_GALLERY = "grid grid-cols-1 xl:grid-cols-2 gap-6 w-full max-w-7xl mx-auto"
CHART_CAPTION = "text-xs text-fruger-muted mt-3 text-center font-medium tracking-wide"

# --- Driver hub ---
# Match rider embeds: a real min-height so the hub stays visible if a parent in the flex
# chain fails to resolve height (flex-1 + min-h-0 alone can collapse to 0px).
IFRAME_DRIVER = (
    # Make the driver iframe fill the remaining viewport height beneath the navbar
    # instead of using fixed min-heights so the content can span the full page.
    # NAVBAR height is h-14 (3.5rem), so subtract that from 100vh.
    "driver-main-iframe flex-1 w-full h-screen max-w-none "
    "border-0 rounded-none shadow-none bg-fruger-surface"
)

# --- Rider hub (FastUI + embed iframes) ---
RIDER_MAIN = "w-full max-w-none space-y-10"
RIDER_SECTION_TITLE = (
    "font-display text-lg font-bold text-fruger-on mb-4 tracking-tight"
)
RIDER_PANEL = (
    "rounded-xl bg-fruger-panel border border-fruger-container shadow-fruger-float "
    "overflow-hidden flex flex-col min-w-0"
)
RIDER_PANEL_HEAD = "px-5 sm:px-6 py-5 border-b border-fruger-container"
RIDER_PANEL_TITLE = "font-display text-lg font-bold text-fruger-on"
RIDER_PANEL_DESC = "text-sm text-fruger-muted mt-1.5 leading-snug"
RIDER_IFRAME_WRAP = "border-t border-fruger-container bg-fruger-surface p-3 sm:p-4"
IFRAME_RIDER = "w-full border-0 flex-1 bg-fruger-surface block rounded-md"

# --- Alerts (soft) ---
WARN_SOFT = "rounded-md bg-amber-50 px-4 py-3 text-amber-950"
ERROR_PANEL = "rounded-md bg-fruger-surfaceLow px-4 py-3 text-fruger-on"
