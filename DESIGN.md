# Design System Specification: The Architectural Monolith

## 1. Overview & Creative North Star: "The Architectural Monolith"
This design system is built upon the concept of **Architectural Monolithism**. Inspired by high-end editorial layouts and premium logistics, the system rejects the "template" aesthetic in favor of a bold, authoritative presence. 

The Creative North Star is the intersection of **Visual Silence** and **Surgical Precision**. We achieve this through:
*   **Intentional Asymmetry:** Breaking the traditional grid to create editorial tension. Large headers should often offset from body copy to guide the eye through a narrative rather than a list.
*   **Negative Space as a Component:** Treat whitespace not as "empty" but as a structural element that defines the boundaries of information.
*   **High-Contrast Confidence:** Utilizing a stark #000000 (`primary`) on #f9f9f9 (`surface`) palette to convey absolute clarity.

## 2. Colors & Tonal Architecture
The palette is a study in binary contrast, punctuated by a professional blue for functional intent.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning content. Boundaries must be defined solely through background color shifts or vertical whitespace. 
*   Use `surface_container_low` (#f3f3f4) to define a secondary content area sitting on a `surface` (#f9f9f9) background.
*   The transition of tones is the border.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. 
*   **Level 0 (Base):** `surface` (#f9f9f9).
*   **Level 1 (Nesting):** `surface_container` (#eeeeee) for grouped content.
*   **Level 2 (Interaction):** `surface_container_highest` (#e2e2e2) for active or hovered states.

### The "Glass & Gradient" Rule
To elevate the system beyond flat minimalism:
*   **Glassmorphism:** For floating modals or navigation bars, use `surface_container_lowest` (#ffffff) at 80% opacity with a `24px` backdrop-blur.
*   **Signature Textures:** For Hero CTAs, utilize a subtle linear gradient transitioning from `primary` (#000000) to `primary_container` (#1b1b1b) at a 45-degree angle to add "soul" to the darkness.

## 3. Typography: The Editorial Voice
Typography is the primary driver of this system’s personality. We pair a geometric powerhouse with a neutral workhorse.

*   **Display & Headlines (Plus Jakarta Sans):** These are your "shouting" layers. Use `display-lg` through `headline-sm` to command attention. The tight tracking and bold weights convey confidence.
*   **Body & Labels (Inter):** The "informative" layer. Inter provides a high X-height and neutral tone, ensuring that even at `body-sm` (0.75rem), the system remains hyper-legible.

**Hierarchy Tip:** Always skip a size in the scale when transitioning from header to body (e.g., pair `headline-md` with `body-md`) to ensure the contrast in scale is intentional and "editorial."

## 4. Elevation & Depth
Depth in this system is achieved through **Tonal Layering**, not structural artifice.

*   **The Layering Principle:** To "lift" a card, do not reach for a shadow. Place a `surface_container_lowest` (#ffffff) element on a `surface_container_low` (#f3f3f4) background. This creates a "soft lift" that feels integrated into the architecture.
*   **Ambient Shadows:** When a floating element (like a Tooltip) requires a shadow, use a large blur (32px+) with a 4% opacity of `on_surface` (#1a1c1c). It should feel like a soft glow of light, not a "drop shadow."
*   **The "Ghost Border":** If accessibility requires a container boundary, use `outline_variant` (#cfc4c5) at 20% opacity. Forbid 100% opaque borders; they clutter the visual field.

## 5. Components

### Buttons: The Action Anchors
*   **Primary:** `primary` (#000000) background with `on_primary` (#ffffff) text. Shape: `sm` rounding (0.125rem) for a sharp, "precision-tooled" look.
*   **Secondary (Action):** `secondary` (#0054cb) background. Reserved exclusively for the "final" action in a flow (e.g., "Confirm Order").
*   **States:** On hover, primary buttons should shift to `primary_container` (#1b1b1b).

### Cards & Lists: Editorial Blocks
*   **Card Styling:** No borders. Use `surface_container_lowest` (#ffffff) for the card body.
*   **Spacing:** Use a 32px internal padding to allow the content to "breathe."
*   **The No-Divider Rule:** Forbid horizontal lines between list items. Use a 16px gap (vertical whitespace) or a subtle shift to `surface_container_low` on alternate rows.

### Input Fields: Minimal Precision
*   **Layout:** A bottom-only "Ghost Border" using `outline` (#7e7576) at 40% opacity. 
*   **Focus State:** The bottom border transitions to 2px width using `secondary` (#0054cb).
*   **Typography:** Labels must use `label-md` in `on_surface_variant` (#4c4546) for a muted, professional feel.

### Floating Action Navigation (Additional Component)
Because this system focuses on the "Monolith," use a bottom-center floating navigation bar.
*   **Background:** `primary` (#000000) at 95% opacity.
*   **Blur:** 12px backdrop-blur.
*   **Icons:** 1.5px stroke-based icons in `on_primary` (#ffffff).

## 6. Do's and Don'ts

### Do
*   **Do** use extreme scale. A `display-lg` header next to `body-md` text creates a high-end, bespoke feel.
*   **Do** align elements to a strict 8px spacing grid, but allow "Hero" images to bleed off the edge of the screen to break the "box" feel.
*   **Do** use `secondary` (#0054cb) sparingly. It is a laser, not a paint brush.

### Don't
*   **Don't** use 1px solid black borders. It cheapens the "Monolith" aesthetic.
*   **Don't** use standard "Material Design" shadows. They are too heavy for this crisp environment.
*   **Don't** use rounded corners above `md` (0.375rem). This system is about sharp, geometric confidence; excessive rounding feels too consumer-soft.
*   **Don't** crowd the interface. If you feel you need a divider line, you actually need more whitespace.