# Khatakshetra Book Factory — Foundation PR7

PR7 preserves the complete PR6 execution record and adds an eight-page, hash-bound Visual Gold Standard extracted from the two registered reference PDFs; evidence-classified diagnosis of the PR6 quality gap; actual-pixel comparison of all eight PR6 attempts; reference-first prompt, cultural-authenticity, source-iconography, production-unit, lettering, and comparative-review contracts; and exactly four immutable, non-executable DM04 recovery requests. No image generation, paid call, manuscript rewrite, PDF assembly, DM08 production, source-graph change, publication, or deployment occurred. See `docs/BOOK_FACTORY_FOUNDATION_PR7.md` for the execution report.

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
./factory image-capabilities
./factory visual-gold-standard --require-source-assets
./factory prepare-proof-recovery --book-id DM04
./factory prepare-proof-generation --book-id DM04 --proof-id PROOF_ID
./factory import-proof-image --book-id DM04 --request REQUEST --image PNG --provider-receipt RECEIPT
./factory prepare-visual-review --book-id DM04 --proof-id PROOF_ID
./factory import-visual-review --book-id DM04 --handoff HANDOFF --response RESPONSE
./factory build-proof-contact-sheet --book-id DM04
./factory prepare-style-approval --book-id DM04
./factory produce-next --dry-run
./factory resume --book-id ID
```

`python3 -m book_factory ...` is equivalent. Installing the local package exposes the `factory` console script declared in `pyproject.toml`. `./factory validate` runs schema/config checks and the existing graph validator; `./factory next` is an alias for dry-run selection.

The synthetic command path is explicit and never changes the authoritative catalogue:

```sh
./factory --catalogue book-factory/fixtures/synthetic-book/catalogue.json produce-next --dry-run
```

All commands are repository-local and make no paid provider calls. `produce-next` still requires `--dry-run`. `source-dossier` writes only with explicit `--write`; otherwise it and `story-packet` are read-only. The handoff commands prepare and import exact JSON files; the repository does not pretend that it can spawn a Codex agent programmatically. The current Codex session performs that orchestration and records a session-scoped, non-cryptographic execution attestation.

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
- Offline unit tests, existing graph tests, dependency-free baseline Node tests, source-path/binary boundary checks, and GitHub Actions CI.

## Scaffolded or still blocked

- Direct programmatic manuscript-generation and editorial-review provider adapters. PR4 uses the verified Codex session handoff instead.
- A reusable credential-backed image service. PR6's real Codex-native adapter is host-injected and session-scoped; a plain repository process fails closed without that executor.
- Editable SVG lettering, PDF assembly, font embedding, or final composed-page inspection. PR7 specifies exact geometry but does not typeset a page.
- Automatic visual acceptance. PR7 validates comparison records deterministically, but aesthetics, complex iconography, and cultural meaning still require an independent image-capable reviewer.
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

Approval records bind a decision to the exact subject hash, scope, approver identity, evidence, conditions, and invalidators. Artifact creators cannot issue their own independent approval. Routine page repair stays inside its retry/QA loop and needs no user approval. New style families, unresolved theology, significant iconography deviations, budget overruns, and repeated failures require an explicit persisted decision.

Reusable approvals must opt into inheritance, keep the identical approved hash, target a descendant scope, retain the same source scope/tradition/edition/evidence hash, remain unexpired, and have no changed invalidator. Source-readiness, manuscript, page-composition, book-specific theological exceptions, and manuscript source disputes are never inheritable.

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
- PR7 recovery requests are prepared but not authorized. A future PR8 requires an explicit campaign decision, fresh backend capability evidence, exact reference-input receipts, and a fresh price/spend decision.
- No human-approved exact character reference exists for the DM04 subjects; role C is deliberately recorded as unavailable rather than filled with a rejected proof.
- No licensed pinned font family or approved Git LFS quota/storage policy exists.
- Human theological/iconographic reviewer identities are not configured.

## Architecture adjustments

The user-specified lifecycle replaces the audit document's more granular proposed state names for this implementation. `READY_FOR_PUBLICATION` is deliberately defined as artifact readiness only and is equivalent in safety boundary to the plan's `FINAL_PDF_READY`; there is still no `PUBLISHED` state.

The requested six-specialist model combines lettering/PDF responsibilities with independent QA in one machine-readable contract, rather than the seven workers pictured in the audit. Independence is still enforced by approver/creator identity and immutable reviewed artifacts.

The plan mentioned a deterministic fixture image provider. To honor the stricter instruction not to simulate provider success, the foundation ships only its unavailable capability contract. A test-only implementation can be added when a later milestone explicitly needs provider-flow testing.

No Git LFS patterns are added because quota/billing authorization is still unknown. CI instead blocks oversized normal-Git binaries under `books/`.

The foundation groups closely related control-plane logic into focused modules rather than adding empty stage-specific placeholders. PR2 adds stage modules only for source intelligence, narrative validation, editorial QA, and bibles because those contracts are now executable.
