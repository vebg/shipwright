# Shipwright Devices

Bundles the open-source [mobile-mcp](https://github.com/mobile-next/mobile-mcp) server (Apache-2.0, `@mobilenext/mobile-mcp`, pinned to 1.0.11) as a Claude Code plugin so that agents can drive local iOS simulators, Android emulators and USB-connected devices: list devices, launch apps, open URLs, read the on-screen element tree, tap by reference, type, swipe and take screenshots.

In Shipwright this is how the `frontend-designer` captures every UI state on real simulators and how the `manual-tester` verifies native flows; their tool lists reference `mcp__plugin_shipwright-devices_mobile-mcp`.

`package.json` + `package-lock.json` next to `.mcp.json` pin `@mobilenext/mobile-mcp` to 1.0.11 with registry URLs and integrity hashes; nothing else is installed.

## Install
```bash
claude plugin marketplace add vebg/shipwright
claude plugin install shipwright-devices@shipwright
```
Requirements: Node.js with `npx`; Xcode with simulators for iOS; Android SDK platform tools (`adb`) and an emulator or device for Android. On an iOS simulator the first run installs the tool's on-device agent (`mobilecli agent install --device <id>`), which then stays on that simulator.

## Rules the agents follow
- Start with `mobile_list_available_devices`; devices must be booted to appear; pass the chosen id to every call.
- Read the screen with the element list, not screenshots; tap by reference; batch known sequences.
- Local devices only. A remote (cloud) device costs money and is never allocated unless the user explicitly approves it in the prompt; release it when done.
- A debug build's element list is the framework's widget tree, not the platform accessibility tree; for accessibility order and labels use the platform dump (`adb shell uiautomator dump`) while the agent is not serving that device, and name the source in evidence.
- On a personal phone capture only the product's screens, never account choosers, notification shades or other apps; crop status bars.

## What this plugin runs, sends and stores
Claude Code starts `npx -y @mobilenext/mobile-mcp@1.0.11` as a local stdio process at session start; `npx` downloads the pinned package from the npm registry on first use. The server talks to your local simulators/emulators/devices through Apple's and Android's command-line tools. Nothing is sent elsewhere unless a tool call explicitly targets a remote device, which the agents may not do without your approval. The plugin stores nothing itself.

## Licence
Apache License 2.0 for this plugin wrapper; mobile-mcp is Apache-2.0 by Mobile Next.
