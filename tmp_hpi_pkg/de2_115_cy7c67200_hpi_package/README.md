# DE2-115 CY7C67200 HPI/SCAN/LCP Bring-up Package

This package is intended to be handed to Gemini CLI, Codex CLI, or Google Jules in the existing repository:

`https://github.com/SemperSupra/DE2-115`

It turns the CY7C67200 work into a staged, testable subsystem rather than a monolithic USB experiment.

## Contents

- `PROMPT_FOR_GEMINI_CODEX_JULES.md` — one-shot agent prompt.
- `RESEARCH_FINDINGS_WITH_CITATIONS.md` — research findings with citations to the uploaded Cypress/Infineon material.
- `IMPLEMENTATION_PLAN.md` — work graph, milestones, acceptance gates, and deliverables.
- `overlay/` — complete source files to add to the DE2-115 repo.
- `tools/install_overlay.py` — optional helper that copies `overlay/` into a local checkout.

## Intended use

From a local checkout of `SemperSupra/DE2-115`:

```powershell
python path\to\this_package\tools\install_overlay.py --repo C:\Users\Mark\Projects\DE2-115 --overlay path\to\this_package\overlay
```

Then have an agent wire the new modules into the current build as described in the prompt.

## Guardrails

The current repo has a working Ethernet/Etherbone baseline. The agent must preserve it. Every USB/HPI change must be gated by the existing low-speed Ethernet regression before and after the change.

Do not continue into LCP/SIE/HID work until CY7C67200 HPI readback is proven by:

- nonzero/plausible reads from `0xC004`, `0xC008`, or `0xC00A`, and
- a successful RAM write/read test at `0x1000`.
