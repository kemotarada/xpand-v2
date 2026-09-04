# STC Bank Visual Director — CHANGELOG & Regression Guard

Purpose: keep every improvement locked in. The recurring problem — "the old behavior comes back after an update" — happens when edits drop rules or when two prompt files drift apart. These rules prevent that.

## How to update WITHOUT losing gains (read before any edit)

1. CANONICAL FILE = `SKILL.md`. It is the single source of truth. `../../stc_bank_system_prompt.md` mirrors only the LOCKED INVARIANTS + v3 header and must never contradict SKILL.md.
2. NEVER delete or soften a rule in the "LOCKED INVARIANTS" block of SKILL.md. To change behavior, ADD a rule alongside; if a locked rule must truly change, bump the MAJOR version and record it here with the reason.
3. Every edit bumps the VERSION line at the top of SKILL.md (and the mirror header) and adds an entry below. No silent edits.
4. After editing, run the Consistency check (bottom of this file). If SKILL.md and the system prompt disagree, fix the system prompt to match SKILL.md.
5. Reference files (`references/*.md`) are loaded BY SKILL.md. Adding a new reference file requires adding a pointer to it in SKILL.md's Rule Hierarchy, or it will be ignored.
6. Do not create a third prompt file for STC visuals. One canonical + one mirror only.

## Version history

### v3.0 — 2026-09-04
Added, in response to real production gaps:
- LOCKED INVARIANTS block (12 laws) + regression guard, in both SKILL.md and the system prompt.
- ANTI-REPETITION engine + `references/scene-library.md`: banned crutch scenes (office desk, phone-on-table), a wide location library with forced family rotation, and the Phone-in-Hand hero framework.
- REAL-APP LAW: a visible app screen must be the real STC Bank app (supplied screenshot, preserved) — corrected the old "keep the screen blank" guidance that conflicted with STC's real app-driven ads.
- `references/stc-ad-dna.md`: STC's real ad families distilled (camera + theme + light + finish + effect + color ratio) so XPAND can hit the reference level, plus a Do-not-recreate list so it never clones STC's page.
- `references/effects-and-finish.md`: blur / bokeh / DOF / atmosphere / bloom / motion used only with purpose and only when optically real (luxury, not decoration).
- RESEARCH → LEARN → COMPARE-BACK loop: after locking an idea, compare the draft to the matched STC family and fix gaps before writing the prompt.
- Output contract now names the matched STC reference family and the effect used (or "none").

### v2.x — prior (baseline in this repo)
- Realism-first color system, scene-tier gate, subject-protection law, hard-rejection gate, text-free rule, exact hex palette, camera vocabulary, final audit.

## Consistency check (run after every edit)

- [ ] SKILL.md VERSION line bumped and CHANGELOG entry added.
- [ ] system prompt header VERSION matches SKILL.md; its LOCKED INVARIANTS match SKILL.md's.
- [ ] No LOCKED INVARIANT was deleted or weakened.
- [ ] Every reference file is pointed to from SKILL.md.
- [ ] Real-App Law, Anti-Repetition Law, and Do-not-recreate list are present in SKILL.md.
- [ ] Only two STC-visual prompt files exist (SKILL.md canonical + system prompt mirror).
