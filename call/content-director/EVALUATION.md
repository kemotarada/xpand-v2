# XPAND creative regression set (v3)

These are fixed evaluation briefs, not pre-generated campaigns or claims of success.
Run through the authenticated campaign endpoint with normal budgets. Do not reset usage,
activate billing, or use production tests to overwrite existing projects. Save the job IDs
and export the full source/process/result JSON for human review.

1. Introduce XPAND to business owners in Hebron in a 20-second vertical motion ad. Original
   typography/graphics only, supplied navy/cyan identity, 2 team-hours/day. No customer
   portfolio, invented results or generic bad-logo/good-logo comparison. CTA: discuss a brief.
2. Explain why coherent visual identity is more than a logo in a 15-second video. No actors,
   no borrowed campaign treatment. Sound must carry a specific part of the idea; include a
   silent-viewing adaptation. No claim of guaranteed trust or sales.
3. Turn XPAND's video-production process into a 30-second story for a business owner who
   cannot explain the offer concisely. One real filming session plus motion is possible;
   equipment/actors are unconfirmed dependencies. Include a feasible motion-only alternative.

## Review protocol

Compare old and new outputs for the SAME brief, asset assumptions, provider availability,
history snapshot and capacity. Review blind if possible. Keep cost, call count and evidence
coverage visible. Do not compare a current-search run to curated-reference mode as equivalent.

| Dimension | Acceptable evidence |
|---|---|
| Research | Read text, honest inspection limits, facts trace to retrieved passages |
| Inference | Each observation yields a concrete picture, story or sound decision |
| Diversity | Three mechanisms differ beyond wording, setting or character |
| Selection | Strength/weakness, logo-swap and feasibility tests; no success forecast |
| Treatment | Coherent world, action, pacing, sound, ending and production alternative |
| Storyboard | Full-duration coverage, evolving beats ≤1s, deliberate held shots |
| Execution | Specific camera/action/sound, timed VO/text, plausible resources and effort |
| Learning | Feedback scope retained; approval is not evidence of commercial performance |

Score each editorial dimension 0 (missing), 1 (generic), 2 (specific), 3 (specific and justified).
No overall automatic 'world-class' label. A longer output alone does not improve a score.

## Automated checks

`npm test` uses isolated PostgreSQL-WASM and mocked providers, never real credentials.
It verifies persistence, owner authentication, lease recovery, caps, immutable older data,
weekly idempotency, capacity, daily agenda, provenance IDs and exact supporting quotes,
storyboard gaps/overlaps/coverage, speech pacing, effort totals and output escaping.
Mocked creative output is explicitly marked TEST and is not a creative quality benchmark.

Existing v2 output has summary scenes only; v3 must pass deterministic storyboard/treatment
gates and store the research insights and direction comparisons. This is a structural
improvement, not proof of greater originality. Live editorial results should be recorded
separately, with limitations and human judgment.

## Production acceptance — 2026-09-19 (Asia/Hebron)

Deployment included commit `bdbf6da`. The owner authorized a temporary daily call cap of
30 (normal 20); task cap remained 10. The live test used the configured Gemini model and
real retrieved reference text, not mocked results. Provider subscriptions/billing were
unchanged. The daily cap was restored to 20 and verified; recorded usage was 27 calls.

- `e0456431-ec93-41e6-8051-e924ee641921`: completed a seven-day mixed work plan;
  saved seven `day_plan` records. Occupied production days received zero extra minutes.
- `d7316a9f-79b0-4582-9796-a44fbcd9e82d`: blocked at the unchanged task cap before
  final quality review. A first timing failure triggered an unnecessarily broad repair.
  The second storyboard covered 20 seconds, but the campaign was NOT marked complete.
- Editorial review found three directions too close to generic logo animation. The
  model's original self-praise was not accepted as evidence of creative quality.

Follow-up: storyboard-only repair now retains the validated treatment instead of paying
for a new package. Regression test forces a timing error and verifies one package,
two storyboards, one review and completion within the existing 10-call cap. Direction
contracts now require distinct narrative mechanisms, a concrete communication problem,
change and on-screen service proof. Quality review requires separate justified criteria;
missing assessments or generic scores cannot silently pass. These gates do not prove
originality. A further live creative run requires owner approval for additional test
budget; this record must not be presented as a successful video acceptance test.
