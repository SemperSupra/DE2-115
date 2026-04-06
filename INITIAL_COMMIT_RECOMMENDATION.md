# Initial Commit Recommendation

## Recommendation

The initial commit should be a **minimal reproducible source snapshot**, not a
full archive of local investigation material. The goal of the first commit is to
capture:

- the board-specific source code,
- the firmware source,
- the scripts required to rebuild/program the board,
- the repository documentation that explains the current state,
- the git hygiene files.

Everything else should stay out of the initial commit until there is a specific
reason to version it.

## Minimum Set To Include

### Repository metadata and documentation

- `.gitignore`
- `.gitattributes`
- `README.md`
- `HANDOFF.md`
- `FINDINGS.md`
- `PROJECT_MAP.md`
- `INITIAL_COMMIT_RECOMMENDATION.md`

### Core hardware/software source

- `de2_115_vga_platform.py`
- `de2_115_vga_target.py`
- `isp1761.py`
- `observe_vga.py`

### Firmware source only

- `firmware/src/main.c`
- `firmware/src/font_8x16.c`
- `firmware/src/font.h`

### Build/program automation

- `Dockerfile`
- `docker-compose.yml`
- `run.bat`
- `scripts/`

### Small project-local helpers

- `test_interaction.py`

## Keep Out Of The Initial Commit

### Generated and rebuildable output

- `build/`
- `firmware/src/demo.bin`
- `firmware/src/demo.elf`
- `firmware/src/*.o`
- `firmware/src/*.d`
- `firmware/src/Makefile`

### Local logs and capture artifacts

- `local_artifacts/`
- `*.log`

### Vendor/reference bulk

- `Downloads/`
- `DE2_115_demonstrations/`

Rationale:

- these trees are large,
- they mix useful reference with a lot of generated/vendor output,
- and they can be added later in a deliberate second commit if you decide to
  vendor them.

### External nested repositories

- `tools/AgentKVM2USB/`
- `tools/AgentWebCam/`

Rationale:

- they are independent git repositories with their own upstreams,
- they should not be silently absorbed into the initial history of this
  superproject,
- and if you want them versioned here later, they should be brought in
  intentionally as submodules, subtree imports, or pinned vendor snapshots.

## Optional Second Commit

If you want a second commit soon after the initial one, a good follow-up would
be one of:

1. Add a curated `third_party/` snapshot containing only the reference files
   actually required for USB LCP extraction.
2. Add `tools/` intentionally with a documented vendoring strategy.
3. Add selected `DE2_115_demonstrations/` source files only, excluding generated
   Quartus/Nios/IDE output.

## Practical Staging Set

If you want a practical first staging pass, start with:

`git add .gitignore .gitattributes README.md HANDOFF.md FINDINGS.md PROJECT_MAP.md INITIAL_COMMIT_RECOMMENDATION.md de2_115_vga_platform.py de2_115_vga_target.py isp1761.py observe_vga.py Dockerfile docker-compose.yml run.bat scripts firmware/src/main.c firmware/src/font_8x16.c firmware/src/font.h test_interaction.py`

## Why This Is The Right Minimum

This set is enough for another engineer to:

- understand the project,
- inspect the current hardware/software design,
- rebuild the firmware and SoC flow,
- and continue the USB bring-up work,

without contaminating the initial history with generated files, local captures,
or third-party repos that should be managed separately.
