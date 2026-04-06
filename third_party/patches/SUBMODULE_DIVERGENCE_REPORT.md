# Nested Repository Divergence Report

## Discovery

- Superproject `.gitmodules`: not present.
- `git submodule status --recursive`: empty.
- `tools/AgentKVM2USB` and `tools/AgentWebCam` are nested git repositories, not
  registered submodules.

## AgentKVM2USB

- Repository path: `tools/AgentKVM2USB`
- Upstream URL: `https://github.com/SemperSupra/AgentKVM2USB`
- Upstream base ref: `origin/main`
- Upstream base commit: `ccd55f7`
- Local ref: `HEAD` on `main`
- Local commit: `9fa9a69`
- Local branch state: behind `origin/main` by 6 commits, plus uncommitted change
  in `test_sdk.py`
- Classification: `Infrastructure`

### Upstream-only commits (`HEAD..origin/main`)

- `ccd55f7` Merge pull request #2 from SemperSupra/refactor/spartan-6-fx3-assumptions-8828302436159790485
- `7fad0e7` Refactor assumptions of Cyclone/ADV7842 to Spartan-6/FX3
- `689791c` Merge pull request #1 from SemperSupra/update-hardware-report-16011522587312263998
- `d626bd5` Update HARDWARE_REPORT.md with verified physical inspection findings
- `18bf138` Finalized Pro GUI: Added Input Grabbing, Clipboard, Performance Mode, and Config Tool integration
- `811ec30` Implement full-featured PySide6 GUI replacement for KvmApp.exe

### Local-only commits (`origin/main..HEAD`)

- none

### Local working-tree diffstat

- `test_sdk.py | 26 +++++++++++++++++---------`
- `1 file changed, 17 insertions(+), 9 deletions(-)`

### Key-file summary

- `test_sdk.py`
  Replaces brittle spies on read-only `cv2.VideoCapture.set` and `hid.device.write`
  methods with test doubles/wrapper-level spying, corrects touch report byte
  offsets, and updates the SRT expectation to match the current action log
  behavior (`Pressed e` rather than `Typed 'test event'`).

### Duplicate scan

- GitHub issue list for `SemperSupra/AgentKVM2USB`: no existing issues returned.
- Search query used: `cv2.VideoCapture read-only hid.device write read-only test_sdk`
- Result: no duplicate found.

### Issue package

- `third_party/patches/AgentKVM2USB/sync-test-sdk-brittle-spies/`

## AgentWebCam

- Repository path: `tools/AgentWebCam`
- Upstream URL: `https://github.com/SemperSupra/AgentWebCam`
- Upstream base ref: `origin/main`
- Upstream base commit: `554537a`
- Local ref: `HEAD` on `main`
- Local commit: `ad02fae`
- Local branch state: behind `origin/main` by 2 commits, no local changes
- Classification: none for local divergence; upstream has product changes

### Upstream-only commits (`HEAD..origin/main`)

- `554537a` Improve GUI responsiveness and startup performance.
- `a5752a2` Enhance GUI with PTZ Joypad, per-device presets, and robust device detection.

### Local-only commits (`origin/main..HEAD`)

- none

### Diffstat (`origin/main..HEAD`)

- `agentwebcam/cli.py | 101 ++--------`
- `agentwebcam/gui.py | 458 -------------------------------------------`
- `agentwebcam/webcam.py | 240 ++++-------------------`
- `pyproject.toml | 4 +-`
- `tests/test_agent_features.py | 62 ------`
- `tests/test_cli.py | 7 -`
- `tests/test_gui.py | 73 -------`
- `tests/test_webcam.py | 4 +-`

### Key-file summary

- `agentwebcam/gui.py`
  Upstream removed the older GUI implementation.
- `agentwebcam/webcam.py`
  Upstream substantially simplified the webcam implementation.
- `agentwebcam/cli.py`
  Upstream reduced and reshaped CLI behavior.

### Status

- No local divergence requiring upstream action.
- Recommended convergence command:
  `git -C tools/AgentWebCam pull --ff-only origin main`

