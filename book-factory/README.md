# Khatakshetra Book Factory — Foundation PR5

PR5 preserves the PR4 manuscript pipeline and adds an authorized DM04 literary-quality revision, separate source-fidelity and literary-experience review gates, versioned character/location bibles, complete storyboard/page scripts, typography controls, and four proof specifications. DM08 remains an existing reference edition and is never regenerated. No image or PDF is generated, and publication remains blocked. See `docs/BOOK_FACTORY_FOUNDATION_PR5.md` for the execution report.

## PR5 visual-preproduction workflow

1. `prepare-manuscript-handoff --pr5-quality-revision` binds the immutable v2 parent and its prior PASS review.
2. `import-manuscript-handoff` stores v3 with event and claim sidecars; v1 and v2 remain unchanged.
3. Prepare and import separate `SOURCE_FIDELITY` and `LITERARY_EXPERIENCE` reviews. Both are mandatory and hash-bound.
4. `prepare-preproduction-handoff` opens only after both review perspectives pass.
5. `import-preproduction-handoff` validates and versions the character bible, location bible, complete storyboard, page scripts, typography specification and four proof specifications.
6. Proof rendering and semantic visual review remain `BLOCKED_PROVIDER`; specification QA never masquerades as image inspection or approval.

The successful PR5 terminal status is `VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED`. It certifies only that the manuscript and preproduction specification gates passed. It does not certify source readiness, publication rights, theological authority, visual quality, print readiness, or release readiness.

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
- Offline unit tests, existing graph tests, dependency-free baseline Node tests, source-path/binary boundary checks, and GitHub Actions CI.

## Scaffolded, not implemented

- Direct programmatic manuscript-generation and editorial-review provider adapters. PR4 uses the verified Codex session handoff instead.
- Illustration generation/editing, including the test fixture execution backend. The fixture provider is only a capability seam and cannot claim success.
- Page composition, editable SVG lettering, PDF assembly, font embedding, rendered-page inspection, or pixel comparison.
- Image-based visual evaluation. Its deterministic result is `ESCALATE` with `VISUAL_BACKEND_NOT_IMPLEMENTED`.
- A real provider, API credential, pricing model, cost reconciliation, or network recovery protocol.
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
- No approved image/LLM/visual-evaluation provider, credential, quota, or price is configured.
- No licensed pinned font family or approved Git LFS quota/storage policy exists.
- Human theological/iconographic reviewer identities are not configured.

## Architecture adjustments

The user-specified lifecycle replaces the audit document's more granular proposed state names for this implementation. `READY_FOR_PUBLICATION` is deliberately defined as artifact readiness only and is equivalent in safety boundary to the plan's `FINAL_PDF_READY`; there is still no `PUBLISHED` state.

The requested six-specialist model combines lettering/PDF responsibilities with independent QA in one machine-readable contract, rather than the seven workers pictured in the audit. Independence is still enforced by approver/creator identity and immutable reviewed artifacts.

The plan mentioned a deterministic fixture image provider. To honor the stricter instruction not to simulate provider success, the foundation ships only its unavailable capability contract. A test-only implementation can be added when a later milestone explicitly needs provider-flow testing.

No Git LFS patterns are added because quota/billing authorization is still unknown. CI instead blocks oversized normal-Git binaries under `books/`.

The foundation groups closely related control-plane logic into focused modules rather than adding empty stage-specific placeholders. PR2 adds stage modules only for source intelligence, narrative validation, editorial QA, and bibles because those contracts are now executable.
