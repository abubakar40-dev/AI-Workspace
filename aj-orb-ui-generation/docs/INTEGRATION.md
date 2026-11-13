# E / F. Interaction documentation and AJ integration contract

## E. How each interaction works

| Gesture | Result |
|---|---|
| Hover orb | 140 ms later the radial menu opens (hover mode). Leaving the orb *and* menu closes it after 260 ms. |
| Click a segment | Runs its command (see inventory R3–R10) and closes the menu. |
| Drag file(s)/text over orb | Menu opens in drag mode, centre reads **Release to Select**. |
| Drag over a segment | Segment highlights cyan if the MIME type could be accepted, red if certainly not ("Not accepted"). Names are hidden by the platform until drop. |
| Drop on a segment | `extractDrop` → `validatePayload` (by file name + MIME) → accepted items go to `onSubmit(payload, intent)`; rejected ones produce shake + toast. Folders are rejected. |
| Drop on the orb centre | Same as **Add files** (`add-file`). |
| Drop on the open panel | Same as **Add files**. |
| Double-click orb | Toggles **move mode** (dashed ring + hint). Menu is suppressed. |
| Drag in move mode | Orb follows pointer, clamped to the screen. |
| Release fast | **Throw**: inertia, edge bounce, settles; `onPositionChange` fires on settle. Slow release = place. |
| Double-click again / Esc / context-menu "Stop moving orb" | Leaves move mode. |
| Right-click orb | Context menu (Show progress, Add files…, Paste, Pause/Resume all, Clear finished, Move orb). |
| Row ✕ / ↻ / ⏸ / ▶ | Calls `onCancel` / `onRetry` / `onPause` / `onResume` for that row; button shows a spinner until the host resolves or the status changes. |
| Chat send | `onSendMessage(text)`; if it throws, the error shows inline and the draft is kept. |
| Esc | Priority: leave move mode → close menu → close panel. |

**State rules** (`lib/orbState.ts`, pure): unseen error → `error`; else any queued/uploading or a submit
in flight → `processing`; else any paused → `paused`; else 1.8 s after a completion → `success`; else
`idle`. An error counts as *seen* when the panel is open (and becomes unseen again if the same item fails again).

## F. AJ integration contract

All types are in `src/aj/types.ts`. The component is **fully controlled**: it owns only transient UI state
(menu/panel open, move mode, toasts). It never stores items or messages.

```tsx
<AjOrb
  items={ActivityItem[]}          // REAL records from the AJ inbox/ingest pipeline
  messages={ChatMessage[]}
  assistantBusy={boolean}
  connection={"connected" | "connecting" | "disconnected"}
  connectionLabel?={string}
  capabilities={{ pause, cancel, retry, chat, clipboard }}   // hide/disable what AJ can't do
  callbacks={AjOrbCallbacks}
  initialPosition?={{x, y}}
  size?={104}                     // multiply by display scale factor
/>
```

### State inputs Freebuff must provide
| Input | Source it must come from | Notes |
|---|---|---|
| `items[].id` | stable id per queued/ingested item | unique, constant for the item's life |
| `items[].name`, `mimeType?` | file name / type | used for badge only |
| `items[].sizeBytes` | file size or `null` | `null` → indeterminate bar |
| `items[].transferredBytes` | **real** bytes processed | must be monotonic per attempt; reset to 0 on retry |
| `items[].status` | real pipeline state | `queued` `uploading` `paused` `completed` `error` `cancelled` |
| `items[].errorMessage` | real failure reason | shown for `error` |
| `items[].addedAt` | epoch ms | sorting |
| `messages[]`, `assistantBusy` | AJ conversation layer, if one exists | If AJ has no chat: set `capabilities.chat=false` and omit `onSendMessage` → the input is disabled |
| `connection` | liveness of the AJ backend | `disconnected` greys the orb and raises one warning toast on transition |

### Callbacks Freebuff must connect (all optional except `onSubmit`; may return Promises; throw to show an error toast)
| Callback | Fired when | Backend operation to connect |
|---|---|---|
| `onSubmit(payload, intent)` | files/text dropped, picked, pasted, or typed as a note | Hand the payload to the **existing canonical AJ inbox backend**. `payload.files` (browser) / `payload.uris` (GTK `file://`) / `payload.text`. `intent` is a UI hint: `add-file add-image add-table analyze cleanup add-text paste-clipboard` — *Freebuff decides what each means* (see assumptions R5/R6). `recent` never reaches `onSubmit`. |
| `onCancel(id)` | row ✕ | cancel the in-flight item |
| `onRetry(id)` | row ↻ | re-run a failed/cancelled item; set status back to `queued`, bytes to 0 |
| `onPause(id)` / `onResume(id)` | row ⏸ / ▶ | only needed if `capabilities.pause` |
| `onPauseAll()` / `onResumeAll()` | context menu | same |
| `onClearFinished()` | "Clear finished" | remove completed/cancelled/error rows from the *view* (do not delete data unless AJ intends it) |
| `onSendMessage(text)` / `onRetryMessage(id)` | chat send / retry | append the user message with `delivery`, update to `sent`/`read`/`error` |
| `onPositionChange(pos)` | move/throw settled | persist (e.g. in AJ settings). Not verified path — Freebuff chooses where |
| `onPanelVisibilityChange(open)` | panel toggled | optional (e.g. resize an input shape on Wayland) |

### Events the host must emit *by changing props* (not callbacks)
* progress ticks → update `items[i].transferredBytes` (throttle ≈ 10–20 Hz);
* completion/failure → change `status` (UI raises the toast and ring automatically);
* assistant answers → push `ChatMessage` with `role:"assistant"`.

### What the UI deliberately does not do
No storage paths, no database, no AJ API names, no fake progress, no seeded records. The only fabricated
data lives in `src/demo/` and is labelled as such.

## GTK port notes (Python + GTK3 + Cairo)

* **Keep the same split:** a `view-model` (items/messages/state) pushed by an adapter; widgets emit signals
  that map 1:1 to the callbacks above.
* **Orb:** pre-render `orb.png` with alpha (clip the artwork to a circle offline). Draw with Cairo:
  image + radial gradient halo + 2 px rings (`cairo.arc`). Redraw only on state change; use a single
  `GLib.timeout_add(33, …)` only while *processing* (ring angle) or *moving*. Idle bob can be dropped on the
  HD 620 or driven at ≤ 15 fps.
* **Radial menu:** geometry in `RadialMenu.tsx` (outer R=170, inner R=68, icon radius 119, segment centres
  22.5°+45°·k from 12 o'clock, 1.4° gap). Hit-test by polar coordinates (angle, radius) — no per-segment
  widgets needed. Icons: export the SVG paths in `components/icons.tsx` to `.svg` and load with
  `Rsvg`/`GdkPixbuf` or draw with Cairo paths.
* **Drop:** `Gtk.drag_dest_set(widget, Gtk.DestDefaults.ALL, [Gtk.TargetEntry.new("text/uri-list",0,0), …], Gdk.DragAction.COPY)`;
  use `drag-motion` (enter/hover-open, per-segment preview via `Gdk.drag_status`) and `drag-data-received`
  (`data.get_uris()` → `SubmitPayload.uris`). Classify with the same extension tables as `lib/fileKinds.ts`
  (or Gio content-type). Preview can use `Gtk.drag_get_source_widget`/target atoms only; names arrive at drop.
* **Transparency/shape:** RGBA visual (`screen.get_rgba_visual()`), `set_app_paintable(True)`, and
  `input_shape_combine_region` so clicks pass through the empty parts of the window.
* **Move/throw on Wayland:** see README limitation 2. Options: (a) fullscreen transparent overlay window with
  an input region that tracks the orb + open panels (enables throw exactly like the demo);
  (b) `begin_move_drag(button, x_root, y_root, time)` for plain move with no throw;
  (c) GNOME Shell extension. Decide with a prototype on Ubuntu 26.04/GNOME 50 — **not verified here**.
* **Panel:** a separate `Gtk.Window` (undecorated, RGBA) or a `Gtk.Popover`; frosted blur is not available on
  GNOME for client windows — use a translucent solid fill (`rgba(255,255,255,.82)`) instead of `backdrop-filter`.
* **Never block the main loop:** run ingest in a worker/`GLib.idle_add` bridge and push progress snapshots to
  the view-model at ≤ 20 Hz.
* **Scaling:** every pixel value is CSS px; multiply by `widget.get_scale_factor()` for Cairo surfaces.
