# C. Feature inventory

Reference column: **1** = orb image, **2** = radial menu image, **3** = upload/chat image, **U** = user's
written requirements. "Assumption" is stated where a purpose had to be interpreted.

## Orb (image 1 + user behaviour)

| ID | Ref | Component | Purpose | Interaction | Behaviour |
|---|---|---|---|---|---|
| O1 | 1 | Glass sphere + circuit art | Always-visible AJ presence | — | Floats with a 6.5 s ±3.5 px bob (disabled in move mode and with reduced-motion) |
| O2 | 1 | Glow halo | Depth/light | hover | Brighter on hover or while menu is open |
| O3 | 1 | Gloss + rim layers | Glass look | — | Static overlays (screen blend) |
| O4 | U | Hover-to-open | Open radial menu without dragging | pointer enters orb | Opens after 140 ms; closes 260 ms after pointer leaves orb **and** menu |
| O5 | U | Drag-to-open | Accept dropped files | drag payload over orb | Menu opens immediately in *drag mode*; closes 160 ms after the drag leaves |
| O6 | U | Move mode | Reposition anywhere | **double-click** toggles | Dashed rotating ring + hint pill "Drag to move · double-click to finish"; Esc also exits |
| O7 | U | Throw | Fling to a corner | drag then release fast (>320 px/s) | Inertia (exp. friction 3.1/s) + edge bounce (62 % restitution); rAF only runs during the throw; position committed via `onPositionChange` |
| O8 | U | Keyboard move | Accessibility | arrows in move mode (Shift = 48 px) | Nudges orb 12 px |
| O9 | U | Right-click menu | Access progress & utilities | right-click / Menu key / Shift+F10 | See "Context menu" |
| O10 | 1 | State ring: processing | Show work in progress | any item `queued/uploading` or submit in flight | Rotating cyan arc |
| O11 | 1 | State ring: paused | Show paused work | only paused items remain | Static amber ring |
| O12 | 1 | State ring: error | Unseen failure | item became `error` and panel not yet opened | Pulsing red ring; badge "!" ; cleared when the panel is open |
| O13 | 1 | State ring: success | Item finished | item changed to `completed` | One 1.3 s green ripple |
| O14 | 1 | Drag-over ring | Drop feedback | file over orb | Bright cyan ring + scale |
| O15 | 1 | Drag-rejected state | Reject feedback | invalid drop | Red ring + 0.36 s shake + toast |
| O16 | 1 | Attention ring | Hint that drop is possible | file dragged anywhere in window | Pulsing cyan ring |
| O17 | 1 | Count badge | Active count | — | `queued+uploading+paused` count, 99 max; red "!" for unseen errors |
| O18 | 1 | Offline dot + desaturation | Backend not connected | `connection==="disconnected"` | Grey dot top-left, sphere desaturated |
| O19 | 1 | Pressed / focus states | Feedback | mouse down / Tab | Scale 0.96; 3 px white focus outline |

## Radial menu (image 2)

| ID | Ref | Component | Purpose / **Assumption** | Interaction | Behaviour |
|---|---|---|---|---|---|
| R1 | 2 | Dark ring disc (Ø 340) | Container | — | Scale-in 0.22 s |
| R2 | 2 | Centre disc "Release to Select" | Status text | — | Drag mode: "Release to Select"; hovering a valid segment: its drop label (cyan); invalid: "Not accepted" (red). Hover mode: "Select an action" / segment label |
| R3 | 2 | Segment: **Add files** (doc + up-arrow, top-left) | Ingest any file. *Intent `add-file`* | click → file picker; drop | Accepts any file or text. Dropping on the orb centre also uses this intent |
| R4 | 2 | Segment: **Recent activity** (doc + clock, top-right) | *Assumption:* opens history. Intent `recent` | click → opens the activity panel | Command-only; drops rejected |
| R5 | 2 | Segment: **Clean up** (brush) | *Assumption:* "tidy/clean this file" intent. `cleanup` | click → picker; drop | Accepts any file; **meaning must be defined by AJ** |
| R6 | 2 | Segment: **Analyze document** (doc + magnifier) | *Assumption:* analyse/search. `analyze` | click → picker (docs/text); drop | Accepts documents, text files, text |
| R7 | 2 | Segment: **Add text note** (text lines) | *Assumption:* add typed/dropped text. `add-text` | click → note composer; drop text/.txt | Accepts text kind + text drops |
| R8 | 2 | Segment: **Paste clipboard** (clipboard list) | *Assumption:* ingest clipboard. `paste-clipboard` | click | Reads clipboard (image or text); error toast if denied/empty; disabled without capability |
| R9 | 2 | Segment: **Add images** (stacked images) | Images. `add-image` | click → picker `image/*`; drop | Accepts image kind only |
| R10 | 2 | Segment: **Add spreadsheets** (table) | Tables. `add-table` | click → picker; drop | Accepts csv/tsv/xlsx/xls/xlsm/ods |
| R11 | 2 | Segment states | Feedback | hover / press / focus / target / rejected / disabled | white 8–16 % fill / cyan 17 % / red 22 % / 30 % opacity |
| R12 | 2 | Keyboard | Accessibility | Tab to segment, Enter/Space | Activates |

## Activity panel (image 3)

| ID | Ref | Component | Purpose | Interaction | Behaviour |
|---|---|---|---|---|---|
| P1 | 3 | Frosted floating window | Container | right-click → Show progress, or *Recent* segment | Placed beside the orb on the roomier side; hides while orb moves; Esc closes |
| P2 | 3 | "Upload States" card + count chip | Progress list | — | Newest first; scrolls |
| P3 | 3 | File badge (PDF/CSV/PNG…) | File type | — | Red for PDF; colour/label by kind |
| P4 | 3 | File name | Identify | hover → full name tooltip | Ellipsis |
| P5 | 3 | Meta line `X of Y • status` | Real progress text | — | Uses `transferredBytes`/`sizeBytes`; per status: Uploading (spinner), Queued (clock), Paused (amber), Completed (green ✓), Error (red !), Cancelled |
| P6 | 3 | Progress bar | Real progress | — | Determinate from bytes; indeterminate sweep if size unknown; empty on error; lighter when paused |
| P7 | 3 | ✕ Cancel (dark circle) | Cancel | click | `onCancel`; spinner while pending; shown for queued/uploading/paused |
| P8 | 3 | ↻ Retry | Retry | click | `onRetry`; shown for error/cancelled |
| P9 | U | ⏸ / ▶ per row | Pause/resume | click | `onPause`/`onResume`; only if `capabilities.pause` |
| P10 | 3 | Error text | Reason | — | Shows `errorMessage` under the meta |
| P11 | U | Row selection | Focus a file in chat chip | click/Enter | Ring on row; chip updates |
| P12 | U | Clear finished | List hygiene | click | `onClearFinished`; disabled with nothing to clear |
| P13 | U | Empty state | No items | — | Message explaining how to add |
| P14 | U | Panel drop zone | Add by dropping on panel | drag over panel | Dashed outline + "Drop to add" veil; uses intent `add-file` |
| P15 | 3 | Chat header (avatar, name, status) | Identity/connection | — | Subtitle from `connection` or `connectionLabel`; coloured dot |
| P16 | 3 | – Minimize | Collapse chat | click | Chat collapses to header; `aria-expanded` |
| P17 | 3 | ✕ Close | Hide panel | click / Esc | Closes whole panel |
| P18 | 3 | File chip in chat | Context of the file | — | Selected row, else newest completed, else newest |
| P19 | 3 | Assistant / user bubbles | Conversation | — | `**bold**` rendered; auto-scroll |
| P20 | 3 | "Read" label | Delivery status | — | `Sending… / Sent / Read / Not delivered + Retry` from `ChatMessage.delivery` |
| P21 | 3 | Typing dots | Assistant busy | `assistantBusy` | 3 bouncing dots |
| P22 | 3 | "Ask a question…" input + send | Ask AJ | Enter / click send | `onSendMessage`; spinner; inline error if it throws; disabled if no chat capability |
| P23 | 3 | Status orb (top-right) | Live aggregate status | — (`role=status`) | Ring colour for working / paused / error / done |
| P24 | U | Narrow layout tabs | Small windows (<760 px) | tabs *Uploads / Ask* | Single column |
| P25 | U | Empty chat message | No messages | — | Hint text |

## Context menu & notifications

| ID | Component | Behaviour |
|---|---|---|
| C1 | Show/Hide progress | Toggles panel; hint shows active count |
| C2 | Add files… | Native picker, intent `add-file` |
| C3 | Paste from clipboard | As R8 |
| C4 | Pause all / Resume all | Single toggle (Resume when only paused items remain); disabled when not applicable / no capability |
| C5 | Clear finished | As P12 |
| C6 | Move orb / Stop moving | Toggles move mode (hint: Double-click / Esc) |
| C7 | Keyboard | ↑/↓ Enter Esc; closes on outside click, blur, resize |
| T1 | Toasts | Driven by real events only: item completed (success), item failed (error), callback failed (error), connection lost (warning), rejected/skipped drops (warning/error). Auto-dismiss 4–8 s; ✕ to dismiss; `role=alert` for errors |
| N1 | Note composer | Textarea; Ctrl+Enter; inline error on failure; Esc closes |
