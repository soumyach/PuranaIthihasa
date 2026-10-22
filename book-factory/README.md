# Khatakshetra Book Factory — Foundation PR10

PR10 binds the autonomous pipeline to a real, narrowly bounded DM04 production slice: page 1, the Medhas/Suratha/Samadhi dialogue scene, and page 4, the Devi manifestation. It verifies the exact manuscript, page-script, storyboard, character-bible, iconography, and A/B/C/D reference inputs; preserves the exhausted PR6 attempts; and creates a separate, hash-bound production-campaign authorization request.

The current DM04 source-rights clearance permits private manuscript work but explicitly does not authorize illustration or PDF production. Consequently, PR10 stops at `AWAITING_CAMPAIGN_AUTHORIZATION` with zero image operations, zero new art, zero composed pages, zero PDFs, and USD 0.00 spent. This is the intended fail-closed result, not a simulated production success. See `docs/BOOK_FACTORY_FOUNDATION_PR10.md` for the evidence and execution report.

## PR10 real-production integration

1. `prepare-production-slice --book-id DM04` selects and hash-locks exactly two real pages; reruns are idempotent.
2. A `PRODUCTION_CAMPAIGN` approval is book-specific, non-inheritable, and valid only for the exact request and subject hashes. It does not reset or extend PR6's exhausted retry counters.
3. `prepare-production-generation` remains blocked until that exact approval is imported. After approval, it may prepare at most one operation per selected page and two operations for the campaign, under the zero-additional-cost policy.
4. Every generation request must prove which exact A/B/C/D reference inputs the backend received. Missing roles remain explicitly unavailable; rejected proofs are never substituted as approved character references.
5. Real image acceptance requires a reviewer distinct from the producer, actual-pixel and reading-size attestations, and all nine required visual dimensions. Deterministic validation cannot manufacture semantic approval.
6. Composition and PDF assembly remain downstream of those visual gates. No production artifact is emitted while the campaign is unauthorized or a selected page has not passed independent review.
7. Page-local recovery is exercised only through an isolated, publication-ineligible fixture in this milestone.

PR9 adds the durable autonomous Director over the existing PR1-PR8 components. One command selects or resumes a book and advances every repository-executable stage until an exact Codex-specialist, external-provider or human-authorization boundary. Each stage records a stable job ID, hash-bound inputs and outputs, worker identity, execution receipt, attempt, timestamps, cost, PASS/FIX/ESCALATE result and recovery instructions. The queue prefers resumable work, skips blocked titles when another is eligible, respects dependencies, excludes DM08, and never equates private-production eligibility with public-publication clearance.

Repository code does not claim to spawn Codex specialists. It persists an exact handoff and stops honestly when the active Codex runtime, an approved image provider, an independent image-capable reviewer or a human decision is required. Synthetic outcomes are accepted only through the isolated PR9 fixture catalogue and remain publication-ineligible.

PR8 preserves the complete PR7 record and adds a deterministic page-composition, editable-lettering and digital-PDF engine. Ten reusable layout families, exact-text hashes, speaker anchors, aspect-preserving crop records, licensed-font resolution, page-local repair, PDF pixel inspection, production lifecycle gates and an isolated four-page technical fixture are executable through the existing `factory` interface. PR8 generated no story art or manuscript, did not alter DM08 or the source graph, and made no publication or semantic visual-approval claim. See `docs/BOOK_FACTORY_FOUNDATION_PR8.md` for the execution report.

## PR8 page engine

1. Editable `.composition.json` is the page authority; PNG and PDF are deterministic derivatives.
2. Production composition requires `LETTERING`, exact asset approvals and approved manuscript/storyboard/series gates. Successful book composition advances only to `PDF_LAYOUT`; successful PDF export advances only to `VISUAL_QA`.
3. Deterministic PDF inspection cannot advance to publication. Independent actual-pixel review remains required for crop safety, iconography, culture, action, composition, character continuity and reading-size quality.
4. `--fixture-mode` accepts only explicitly synthetic test assets, writes publication-ineligible artifacts and cannot mutate production state.
5. STIXGeneral is the preferred installed serif. Bitstream Vera is the documented operational fallback. No font binary is bundled in this repository, and installation is not represented as blanket publication clearance.
6. The committed four-page fixture and PDF are labeled `KHATAKSHETRA BOOK FACTORY — NON-PRODUCTION RENDERER TEST`.

## PR7 benchmark and recovery workflow

1. `scripts/extract_visual_gold_standard.py` verifies both exact local PDFs and the eight extracted page hashes; `--extract` reproducibly recreates them with Poppler at 72 dpi.
2. `visual-gold-standard --require-source-assets` validates provenance, all A–H reference categories, source-PDF hashes, page hashes, dimensions, and curation fields.
3. The reference package assigns separate roles A (series identity), B (page composition), C (approved character identity), and D (setting). Style/composition never authorize benchmark story-content transfer.
4. Recovery prompts resolve source, iconography, culture, production unit, composition, and exact lettering geometry before one concise scene instruction is built.
5. Comparative review examines actual pixels against exact reference pages across eleven dimensions. Deterministic code verifies bindings and completeness; an independent image-capable reviewer supplies semantic visual judgments.
6. `prepare-proof-recovery --book-id DM04` is idempotent and stores exactly four requests for a separately authorized PR8. It never invokes a provider or resets PR6's exhausted counters.

## PR6 illustration-proof workflow

1. `image-capabilities` records every inspected backend and selects only the zero-direct-cost Codex built-in image tool for this execution session.
2. `prepare-proof-generation` persists an exact request and operation key before any provider call.
3. `import-proof-image` validates the real PNG pixel stream, normalizes without stretching when needed, rejects duplicates, and stores a hash-bound execution receipt.
4. `prepare-visual-review` and `import-visual-review` enforce an actual-pixel review by an identity distinct from the producer.
5. A `FIX` may open one targeted retry carrying the exact prior review hash and findings. Two attempts per proof and eight total are hard ceilings.
6. `build-proof-contact-sheet` embeds the latest real PNG pixels and exact QA metadata. `prepare-style-approval` fails closed unless all four latest images have independent `PASS`.

The PR6 terminal status is `ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED`. It records successful real generation and deterministic validation, not visual approval, source certification, publication rights, print readiness, or release readiness.

## Command interface

From the repository root, use the checked-in launcher:

```sh
./factory status
./factory queue
./factory blocked
./factory approvals
./factory costs
./factory list-books
./factory check-readiness
./factory missing-inputs
./factory source-dossier --book-id ID
./factory story-packet --spine-id SPINE_ID
./factory evaluate-catalogue
./factory prepare-pilot --book-id DM04
./factory draft-manuscript --book-id DM04 --dry-run
./factory review-manuscript --book-id DM04
./factory import-source-clearance --book-id DM04 --record PATH
./factory prepare-manuscript-handoff --book-id DM04
./factory import-manuscript-handoff --book-id DM04 --handoff PATH --response PATH
./factory prepare-review-handoff --book-id DM04
./factory import-review-handoff --book-id DM04 --handoff PATH --response PATH
./factory manuscript-status --book-id DM04
./factory prepare-complete-book-image-campaign --book-id DM02 --usage-observation PATH
./factory import-dm02-visual-proof-authorization --book-id DM02 --authorization PATH
./factory record-dm02-visual-proof-usage --book-id DM02 --phase BEFORE --observation PATH
./factory prepare-dm02-visual-proof-generation --book-id DM02 --panel-id PANEL_ID
./factory import-dm02-visual-proof-image --book-id DM02 --panel-id PANEL_ID --request REQUEST --image PNG --provider-receipt RECEIPT
./factory prepare-dm02-visual-proof-review --book-id DM02 --panel-id PANEL_ID
./factory import-dm02-visual-proof-review --book-id DM02 --panel-id PANEL_ID --request REQUEST --response RESPONSE
./factory build-dm02-visual-proof-contact-sheet --book-id DM02
./factory dm02-visual-proof-status --book-id DM02
./factory image-capabilities
./factory visual-gold-standard --require-source-assets
./factory prepare-proof-recovery --book-id DM04
./factory prepare-proof-generation --book-id DM04 --proof-id PROOF_ID
./factory import-proof-image --book-id DM04 --request REQUEST --image PNG --provider-receipt RECEIPT
./factory prepare-visual-review --book-id DM04 --proof-id PROOF_ID
./factory import-visual-review --book-id DM04 --handoff HANDOFF --response RESPONSE
./factory build-proof-contact-sheet --book-id DM04
./factory prepare-style-approval --book-id DM04
./factory prepare-production-slice --book-id DM04
./factory production-slice-status --book-id DM04
./factory import-production-campaign-approval --book-id DM04 --approval PATH
./factory prepare-production-generation --book-id DM04 --page-id PAGE_ID
./factory compose-page --spec PAGE.json --output-dir OUTPUT
./factory validate-page --source PAGE.composition.json
./factory compose-book --manifest BOOK.json --output-dir OUTPUT
./factory export-pdf --manifest COMPOSED.json --output BOOK.pdf
./factory inspect-pdf --pdf BOOK.pdf --manifest COMPOSED.json
./factory resume-layout --book-id ID --page-id PAGE_ID
./factory produce-next --dry-run
./factory produce-book --book-id ID
./factory resume-book --book-id ID
./factory resume --book-id ID
```

`python3 -m book_factory ...` is equivalent. Installing the local package exposes the `factory` console script declared in `pyproject.toml`. `./factory validate` runs schema/config checks and the existing graph validator; `./factory next` is an alias for dry-run selection. The legacy `resume` command remains available; `resume-book` is the PR9 lifecycle entry point.

The synthetic command path is explicit and never changes the authoritative catalogue:

```sh
./factory --catalogue book-factory/fixtures/synthetic-book/catalogue.json produce-next --dry-run
./factory --catalogue book-factory/fixtures/autonomous-orchestration/catalogue.json produce-next --fixture-mode --fixture-plan book-factory/fixtures/autonomous-orchestration/lifecycle-plan.json
./factory --catalogue book-factory/fixtures/autonomous-orchestration/catalogue.json resume-book --book-id FX-001 --fixture-mode --fixture-plan book-factory/fixtures/autonomous-orchestration/lifecycle-plan.json
./factory compose-book --manifest book-factory/fixtures/page-engine/demo-book.json --output-dir output/page-engine-demo --fixture-mode
./factory export-pdf --manifest output/page-engine-demo/composed-book-manifest.json --output output/pdf/khatakshetra-book-factory-non-production-renderer-test.pdf --fixture-mode
```

All commands are repository-local and make no paid provider calls under the checked-in zero-spend policy. Production `produce-next`, `produce-book` and `resume-book` stop at the first unmet execution boundary and persist its handoff; `--dry-run` selects without mutation. `source-dossier` writes only with explicit `--write`; otherwise it and `story-packet` are read-only. The handoff commands prepare and import exact JSON files; the repository does not pretend that it can spawn a Codex agent programmatically. The active Codex session performs that orchestration and records a session-scoped, non-cryptographic execution attestation.

`prepare-complete-book-image-campaign` derives one visual unit per storyboard panel, binds the immutable preproduction package and a read-only Codex usage observation, proposes the existing two-attempt ceiling without authorizing it, and stops at `AWAITING_CAMPAIGN_AUTHORIZATION`. It never creates an approval or invokes an image provider.

The DM02 visual-proof commands are a stricter execution slice over that preserved campaign. They accept only the four frozen proof-first panel ids, require a separate exact-hash campaign approval plus a four-unit private-illustration clearance, record before/after allowance observations, permit one built-in host operation per panel, reject retries and duplicate outputs, and require independent actual-pixel review. They do not authorize any of the remaining 31 initial images, a PDF, publication, paid providers, or reference promotion.

## PR9 execution and quality boundaries

- Repository-executable: catalogue queueing, graph/readiness checks, exact-text and mechanical QA, content-addressed storage, lettering composition, PDF assembly and deterministic inspection.
- Active Codex orchestration: manuscript, independent editorial/source review, storyboard/bible work and independent image-capable composed-page review.
- External provider: art proofs, illustration and provider-side local edits, always behind capability, approval, attempt and budget gates.
- Human authorization: new visual direction, disputed source/theology/iconography, repeated critical failure, budget overrun and public-publication clearance.
- Composed-page QA separates mechanical checks from semantic and PR7 artistic comparison. Geometry can never emit semantic PASS.
- Page failures route to lettering repair, crop adjustment, local image edit, regeneration, page-PDF re-export or reapproval without resetting counters or regenerating unaffected pages.
- Fixture pages remain PR8 renderer geometry only. They are not approved artistic direction and cannot certify a Khatakshetra publication.

## PR4 private-draft workflow

The Director enforces the following sequence:

1. Store a source-rights clearance bound to the exact dossier, Story Packet, graph, and rules hashes.
2. Open only `PRIVATE_DRAFT_PERMITTED_PUBLICATION_BLOCKED`; do not change source readiness or publication readiness.
3. Prepare a locked manuscript handoff for a `manuscript-story` specialist.
4. Import the structured response, validate every required event and evidence reference, and store immutable JSON, Markdown, coverage, provenance, and execution records.
5. Prepare a review handoff bound to that immutable manuscript hash.
6. Require a different `family-editor` agent, all semantic dimensions, exact hash attestations, and evidence-linked findings.
7. On `FIX`, produce a targeted revision request and preserve the rejected draft; on `PASS`, record editorial completion without opening publication.

The direct `manuscript_generation` and `editorial_review` adapters remain unavailable. This is intentional: the verified equivalent is the explicit Codex session handoff, not an undeclared use of the interactive model.

## Implemented

- Lossless authoritative catalogue import preserving all 78 book IDs, 12 collection codes, original fields, counts, metadata, and exact source hash.
- Explicit graph mapping outcomes for every catalogue entry, including event-scoped bindings for books that share broad story spines.
- DM08 reference-edition registration with immutable PDF/manuscript hashes, automatic-production exclusion, and independent source/publication statuses.
- Retained PR3's evidence-backed pilot ranking and immutable DM04 dossier/Story Packet preparation as the locked input to PR4 manuscript generation.
- Evidence-backed DM04 private-draft clearance that distinguishes the ancient narrative, Pargiter's 1904 translation, modern web presentation, and publication rights.
- Zero-cost Codex manuscript and independent-review handoffs with locked inputs, exact execution receipts, and honest identity-assurance limits.
- Immutable manuscript/review versions, literary Markdown, event coverage, claim provenance, deterministic validation, targeted revision requests, and a separated production-status record.
- Readiness values `READY`, `NEEDS_SOURCE_REVIEW`, `INCOMPLETE_SOURCE`, `BLOCKED`, and `COMPLETED`; selection is by ascending priority then stable book ID, and considers only `READY` entries.
- Read-only access to complete graph spines, ordered events, passages, evidence, related entities/relationships/boons/powers, variants, review flags, and bounded-completeness metadata.
- Invocation of the existing graph validator with a before/after byte-hash guard.
- Hash-addressed source-readiness dossiers that separately assess bounded arcs, chapter extraction, source examination, critical flags, and rights.
- Evidence-grounded Story Packets with ordered events, claims, characters, relationships, conflicts, motivations, powers, citations, variants, and explicit adaptation boundaries.
- Deterministic manuscript validation plus an independent editorial gate that escalates when semantic review is unavailable.
- Separate character and location bible schemas with identity and source-scope controls.
- Replayable append-only events and atomic `state.json` materialization for the requested lifecycle, plus `BLOCKED` and `FAILED` recovery.
- Deterministic book/page/event/job/artifact IDs, immutable content-addressed artifacts, operation idempotency, retry bounds, one-active-book lease, and bounded concurrency configuration.
- Immutable approval records for series, collection, character-family, book-exception, and manuscript-dispute decisions in addition to PR1 approvals. Inheritance also binds source scope, tradition, edition, evidence hash, expiry, and invalidators.
- Provider-neutral language model, image/edit, PDF, and visual-evaluation contracts. Every production capability is unavailable by default with an actionable setup hint.
- Hard budget reservation before provider execution. The checked-in policy permits zero paid spend.
- Deterministic `PASS` / `FIX` / `ESCALATE` reports for source-event coverage, claim provenance, manuscript completeness, character/iconography fields, scene continuity, caption/dialogue duplication, page order, and PDF 3:4 geometry/duplicate render metadata.
- Machine-readable contracts and reusable skills for the Director and six specialist roles.
- Eight real reference pages with exact PDF/page provenance, known-good qualities, known shortcomings, and an offline extraction verifier.
- A reference-first A/B/C/D conditioning architecture that separates visual guidance from prohibited benchmark characters, theology, equipment, and plot.
- Reusable Indian cultural-authenticity and DM04 source-iconography gates, including explicit prohibition of the PR6 Greco-Roman red-crested helmet and unsupported demonic-face flag.
- Distinct `CHARACTER_REFERENCE`, `PANEL_ILLUSTRATION`, and `FULL_PAGE_IMMERSIVE` units plus exact DM04 recovery lettering geometry.
- An independent eleven-dimension comparative review of all eight real PR6 images and a side-by-side evidence artifact.
- Exactly four versioned recovery requests with preserved PR6 parents, locked hashes, a recommended four-operation PR8 cap, and generation authorization set to false.
- A hash-bound two-page DM04 real-production plan, separate production-campaign authorization, exact A/B/C/D reference receipt contract, independent nine-dimension actual-pixel review gate, and isolated page-local recovery fixture.
- Offline unit tests, existing graph tests, dependency-free baseline Node tests, source-path/binary boundary checks, and GitHub Actions CI.

## Scaffolded or still blocked

- Direct programmatic manuscript-generation and editorial-review provider adapters. PR4 uses the verified Codex session handoff instead.
- A reusable credential-backed image service. PR6's real Codex-native adapter is host-injected and session-scoped; a plain repository process fails closed without that executor.
- Production-ready font embedding, print trim/bleed/export profiles and real-book composed-page inspection. PR8 supplies editable composition JSON and digital PDF assembly; PR9 still requires independent actual-pixel review before artifact readiness.
- Automatic visual acceptance. PR7 validates comparison records deterministically, but aesthetics, complex iconography, and cultural meaning still require an independent image-capable reviewer.
- The PR10 DM04 illustration campaign. The exact authorization request is pending because the current private-draft clearance explicitly excludes illustration and PDF production.
- A paid provider credential, pinned external pricing model, or provider-side recovery API. PR6 made no paid call.
- Git LFS enablement, publishing, deployment, PR creation, merging, sales, or email.

## Catalogue and readiness

The exact catalogue v0.1 bytes are retained under `book-factory/inputs/catalogues/`; `books/catalogue.json` is a deterministic, lossless normalization with derived factory decisions kept separate from the original fields. The roadmap labels are preserved but are not treated as verified readiness. Current reconciliation has four exact mappings, 18 subset mappings, and 56 explicit unmapped entries.

Strictly ready books are currently zero because rights clearance and independent review remain unresolved. DM04, DM02, and DM01 are conditional controlled-pilot finalists. That status permits only pre-production source packaging; it never means publication ready, source certified, rights cleared, or editorially approved.

The synthetic catalogue under `book-factory/fixtures/` exists only for tests and is never read by the normal CLI.

## Durable state and resumption

Each real run will live under `books/<book-id>/run/`:

- `events.jsonl` is the append-only authority.
- `state.json` is an atomic materialized view repaired automatically by replay after interruption.
- Every mutating operation requires a durable operation key. Reusing a successful key returns the existing state rather than duplicating events.
- Artifacts live under `books/_artifacts/sha256/<prefix>/` and are never overwritten.

The lifecycle is:

```text
QUEUED -> SOURCE_CHECK -> MANUSCRIPT -> EDITORIAL_QA -> STORYBOARD
-> CHARACTER_BIBLE -> ART_PROOFS -> AWAITING_STYLE_APPROVAL
-> ILLUSTRATION -> LETTERING -> PDF_LAYOUT -> VISUAL_QA
-> READY_FOR_PUBLICATION
```

Any active stage can enter `BLOCKED` or `FAILED` with a reason and exact `resume_stage`. Recovery returns only to that stage, retaining completed stages. `READY_FOR_PUBLICATION` means an independently reviewed repository artifact is ready for a separately authorized publication workflow; it does not publish anything and there is no later publishing transition.

## Approvals

Approval records bind a decision to the exact subject hash, scope, approver identity, evidence, conditions, and invalidators. Artifact creators cannot issue their own independent approval. Routine page repair stays inside its retry/QA loop and needs no user approval. New style families, unresolved theology, significant iconography deviations, budget overruns, repeated failures, and a new real-production campaign require an explicit persisted decision.

Reusable approvals must opt into inheritance, keep the identical approved hash, target a descendant scope, retain the same source scope/tradition/edition/evidence hash, remain unexpired, and have no changed invalidator. Source-readiness, manuscript, page-composition, production-campaign, book-specific theological exceptions, and manuscript source disputes are never inheritable.

## Adding a provider later

Implement `Provider.capabilities()`, `estimate_minor_units()`, and `execute()` for one provider kind. Register it only after credentials, rights, spending authority, retry/recovery behavior, and benchmark evaluation are approved. Capability checks and budget reservation must pass before `execute`; do not log secrets or silently switch providers. Paid calls also require a durable intent/reconciliation ledger in a later milestone.

## Authoritative inputs and blockers

- `MYTHOLOGY_COMIC_RULES.md` is imported unchanged and exact-hash registered.
- Both named visual benchmark PDFs are imported unchanged as presentation-only references; rights remain unresolved.
- The authoritative 78-book catalogue and DM08 Manuscript v2 are registered with their exact hashes.
- DM08 is an `EXISTING_EDITION`, not a newly produced or certified factory output.
- Both reference PDFs remain local, hash-verified, ignored presentation references; no oversized PDF exists in ordinary Git history.
- DM04's source dossier remains `BLOCKED`; a separate private-draft clearance permits only an original editorial adaptation from graph paraphrases and locators.
- DM04 publication remains blocked on target-market legal review, atomically partial source extraction, lack of blanket full-arc source/theological approval, and all visual production.
- The Codex built-in image tool worked for this PR6 session, but no reusable repository credential, quota, or external price is configured.
- All four latest DM04 proofs remain `FIX` after attempt two; the hard retry ceiling is exhausted and style approval is unopened.
- PR7 recovery requests are prepared but not authorized. Any future recovery campaign requires an explicit decision, fresh backend capability evidence, exact reference-input receipts, and a fresh price/spend decision.
- PR10 has prepared that separate request for the exact two-page campaign, but no approval has been imported; status is `AWAITING_CAMPAIGN_AUTHORIZATION` and generation remains disabled.
- No human-approved exact character reference exists for the DM04 subjects; role C is deliberately recorded as unavailable rather than filled with a rejected proof.
- No licensed pinned font family or approved Git LFS quota/storage policy exists.
- Human theological/iconographic reviewer identities are not configured.

## Architecture adjustments

The user-specified lifecycle replaces the audit document's more granular proposed state names for this implementation. `READY_FOR_PUBLICATION` is deliberately defined as artifact readiness only and is equivalent in safety boundary to the plan's `FINAL_PDF_READY`; there is still no `PUBLISHED` state.

The requested six-specialist model combines lettering/PDF responsibilities with independent QA in one machine-readable contract, rather than the seven workers pictured in the audit. Independence is still enforced by approver/creator identity and immutable reviewed artifacts.

The plan mentioned a deterministic fixture image provider. To honor the stricter instruction not to simulate provider success, the foundation ships only its unavailable capability contract. A test-only implementation can be added when a later milestone explicitly needs provider-flow testing.

No Git LFS patterns are added because quota/billing authorization is still unknown. CI instead blocks oversized normal-Git binaries under `books/`.

The foundation groups closely related control-plane logic into focused modules rather than adding empty stage-specific placeholders. PR2 adds stage modules only for source intelligence, narrative validation, editorial QA, and bibles because those contracts are now executable.
