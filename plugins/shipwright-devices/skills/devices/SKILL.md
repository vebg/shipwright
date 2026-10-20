---
name: devices
description: How to drive local iOS simulators and Android emulators/devices with the bundled mobile-mcp tools — list and pick a device, install the simulator agent, read the screen by element references, batch taps and typing, capture screenshots, and the limits (local only, no remote devices without approval). Use when a task needs device interaction or native screenshots.
---
# Driving local devices with mobile-mcp

1. **Pick a device.** Call `mobile_list_available_devices` and pass its `device` id to every later call; there is no implicit current device. Boot simulators/emulators first (`xcrun simctl boot <udid>`, `emulator -avd <name>`; `adb wait-for-device` for Android). Prefer `mobile_launch_app` to open an app and `mobile_open_url` for `http(s)` pages over navigating the UI.
2. **iOS simulator first use.** If taps do nothing, install the on-device agent once: `mobilecli agent install --device <udid>` (it stays installed on that simulator).
3. **Read, then act.** Use `mobile_list_elements_on_screen` to get refs, labels and coordinates; tap by ref so layout differences do not matter; fall back to `mobile_take_screenshot` only for elements missing from the hierarchy or to judge appearance. Group known sequences (tap, type, tap) into `mobile_batch_commands`.
4. **States by route.** Prefer the app's route options (query parameters, preview entries) to reach a state; a capture must not depend on a long tap walk.
5. **Captures.** Save screenshots under the task's `docs/evidence/screenshots/<TASK-ID>/<platform>/` with route/state in the name; inspect each one once; caption it. Native capture alternatives: `adb exec-out screencap -p > file.png`, `xcrun simctl io <udid> screenshot file.png`.
6. **Accessibility.** The element list of a debug build is the framework widget tree. For platform accessibility order/labels use `adb shell uiautomator dump` (Android) while this server is not serving that device, and record the source; spoken screen-reader output cannot be observed — say so.
7. **Limits.** Local devices only; never allocate a remote device unless the user approved it in this conversation, and release it afterwards. The iPhone simulator has no own time zone or airplane mode — run those checks on Android and record it. On a personal phone capture only the product's screens and crop status bars; never change its accounts, time zone or other apps.
