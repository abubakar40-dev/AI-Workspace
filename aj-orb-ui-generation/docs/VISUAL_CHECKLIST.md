# G. Visual verification checklist

Run `npm run dev`, open the app, use the **Demo harness** (bottom-left) to create test files, and compare.

## Image 1 — orb
- [ ] Perfect circle, ~104 px, no black corners from the source image
- [ ] Glass rim visible, soft white highlight top-left, cyan circuit art inside
- [ ] Blue outer glow; slightly stronger on hover
- [ ] Gentle vertical float (none in move mode)
- [ ] Processing: rotating cyan arc · Paused: amber ring · Error: pulsing red ring + red "!" badge ·
      Success: green ripple · Drag-over: bright cyan ring · Rejected: red ring + shake · Move: dashed ring
- [ ] Count badge bottom-right (purple) · offline: grey dot + desaturated sphere
- [ ] Focus ring visible with keyboard (Tab)

## Image 2 — radial menu
- [ ] Dark disc (#1b1d28-ish), outer Ø ≈ 3.3× the orb
- [ ] Centre disc ≈ 40 % of outer radius, thin light border, dims the orb beneath
- [ ] Centre text "Release to Select" (drag) — semi-bold, ~75 % white, centred
- [ ] Eight outline icons, light grey, at ≈ 69 % radius, in this order clockwise from top-right:
      doc+clock, brush, doc+magnifier, text lines, clipboard list, stacked images, table, doc+up-arrow
- [ ] Top-left icon is the upload doc; left-upper = table; left-lower = images; bottom-left = clipboard;
      bottom-right = lines; right-lower = doc search; right-upper = brush; top-right = doc+clock
- [ ] Hover/target/rejected segment fills (white 8 % / cyan / red)
- [ ] Opens on hover without dragging; opens on file drag; closes when leaving

## Image 3 — panel
- [ ] Frosted lavender-white left card titled "Upload States" (≈ 18 px medium)
- [ ] White rows: PDF badge (red tag overlapping a page), name 15 px medium, meta 12 px grey
- [ ] Meta format `60 KB of 120 KB • ⟳ Uploading…` / `• ✓ Completed` / `• ! Error`
- [ ] Dark circular ✕ for uploading rows; ↻ icon for error rows
- [ ] Full-width bar inside each row: deep purple (#4a3a85) on grey (#c9cbd8); empty on error
- [ ] Chat card: avatar, name, subtitle with dot, – and ✕ top right
- [ ] File chip with badge + `size • ✓ Completed`
- [ ] White assistant bubbles with small avatars; purple user bubbles; small grey "Read"/status label
- [ ] Bold inline spans render bold
- [ ] Pill input "Ask a question..." with black send arrow
- [ ] Small iridescent purple status orb at the panel's top-right corner
- [ ] Panel sits beside the orb, never off-screen; narrow window → tabs

## Behaviour
- [ ] Hover opens menu; drag file opens menu; drop PDF on *Add images* → rejected shake + toast
- [ ] Drop PDF on *Analyze document* → row appears, progress advances by real bytes
- [ ] Double-click → dashed ring; drag; fast release throws and bounces; Esc exits
- [ ] Right-click → menu → *Show progress* opens panel; Esc closes
- [ ] Harness "Fail next transfer" → error row, red ring/badge, toast; ↻ retries
- [ ] ⏸ / ▶ / ✕ per row; Pause all / Resume all in the context menu
- [ ] Chat send → message ends in "Not delivered · Retry" (no backend in demo — expected)
