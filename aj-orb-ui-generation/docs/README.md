# AJ Orb — UI reference implementation (handoff for Freebuff)

> **What this is:** a React/TypeScript/CSS *visual + interaction reference* for the AJ Orb.
> **What this is NOT:** GTK3/Cairo code, nor a connected backend. The target app is a Python/GTK3/Cairo
> desktop program (Ubuntu 26.04, GNOME 50, Wayland). This code must be **ported**, not shipped.
> It has been **type-checked and built**, but **not run in a real browser or on the target machine**
> (the sandbox lacked browser libraries). Treat interaction timings as starting values to verify.

Files:

| Doc | Content |
|---|---|
| `README.md` (this) | Image analysis, combined architecture, limitations |
| `FEATURE_INVENTORY.md` | Every visible element, its purpose, interaction and behaviour |
| `INTEGRATION.md` | Interaction rules, the AJ integration contract, GTK port notes |
| `VISUAL_CHECKLIST.md` | Checklist to compare against the 3 reference images |

## A. Analysis of the three reference images

### Image 1 — the orb
A perfectly round glass sphere on black. Thin transparent glass rim with bright specular arcs, a soft white
glossy highlight top-left, a luminous cyan-blue circuit board inside (traces, microchip, glowing nodes),
blue light bleeding at the lower rim. No UI chrome, no text. → This is the **floating orb** (idle state).
Reproduced with a generated render of the same subject (`src/assets/orb.jpg`), clipped to a circle, with CSS
layers for glow halo, gloss, rim and state rings. *The artwork is a stand-in: the user's original image
file was not available to the code environment — replace `src/assets/orb.jpg` with the real asset (square,
sphere ≈ 76 % of the frame; `.aj-orb__img` scale 1.31 crops to the rim).*

### Image 2 — the radial menu
A dark (≈ `#1b1d28`) disc on a purple→blue wallpaper. Inside: a darker centre disc (≈ 39 % of outer radius)
with a thin light border and the text **"Release to Select"** (semi-bold, ~75 % white). Eight outlined,
light-grey icons sit on a ring at ≈ 69 % radius, centred on 22.5° + 45°·k. Clockwise from top-right:
document-with-clock, paint-brush, document-with-magnifier, text-lines, clipboard-list, stacked images,
table, document-with-up-arrow. No dividers, no labels, no highlight state shown. → This is the **drop/hover
action wheel** ("Release to Select" = drag mode).

### Image 3 — upload states + assistant chat
Light, frosted lavender/peach UI.
* **Left card "Upload States"**: three white rows. Each: red **PDF** page badge, file name
  (`Google-certificate.pdf`), meta line `60 KB of 120 KB • ⟳ Uploading…`, circular dark **✕** (cancel),
  and a full-width purple progress bar (≈ 50 %). Row 2: `120 KB of 120 KB • ✓ Completed`, full bar.
  Row 3: `60 KB of 120 KB • ! Error`, grey empty bar, **↻** retry icon.
* **Right card "ChatSavvy"** chat window: round avatar, title + subtitle ("Our bot is active instantly"),
  **–** minimize and **✕** close; a file chip (PDF, name, size • ✓ Completed); white assistant bubbles with
  small round avatars; purple user bubbles with "Read" under them; bold inline text in an answer; pill input
  "Ask a question…" with a send arrow.
* A small iridescent purple sphere top-right and a large glass sphere overlapping the chat bottom-left.
→ This is the **progress/activity panel** opened from right-click → *Show progress*.

## B. Combined architecture (how the three images are ONE app)

```
            ┌──────────── Image 1 ────────────┐
            │  floating ORB (always visible)  │
            └───────┬───────────────┬─────────┘
   hover / file drag │               │ right-click → "Show progress"
                     ▼               ▼
        Image 2: RADIAL MENU    Image 3: ACTIVITY PANEL
        (8 actions, drop zone)  (Upload States + Ask AJ chat + status orb)
                     │               ▲
                     └── onSubmit ───┘  items flow back as ActivityItem[]
```

* The orb is the single always-on element; the menu and panel are its two "expanded" states.
* Image 3's large glass sphere **is** the Image 1 orb (not duplicated); its small purple sphere became the
  panel's live **status orb** (reflects idle / working / paused / error / done).
* Orb gestures requested by the user:
  * hover (no drag) → radial menu opens (click an action);
  * drag a file over the orb → same menu opens in *drag mode* ("Release to Select"), drop on a segment;
  * **double-click** → *move mode*: drag and **throw** the orb anywhere (inertia + edge bounce);
  * **right-click** → context menu, including **Show progress** → opens the Image 3 panel.

Source layout:

```
src/aj/                 ← the portable UI (props in, callbacks out; no backend knowledge)
  types.ts              ← INTEGRATION CONTRACT
  AjOrb.tsx             ← root: wires gestures, menus, panel, toasts
  hooks/useOrbMotion.ts ← move + throw physics
  lib/                  ← pure logic (state derivation, drop validation, placement, formatting)
  components/           ← OrbBody, RadialMenu, ContextMenu, ProgressPanel, UploadStatesCard,
                           ChatCard, NoteComposer, Toasts, FileBadge, ItemMeta, icons
src/demo/               ← browser-only demo adapter/harness. REPLACE with the real AJ adapter.
src/index.css           ← all visual styling (class names are `aj-*`)
```

## H. Known limitations (read before porting)

1. **Browser code, not GTK.** Nothing here runs in GTK3/Cairo. See `INTEGRATION.md` §GTK port notes.
2. **Wayland cannot place or fling toplevel windows.** Clients can't set absolute window positions. A
   throwable orb needs either: a layer-shell overlay (not available on GNOME/Mutter), a **fullscreen
   transparent input-shaped overlay window** in which the orb is drawn (what this demo emulates), or a GNOME
   Shell extension. `Gtk.Window.begin_move_drag()` gives drag-to-move but **no throw**. The throw physics
   are in `useOrbMotion.ts` and port 1:1 if the orb is drawn inside a full-screen overlay.
3. **Hover on an unfocused, always-on-top, drop-accepting window on GNOME** needs verification; GTK DnD
   `drag-motion` gives enter/leave while dragging, but hover-open without drag relies on `enter-notify`.
4. **Orb artwork is a generated stand-in**, not the user's original Image 1 file.
5. **Backend is not implemented.** The demo adapter reads real file bytes with a throttled loop; chat can't be
   answered (messages end in the `error` delivery state). No AJ API names are assumed anywhere.
6. **Drag previews** can only reject on MIME type (browsers/GTK hide file names until drop); final
   validation happens on drop and rejects with a shake + toast.
7. **Icon meanings are interpretations** (see inventory column "Assumption"); confirm with the product owner.
8. **Not verified**: real-browser behaviour (no browser available in the build sandbox), GTK, Wayland,
   HiDPI/fractional scaling on the Dell Latitude 5480, or performance on Intel HD 620.
9. Font: "Plus Jakarta Sans" is loaded from Google Fonts with system fallbacks; for an offline desktop app
   bundle a font or use the system font.
