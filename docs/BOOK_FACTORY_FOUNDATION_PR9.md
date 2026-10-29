# Khatakshetra Autonomous Book Factory — Foundation PR9

## 1. Branch and local commit

- Branch: `feature/book-factory-autonomous-orchestration-pr9`
- Baseline: PR8 commit `7e844c138b9590da6d47b30a46c27fe18e9a7fae`
- Delivery: one local PR9 commit; the exact commit ID is reported after commit creation.
- No push, pull request, merge, deployment or publication was performed.
- The pre-existing `.DS_Store` modifications were left unstaged and unchanged by PR9.

## 2. Actual autonomous execution capabilities

`factory produce-next`, `factory produce-book --book-id ID` and `factory resume-book --book-id ID` now use one durable Director. The Director selects or resumes work, acquires the one-active-book lease, enforces zero-spend and retry policy, records stable jobs and advances every supported repository stage until it reaches a real execution boundary.

Each stage job records the stable job ID, exact input/output/policy hashes, page ID where applicable, worker identity, receipt, attempt, estimated/actual cost, start/completion timestamps, PASS/FIX/ESCALATE result and recovery instructions. The append-only event stream is authoritative; current job JSON is a repairable materialization. Same-input successful jobs are reused. Changed inputs invalidate the stage and only its downstream dependents.

Repository-executable work includes deterministic selection, readiness inspection, hash/schema/prerequisite checks, content-addressed storage, exact-lettering preservation, composition, PDF assembly, mechanical inspection, cost reporting and recovery routing. `factory status`, `queue`, `blocked`, `approvals` and `costs` expose the control plane without publishing anything.

Readiness remains multidimensional: source readiness, private-production clearance, editorial certification, visual completion, publication clearance and publication-artifact readiness cannot override one another.

## 3. Stages still requiring Codex, external tools or human authority

| Boundary | Stages | PR9 behavior |
|---|---|---|
| Active Codex orchestration | manuscript; independent editorial/source review; storyboard and bibles; independent actual-pixel composed-page review | Persist an exact handoff. Repository code explicitly reports that it cannot programmatically spawn a Codex specialist. |
| External provider | art proofs; production illustration; provider-side image edit | Require capability, campaign approval, exact A/B/C/D reference receipt, budget reservation and remaining attempts. No fallback or call occurred. |
| Human authorization | new series/collection style, unresolved source/theology/iconography, repeated critical failure, budget overrun, public-publication clearance | Persist a scoped approval requirement and stop. Routine lettering repair is autonomous. |

No unavailable stage is represented as completed, and no semantic review is fabricated.

## 4. Queue behavior demonstrated

The deterministic policy is: resumable partial work first, then ascending catalogue priority, then stable book ID. It records a reason for every selected, skipped, blocked, complete or excluded record; preserves catalogue IDs; respects title dependencies and collection approval scope; and separates private-production eligibility from public-publication eligibility.

The isolated acceptance catalogue demonstrates all key branches: `FX-BLOCKED` is skipped, DM08 is excluded as `EXISTING_EDITION`, `FX-001` is selected, and dependency-bound `FX-002` becomes the next candidate only after `FX-001` reaches fixture artifact readiness. In the authoritative 78-book queue, DM04 is a blocked partial run rather than a global stall, while DM08 remains excluded.

## 5. Synthetic dry-run lifecycle results

The explicit non-production fixture traversed all twelve orchestrated stages:

`SOURCE_CHECK → MANUSCRIPT → EDITORIAL_QA → STORYBOARD → CHARACTER_BIBLE → ART_PROOFS → AWAITING_STYLE_APPROVAL → ILLUSTRATION → LETTERING → PDF_LAYOUT → VISUAL_QA → READY_FOR_PUBLICATION`

The first run intentionally interrupted illustration. `resume-book` reused the same stable illustration job at attempt 1, completed the remaining stages, preserved exact lettering, stored every stage output through the fixture content-addressed store and continued the queue to `FX-002`. All receipts declare synthetic fixture execution, zero real provider calls and zero paid cost.

The PDF stage composed and exported the existing PR8 four-page technical renderer fixture. Deterministic inspection passed with four ordered 1086 × 1448 pages and PDF SHA-256 `7b6202b860a45a8c7e5bd151498a3095836e79012dd5183c239edeff7d145417`. Poppler rendering and visual inspection confirmed that all four pages render and retain the prominent non-production labels. These geometric pages are not artistic references and make no semantic or publication claim.

## 6. Page-local recovery behavior

PR9 routes balloon placement and overflow to lettering repair; crop errors to crop adjustment; wrong artwork, character, iconography or cultural treatment to local image edit or regeneration; missing panels to panel regeneration; failed PDF pages to page re-export; interrupted generation to the same job ID; and invalid approvals to reapproval.

Every route keeps the page and panel identity, preserves unaffected pages and every prior version, retains cumulative attempt counters, and invalidates only real dependents. Page 18 repair therefore does not rebuild pages 1–17 or 19 onward unless a shared upstream hash actually changed.

## 7. Visual-quality controls implemented

Composed-page review now has three explicit groups:

1. Mechanical: dimensions, ordering, text, clipping/overflow, tails, source wording, numbering, image hashes and page completeness.
2. Semantic: action, identities/forms, Indian cultural authenticity, narrative emphasis, artwork obstruction, expression, continuity, visual language, prohibited unrelated motifs and cinematic impact.
3. Artistic comparison: exact rendered pixels at actual reading size against role-labeled PR7 Gold Standard pages.

Every non-PASS finding must identify book/page/panel, actual discrepancy, supporting script or visual standard, severity and whether the remedy is lettering, crop, local edit or regeneration. PR8 geometry cannot satisfy the artistic gate.

Reference conditioning validates the exact A/B/C/D paths and hashes actually submitted to the backend. A backend that cannot consume reference images is reported as unsupported; text-only generation cannot be labeled reference-conditioned. Style/composition references do not authorize Vishnu, Narada, Raktabija or other benchmark story content to transfer into a new story.

## 8. Actual semantic-review capability

Deterministic code validates bindings, identity separation, completeness and outcome consistency only. Semantic and artistic PASS requires a named, independent, image-capable reviewer who attests inspection of the exact composed-page pixels at actual reading size. The creator cannot self-review. Missing capability, incomplete dimensions, stale hashes or uncertain independence returns ESCALATE.

The acceptance fixture carries explicit fixture-only outcomes to test the state machine. Those outcomes cannot enter production state and are not evidence that any real Khatakshetra page is artistically approved.

## 9. Test results

- PR9 tests: 20 passed.
- Complete Book Factory Python regressions: 151 passed.
- Complete repository Node regressions: 10 test files passed (293 assertions). `jsdom` was installed only in `/tmp` for validation; no Node dependency or package file was added to the repository.
- `python3 -m book_factory validate`: PASS, including the immutable source-graph hash `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`.
- The tests cover stage prerequisites, deterministic selection, blocked-title skipping, DM08 exclusion, durable resume, independence, scoped hash invalidation, approval inheritance, localized repair, exact lettering, image-capable review requirements, no false artistic PASS, reference receipts, budgets, attempt exhaustion, provider failure, PDF assembly, publication gates, fixture isolation and source-graph immutability.

## 10. DM04 production state and blockers

DM04 remains at `ART_PROOFS`. Its immutable production status is still `ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED`.

The Director reports, without creating art or resetting anything:

- PR6 image-attempt budget exhausted; reset is forbidden.
- PR7 recovery requests are prepared but not authorized.
- Human style approval is unavailable because the latest proofs remain FIX.
- Worldwide/target-market publication rights are not cleared.
- Chapter extraction remains atomically partial.
- Independent full-arc source/theological approval is not established.
- Font license selection and trim/bleed/export profile remain pending.
- Full-book illustration, composed-page review and publication remain outside the completed work.

DM04's source readiness remains BLOCKED even though its private draft and dual-perspective manuscript review exist. DM08 was not regenerated, rewritten, illustrated or otherwise entered into production.

## 11. Remaining engineering gaps

- No repository-native mechanism exists to spawn or authenticate Codex specialists; active-session handoffs retain session-scoped, non-cryptographic identity assurance.
- No reusable authorized image-provider credential, quota, price schedule or campaign approval exists.
- No real production composed-page visual review has been executed.
- No human theological/iconographic reviewer roster or publication-rights clearance is configured.
- Collection/character/location approvals can now be scoped and inherited, but real reusable approvals must still be supplied by authorized owners.
- The queue has no strictly production-ready authoritative title today; it correctly reports blockers instead of manufacturing work.
- Git LFS/storage policy, print trim/bleed/export profiles, publishing, deployment and marketplace release remain unimplemented and unauthorized.

## 12. Recommended PR10 acceptance-test scope

PR10 should run one newly authorized, non-DM08 book through the real orchestration boundary with no fixture PASS substitutions: lock source/private-draft authority; execute and import independent manuscript/editorial handoffs; approve storyboard/bibles and collection style; configure one authorized zero-or-capped-cost image provider that proves A/B/C/D receipt integrity; produce a deliberately small page subset; exercise one page-local failure and recovery; compose the exact pages; perform independent image-capable actual-reading-size comparison against PR7; reconcile costs and attempts; and stop at reviewable publication-artifact readiness without publishing, deploying or producing a full book unless separately authorized.

PR10 acceptance should explicitly prove interrupted external-call recovery, approval expiry/invalidation, queue continuation after a real blocker, and preservation of DM04's exhausted PR6 counters.
