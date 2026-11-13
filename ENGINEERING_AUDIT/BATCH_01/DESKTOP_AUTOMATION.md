# Desktop & Browser Automation Audit (Batch 01)

**Status:** Not executed. Master context: Ubuntu 26.04.1/GNOME/Wayland environment (historical), computer automation treated as broken until controlled tests pass. Current session type/AT-SPI/portal/wl-clipboard/computer-use-linux/Dogtail presence **not verified** in this pass.

## Safe test plan (Category A plan; UI interaction requires approval A7)
1. Detect session: `XDG_SESSION_TYPE`, `loginctl`, GNOME/portal services.
2. Verify AT-SPI/portal availability (read-only checks).
3. Screenshot capability in controlled harmless window.
4. Accessibility tree read on known app.
5. Reversible input tests only in a disposable test window (explicit approval).
6. Browser automation isolated from real accounts/forms.

## Risks
Wayland pointer/window restrictions; false positives if success not state-verified; tests can cause side effects if run against real apps.
