---
version: 1
slug: "web-app-page-tsx"
primary_target: "web/app/page.tsx"
related_targets: ["web/app/audit/page.tsx","web/app/research/[id]/page.tsx"]
---

# Discovery timeline (`/`)

Scope: primary screen of Time Poverty Lab. Mode: **Read** (the judge must understand the discovery loop), inside the pinned Education2025 app shell. Related: `/audit` and `/research/[id]` (Supabase audit trail, same shell).

Audience and job: hackathon judges watching a narrated 2-minute demo (projected or recorded); secondary, public-URL visitors. They must see that agents examine evidence, find uncertainty, choose the next experiment, run it reproducibly and update the decision, and that every card is a real artifact with an ID.

Content: only artifacts read at render time (`initial_state.json`, `experiments/EXP-*/spec.json`, `reports/experiments/EXP-*/{result,validation}.json`, `reports/discovery/*/{critiques,hypotheses,candidates,decisions}/*.json`). Stages without artifacts render as honest "awaiting" placeholders naming the producer and path. Never hard-code EXP-002 or any number.

Modes: REPLAY = committed snapshot bundle (`web/data/discovery-snapshot.json`, git-tracked artifacts only), works on Vercel; timed playback follows the storyboard, arrow keys step. LIVE = local server reads the repo files and refreshes every 3 s; new artifacts flash in. Live without repo falls back to replay with a notice.

Composition chosen by the user (structured question, code-led because Gemini image quota was 0 and no OpenAI key): "Espina + inspector".

## Direction contract

THESIS: The discovery loop is a course of study the lab completes in public: a vertical spine of nine numbered stages, each a real artifact, with the uncertainty stage weighted as heavily as the evidence. Refuses the chat transcript and the KPI dashboard.

OWN-WORLD: Education2025, pinned, polished quieter on the user's request (2026-10-03). Wordmark "tiemPO" in Inter Black. Solid #0055FF sidebar, Play button and evidence marks; the thesis banner is a white surface, #E9ECF1 canvas, flat white 16px cards, Inter, pill chips/buttons, ModuleNumber squares, green/gray status checks, no gradients, no shadows at rest. Five artifact types: EVIDENCE solid blue, EXPERIMENT navy #002B85, UNCERTAINTY yellow #FFC83D with ink text, HYPOTHESIS dashed blue outline, DECISION ink #121722. Geist Mono only for hashes and paths.

STORY: The judge reads the question, sees EXP-001 run on analytic_v1, sees sleep's −48.7 point estimate and the INCONCLUSIVE ranking, watches the critic name what is uncertain, then sees hypotheses, competing candidates, the Director's choice, new evidence and the updated decision appear (or wait honestly).

FIRST VIEWPORT: Blue sidebar (240) with the text-only tiemPO wordmark. Topbar 80: tiemPO wordmark (links to the replay start), ghost ← →, the labelled "Start discovery" pill, stage counter and replay clock; no mode tabs (LIVE only by URL, /?mode=live). White thesis banner with the headline left and the 9-cell stage tracker right. Below, 1fr/320px: the spine starting at stage 1 (question, facts line, H1–H4 list) and the sticky artifact inspector already open on the newest recorded artifact (CRIT-EXP-001-001: path, sha256, agent, model). At 900px height the evidence card sits just below the fold; Play, the arrow keys or ?stage=N bring each stage, the forest plot first, to the centre.

FORM: Vertical spine + inspector, option 1 of 4 in a structured-question round (spine, discovery accordion, presenter stage, type lanes). Locked by the user on 2026-10-03: answer "Espina + inspector (Recommended)". No surface concept-seed was dealt: the brief pinned the vertical flow and the user chose among the four structures directly. An unscoped roll (key b5391451) ran by accident while reading the CLI help and was set aside unused.

SIGNATURE INTERACTION: Replay reveals one stage at a time on the storyboard clock (or →/← keys), the spine segment fills blue up to the active stage, the inspector follows, and the page scrolls the new stage into view. Live mode pulses newly arrived artifacts.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
