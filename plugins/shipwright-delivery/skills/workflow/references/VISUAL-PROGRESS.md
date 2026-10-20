# Screenshot progress reporting

## Tooling
Web: ad-hoc browser automation (for example the `webapp-testing` skill from `example-skills@anthropic-agent-skills`, or a scratch Playwright script with Chromium installed) — scripts stay in a scratch directory, never committed as test suites. Native apps: capture the real app on a simulator, emulator or connected device with native tools (`adb exec-out screencap -p`, `xcrun simctl io booted screenshot`) or the shipwright-devices plugin. A web build of a native app may be a separately labelled preview but never counts as iOS/Android validation. If the required device/SDK is unavailable, report that gap instead of substituting a different capture. Do not claim capture works until verified.

## When to capture
After a meaningful UI milestone, at the end of a batch containing UI changes, on a visual failure, or when the owner asks to see progress. Capture only relevant screens, usually one desktop and one narrow/mobile viewport for responsive work. Not after every tool call. Backend-only work gets textual evidence unless it changes visible behavior.

## Workflow
1. Read the selected task and its visual acceptance criteria. Start or reuse the actual development server/app using the project's commands. Do not assume a port or framework.
2. Navigate the real app to the target state with synthetic data; perform the login/interactions needed before capture.
3. Wait for meaningful UI readiness using an observed locator or app-specific signal; a long-lived realtime connection need not reach network idle. Note loading, empty, error and success states accurately.
4. Save PNGs under `docs/evidence/screenshots/<TASK-ID>/<surface>/` with names identifying route/state and viewport. Files must exist before they are reported.
5. Inspect each captured image. Check readability, clipping, layout and the expected state. Record the difference between captured, visually inspected and functionally verified. A screenshot alone does not prove booking or authorization correctness.
6. Link the screenshots in `docs/evidence/<TASK-ID>.md` with capture time, sanitized route, viewport, state, what changed and known problems. Keep real customer information, credentials and tokens out of captures; use fixtures or mask narrowly and disclose the masking. On a personal device capture only the product's screens and crop status bars.
7. Return the screenshot paths and a short caption to the main conversation, which relays the files or clickable paths and states any display limitation. Never replace missing screenshots with mockups or fabricated links.

## Contact sheets and recordings
A design hand-over includes contact sheets (one image per screen group, captures side by side) so the planner inspects sheets and opens single captures only on doubt. When acceptance criteria describe motion, add a short screen recording (MP4 H.264, 10–20 s, small) next to the stills; stills remain the inspection record. Recordings sent to the owner over chat go as documents, not compressed inline video.

## Completion behavior
If a UI task requires screenshots and capture is unavailable, record the blocker and do not mark that criterion passed. Hand-overs carry screenshot paths back to the main conversation; they are not left buried in tool output.

## Brand fidelity
Compare actual screenshots with selected logo variants, typography, token roles, image crops and the surface brief (docs/DESIGN-WORKFLOW.md). Evidence includes design-source revision, asset IDs and viewport/device. Visual similarity alone is not acceptance; functional and native checks stay.

## Helpers
`scripts/contact_sheet.py <TASK-ID> [--surface <name>]` (plugin `scripts/`) builds the labelled contact sheet with ImageMagick or ffmpeg; `scripts/record.sh ios|android|screen <TASK-ID> <name> [seconds]` records a short MP4 into `docs/evidence/screenshots/<TASK-ID>/`. Both are local-only and never upload.
