---
target: tiemPO home (research lens)
total_score: 22
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 4
target_identity: "file:/home/RogerZuriaga/Documents/7moSemestre/hack nation/Hack-nation-hackathon/web/app/page.tsx"
target_fingerprint: "sha256:31a8f3e20de91fb3178bb72aebc0cafda739ed20ec57c5675988f5219d9a7b5a"
target_path: /home/RogerZuriaga/Documents/7moSemestre/hack nation/Hack-nation-hackathon/web/app/page.tsx
timestamp: 2026-10-04T06-17-17Z
slug: web-app-page-tsx
closed: true
---
Method: dual-agent (A: design-review sub-agent · B: detector sub-agent). No browser automation in session: A judged from source + server-rendered HTML; no overlay.

## Design Health Score: 22/40 (Acceptable)

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | REPLAY never says it shows committed artifacts (payload.source computed, never rendered) |
| 2 | Match System / Real World | 2 | Dev jargon on screen: reports/discovery/<session>/…, save_hypothesis, commute_5h |
| 3 | User Control and Freedom | 2 | "Start discovery" collapses the overview; only Esc (undisclosed) returns |
| 4 | Consistency and Standards | 2 | Spec and result share the chip "EXP-001" (model.ts:166,175); /audit has a different visual style |
| 5 | Error Prevention | 3 | Green check on "tested" H1/H2 reads as "confirmed" |
| 6 | Recognition Rather Than Recall | 2 | Role legend on another page; H3/H4 defined at stage 1, cited at stage 4 |
| 7 | Flexibility and Efficiency | 2 | ?stage=N and keys exist; no artifact permalink, JSON, commit or export |
| 8 | Aesthetic and Minimalist Design | 3 | Calm and flat, but 5 empty cards fill half the scroll |
| 9 | Error Recovery | 2 | /audit prints the raw DB error |
| 10 | Help and Documentation | 1 | /guide is 6 legend rows and one sentence |

## Design Specificity Verdict
Center specific (9-stage spine, honest awaiting cards naming agent + path, forest plot with true minus, provenance inspector); frame generic (learning-platform shell; largest text is a slogan, not the question or finding). Under the research lens the page is a replayed case study, not an instrument that accelerates the researcher.
Detector: 6 gray-on-color, all false positives (gray-900 on yellow ≈11.6:1; classes paired across conditional branches). Missed by the detector: awaiting markers gray-500 on gray-100 ≈4.0:1; yellow-600 icon on white ≈2.5:1.

## What's Working
1. Honest empty states (primitives.tsx:221-240).
2. Evidence block (stages.tsx:113-172, ForestPlot.tsx): shared axis, signed tabular figures, CR1 caveat, "point estimate" wording.
3. Provenance by default: clickable IDs, inspector with path, SHA-256, producer, model.

## Priority Issues
- [P0] The loop's payoff is off screen and the replay ends on an empty card (12-15 of 40 s on empty stages; slogan headline). Fix: collapse pending stages into a "Next in the loop" band, show critique → hypothesis handoff, end replay on evidence + critique, finding-led headline. Command: shape → distill.
- [P1] Ranking uncertainty is not legible: "2 of 6 paired differences exclude zero" without naming them; sleep − leisure unseen; H1/H2 assessments from result.json not shown; green check overclaims. Command: clarify.
- [P1] Provenance stops before reproduction: no JSON, commit link or reproduce command; critic's 6 sourced statements collapsed into one sentence; duplicate EXP-001 chips. Command: harden.
- [P1] "Audit trail" contradicts the spine: Supabase [DEMO] case with the old 60-weekly-minute question and 5 outcomes incl. care (supabase/seed.sql:9). Command: distill.
- [P1] Screen reader / keyboard: clock announced every second (DiscoveryView.tsx:367-373); whole Inspector aria-live (Inspector.tsx:70); page-wide key capture; h1 → h3; outline-none on forest-plot rows. Command: audit.

## Persona Red Flags
- Alex: Start wipes the overview; cannot scrub; ID chips are buttons (no text selection); no artifact permalinks.
- Sam: clock announced every second; inspector re-read on each stage; no skip link; chip click does not move focus; "Question: Question".
- Dr. Reyes (time-use researcher): no formula, reference categories, weighted N (12.7 M) or unadjusted estimates; no export; "Requires human review" with nothing to act on.
- The judge (projected): science set at 12-13 px; navy vs ink markers merge on a projector; blue-200 active ring faint.

## Minor Observations
- "4 Oct 2026, 02:12 UTC" reads as tomorrow in CDMX.
- /?stage=5 shows "Resume" on a fresh load.
- Forest-plot tooltip is whitespace-nowrap (~90 chars).
- "Selected experiment" labeled Decision.

## Questions to Consider
1. If stages 5-9 are still empty on judging day, should the spine show 4 stages plus one live "next" slot?
2. Why is the largest text a slogan rather than "Sleep −48.7 min [−63.5, −33.9]"?
3. Who is the "human" in "Requires human review", and why is there no button?
4. Is the home page a case study or a lab?
5. Does the learning-platform shell signal "course progress" instead of "rigor"?
