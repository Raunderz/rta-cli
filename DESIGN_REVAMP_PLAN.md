# Full Design Revamp Plan — Mobile IDE Landing Page

## Status Legend
- [ ] Not started
- [x] Done
- [/] In progress
- [!] Blocked

---

## 1. Hero Section
**Current:** Dark, minimalist, terminal mockup. Corporate and serious.
**New:**
- [x] Light background (soft cream, pale blue, or near-white)
- [x] Illustrated landscape as hero background — peaceful, pixel-art or painted style scenery
- [x] Hero text positioned over/beside the landscape, not in a 2-column grid
- [x] One primary CTA button (large, warm-colored — teal or golden yellow)
- [x] Secondary CTAs below in a lighter style
- [x] Terminal/demo stays as smaller, softer element — floating beside text or at bottom

**Why:** Landscapes = peaceful/welcoming. Dark terminals = serious engineering. Want excitement, not intimidation.

---

## 2. Color Palette
**Current:** Warm grays, golds, muted browns. Premium but cold.
**New:**
- [x] Primary: Teal/cyan (#0D9488, #06B6D4) or forest green (#059669)
- [x] Secondary: Soft yellow or warm cream (#FBBF24 or #FEF3C7) for accents
- [x] Backgrounds: Off-white (#FAFAF8) or very pale blue (#F0F9FF) for light sections
- [x] Text: Dark charcoal (#1F2937) on light, off-white on dark
- [x] Accents: One warm color (yellow/cream) for CTAs and highlights

**Why:** Teal + yellow = indie and peaceful. Warm golds = expensive. We're a tool for makers, not a luxury brand.

---

## 3. Typography
**Current:** Serif italics for headlines (Fraunces). Very design-forward.
**New:**
- [x] Headlines: Clean sans-serif (Inter, System Font, Poppins). Regular weight, not italic.
- [x] Body: Same sans-serif, 16px, 1.6 line height. Generous spacing.
- [x] Monospace: Keep for code snippets, terminal text, labels
- [x] Sizing: Large headlines (36-48px), normal body (16px), small captions (12-14px)

**Why:** Serif + italics = "we designed this carefully." Sans + weight = "approachable and modern."

---

## 4. Navigation/Header
**Current:** Dark bar with logo + nav links. Minimal, clean.
**New:**
- [x] Background: Light cream or white (not dark translucent)
- [x] Logo can have small colored dot or icon next to it
- [x] Nav links in dark text (not gray)
- [x] No glassmorphism — just solid clean header

**Why:** Dark navbars = corporate. Light navbars = welcoming.

---

## 5. Feature Section
**Current:** 3-column grid with 1px borders, minimal text. Stark.
**New:**
- [x] White or soft-colored cards instead of borders
- [x] Small rounded corners (12-16px)
- [x] Subtle shadows (not flat, not heavy)
- [x] Tiny illustrated icon per feature
- [x] Headline + 1-2 sentences per card
- [x] Slight hover lift (shadow increases, slight color shift)
- [x] 3-column desktop, 2 tablet, 1 mobile

**Why:** Cards = more tactile. Icons + shadows + text = easier to scan. Hover animation = feels alive.

---

## 6. Call-to-Action Buttons
**Current:** Monospace, uppercase, bordered, minimal. Tech-bro aesthetic.
**New:**
- [x] Filled button for primary CTA (teal or yellow)
- [x] Outline or ghost style for secondary
- [x] Slightly rounded corners (8px)
- [x] Better padding (more breathing room)
- [x] Hover state: slight shadow, subtle color shift
- [x] No monospace (or only special cases)
- [x] Sentence case, not all-caps

**Why:** Filled buttons = more inviting. Case + padding = more approachable. Hover animations = interactive feedback.

---

## 7. Dashboard/Chat Section
**Current:** Dark mockup showing actual tool interface.
**New:**
- [x] Keep it dark (workspaces should feel focused)
- [x] Softer borders and cards
- [ ] Smaller inset mockup, not full-width
- [ ] Positioned below the fold as "see what's inside"
- [ ] Subtle device frame (MacBook outline) to make it feel real

**Why:** Contrast works — light landing → dark tool. Device frames = more tangible.

---

## 8. Pricing Section
**Current:** 3-column cards, minimal styling.
**New:**
- [x] White cards on light background with subtle borders
- [x] Better spacing between cards
- [x] Highlight "recommended" tier with colored border or badge
- [x] Clear pricing hierarchy — big number, small label
- [x] Feature lists readable, not cramped
- [x] CTA button per card (filled for featured, outline for others)

**Why:** Pricing should feel trustworthy and clear, not minimal and sparse.

---

## 9. Footer
**Current:** Probably dark grid layout.
**New:**
- [x] Background: Light cream or off-white
- [x] Text: Dark
- [x] Links: Colored (teal accent)
- [x] More whitespace between sections

**Why:** Consistency with light, approachable feel.

---

## 10. Illustrations & Visual Elements
**What to add:**
- [x] Hero background: Painted or pixel-art landscape (mountains, trees, clouds)
- [x] Feature icons: Small, friendly, not abstract
- [x] Decorative elements: Subtle shapes, floating clouds or leaves
- [ ] Status indicators: Green dots, checkmarks

**What to remove:**
- [x] Geometric noise texture (too corporate)
- [x] Glassmorphism effects (too trendy, cold)
- [x] Abstract line art (minimize)

**Why:** Illustrations = warmth. Geometry + glass = cold corporate vibes.

---

## 11. Animations & Interactions
**Current:** Probably subtle, minimal motion. Professional but boring.
**New:**
- [x] Cards hover lift (subtle shadow increase)
- [x] Button hover glow or color shift
- [x] Smooth scroll transitions
- [x] Loading states (spinners, progress bars)
- [x] Micro-interactions: links underline on hover, buttons scale slightly on click
- [x] Floating animation on landscape particles

**Why:** Smooth motion = polished. Polished = indie and intentional, not corporate.

---

## 12. Responsive Design
**Current:** Probably fine, but too minimal on mobile.
**New:**
- [x] Mobile-first approach
- [x] Larger touch targets (buttons, links)
- [x] Stacked layouts that feel intentional, not cramped
- [x] Readable text sizes (no 11px fonts on mobile)
- [x] Hero image scales gracefully on small screens

**Why:** Mobile users shouldn't feel like second-class citizens.

---

## 13. Overall Layout
**Change from:** Dark, minimal, grid-heavy, sparse whitespace
**Change to:** Light, spacious, card-based, illustrated, warm-colored accents
- [x] More breathing room (current site feels tight)
- [x] Subtle depth (shadows, rounded corners, colors)

---

## Priority Order (Implementation Phases)

1. [x] **Color palette swap** — biggest immediate impact
2. [x] **Hero section redesign** — add illustration + lighten background
3. [x] **Typography update** — drop serif italics, use hierarchy
4. [x] **Cards + shadows** — feature section, pricing, etc.
5. [x] **Illustrations + icons** — add personality
6. [x] **Buttons + interactions** — polish
7. [x] **Mobile refinement** — ensure everything feels good at small sizes

---

## The Feeling

**Before:** "This is a serious, well-designed product for engineers."
**After:** "This is made by someone who loves coding. I want to try it."

Less premium SaaS, more indie passion project. Less minimal design flex, more peaceful, approachable tool.
