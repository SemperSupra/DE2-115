# [SYNC] AgentKVM2USB: `test_sdk.py` uses brittle spies on read-only device methods and stale output expectations

## Context

- Upstream repository: `SemperSupra/AgentKVM2USB`
- Upstream base tested: `origin/main` at `ccd55f7`
- Local integration context: nested repository under `tools/AgentKVM2USB` inside
  the DE2-115 bring-up workspace
- Local prototype basis: dirty working-tree patch on top of local `HEAD`
  `9fa9a69`
- Test command used for clean-upstream reproduction:
  `pytest tmp_upstream_test_sdk.py -q`
  where `tmp_upstream_test_sdk.py` was materialized from `origin/main:test_sdk.py`

## Problem Statement

Expected:

- `test_sdk.py` should pass on current upstream without requiring live mutation of
  C-extension-backed device methods.
- The tests should verify SDK behavior through stable seams.

Actual:

- 4 tests fail on current upstream:
  - `test_autotune_logic`
  - `test_semantic_typing`
  - `test_normalized_click`
  - `test_session_recording_and_srt`
- Reproduced failure strings include:
  - `AttributeError: 'cv2.VideoCapture' object attribute 'set' is read-only`
  - `AttributeError: 'hid.device' object attribute 'write' is read-only`
  - `assert "Typed 'test event'" in '...Pressed e...'`

Impact:

- The upstream test suite is currently coupled to implementation details that are
  not patchable on common Python/OpenCV/HID bindings.
- This blocks reliable validation of the SDK in downstream integrations and
  obscures behavior regressions behind test-framework brittleness.

## Minimal Reproduction

1. Check out current upstream `main` at `ccd55f7`.
2. Install the repository's test dependencies.
3. Run `pytest test_sdk.py -q`.
4. Observe 4 failures caused by read-only method spying and one stale SRT
   assertion.

## Root-Cause Hypothesis

Supported by the reproduced failures and local patch prototype:

- `pytest-mock` cannot safely spy on `cv2.VideoCapture.set` or `hid.device.write`
  because those are read-only attributes on extension objects in this runtime.
- The tests are asserting transport-level details (`device.write`) rather than
  SDK-level behavior (`_raw_kb` invocation or full report bytes from a test
  double).
- `test_session_recording_and_srt` assumes `type("test event")` leaves
  `last_action_text` as `Typed 'test event'`, but the implementation updates it
  again via `press()` for mapped keys, so the recorded subtitle reflects the last
  key action (`Pressed e` in the observed run).

## Implementation Strategy

Smallest-change approach:

- Fix only the test suite first. Do not change runtime SDK behavior unless the
  maintainers want to preserve the older SRT semantics.

Files/areas likely to change:

- `test_sdk.py`
- Optionally `epiphan_sdk.py` only if upstream wants to stabilize action logging
  semantics for `type()`

Recommended changes:

- Replace spies on `sdk.cap.set` with a mocked capture object assigned to
  `sdk.cap`, exposing `get`, `set`, and `isOpened`.
- Spy on `sdk._raw_kb` instead of `sdk.kb_dev.write`.
- Replace direct spying on `sdk.touch_dev.write` with a mock touch device and
  assert on the captured report payload.
- Update the click-report byte assertions to match the actual emitted packet
  shape.
- Update the SRT assertion to either:
  - assert the currently emitted action text, or
  - change `type()`/recording semantics intentionally and document that behavior.
- Prevent background reader-thread noise in tests by disabling or replacing the
  capture update thread when `sdk.cap` is swapped with a mock.

Tests to add or update:

- Keep the existing test cases but rewrite their fixtures/assertions around test
  doubles.
- Add one regression assertion that `pytest test_sdk.py -q` completes without
  unhandled thread warnings.
- If action-log behavior is intentionally changed, add a targeted unit test for
  `type()` plus recording/SRT interaction.

Risk and compatibility considerations:

- Test-only fix is low risk and should not alter runtime behavior.
- If `epiphan_sdk.py` is changed to preserve `Typed '<text>'` throughout
  recording, that is a product behavior change and should be treated separately
  from the infrastructure fix.

## Acceptance Criteria

- `pytest test_sdk.py -q` passes on current upstream.
- No test depends on spying on read-only C-extension attributes.
- HID and click tests validate stable SDK seams or mock devices instead of raw
  extension objects.
- Session-recording expectation is aligned with documented action-log behavior.
- Test runs do not emit unhandled background-thread warnings after capture mocks
  are introduced.

## Attachments

- Patch package:
  `third_party/patches/AgentKVM2USB/sync-test-sdk-brittle-spies/patches/`
- Diff summary:
  `third_party/patches/AgentKVM2USB/sync-test-sdk-brittle-spies/diffstat.txt`
- Range diff note:
  `third_party/patches/AgentKVM2USB/sync-test-sdk-brittle-spies/range-diff.txt`

