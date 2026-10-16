# Khatakshetra Book Factory — Foundation PR2

This milestone extends the offline control plane with evidence-grounded source dossiers, Story Packets, narrative contracts, separate character/location bible contracts, independent editorial gates, and scope-safe approvals. It does not generate a manuscript, image, page, PDF, pull request, deployment, or public release. See `docs/BOOK_FACTORY_FOUNDATION_PR2.md` for the complete execution report.

## Command interface

From the repository root, use the checked-in launcher:

```sh
./factory status
./factory list-books
./factory check-readiness
./factory missing-inputs
./factory source-dossier --book-id ID
./factory story-packet --spine-id SPINE_ID
./factory produce-next --dry-run
./factory resume --book-id ID
```

`python3 -m book_factory ...` is equivalent. Installing the local package exposes the `factory` console script declared in `pyproject.toml`. `./factory validate` runs schema/config checks and the existing graph validator; `./factory next` is an alias for dry-run selection.

The synthetic command path is explicit and never changes the authoritative catalogue:

```sh
./factory --catalogue book-factory/fixtures/synthetic-book/catalogue.json produce-next --dry-run
```

All commands are repository-local and make no network or provider calls. `produce-next` still requires `--dry-run`. `source-dossier` writes only with explicit `--write`; otherwise it and `story-packet` are read-only. `resume` reads durable state but never advances an unsupported stage.

## Implemented

- Empty authoritative catalogue plus schema/import support that preserves original book and collection IDs.
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

- Manuscript generation or rewriting.
- Illustration generation/editing, including the test fixture execution backend. The fixture provider is only a capability seam and cannot claim success.
- Page composition, editable SVG lettering, PDF assembly, font embedding, rendered-page inspection, or pixel comparison.
- Image-based visual evaluation. Its deterministic result is `ESCALATE` with `VISUAL_BACKEND_NOT_IMPLEMENTED`.
- A real provider, API credential, pricing model, cost reconciliation, or network recovery protocol.
- Git LFS enablement, publishing, deployment, PR creation, merging, sales, or email.

## Catalogue and readiness

No 78-book production catalogue is present in the audited checkout. Existing story-pack, launch-library, and collection JSON files are useful editorial inputs but are not silently promoted to production manifests. `books/catalogue.json` therefore remains empty. Importers accept only explicit records, retain their IDs and `collection_ids`, reject conflicting redefinitions, and never infer source mappings.

A catalogue value of `READY` is only an eligibility input. Production readiness also requires the source graph validator, the exact authoritative rules hash, source/rights review, and applicable approvals. A graph spine with `status: COMPLETE` means its bounded event sequence is complete; it does not establish exhaustive scripture coverage.

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
- The authoritative 78-book catalogue is absent, so `books/catalogue.json` remains empty.
- DM08 Manuscript v2 is absent and no DM08 production record was created.
- The 122,897,487-byte Enemy benchmark requires an approved large-file policy before a GitHub push.
- No approved image/LLM/visual-evaluation provider, credential, quota, or price is configured.
- No licensed pinned font family or approved Git LFS quota/storage policy exists.
- Human theological/iconographic reviewer identities are not configured.

## Architecture adjustments

The user-specified lifecycle replaces the audit document's more granular proposed state names for this implementation. `READY_FOR_PUBLICATION` is deliberately defined as artifact readiness only and is equivalent in safety boundary to the plan's `FINAL_PDF_READY`; there is still no `PUBLISHED` state.

The requested six-specialist model combines lettering/PDF responsibilities with independent QA in one machine-readable contract, rather than the seven workers pictured in the audit. Independence is still enforced by approver/creator identity and immutable reviewed artifacts.

The plan mentioned a deterministic fixture image provider. To honor the stricter instruction not to simulate provider success, the foundation ships only its unavailable capability contract. A test-only implementation can be added when a later milestone explicitly needs provider-flow testing.

No Git LFS patterns are added because quota/billing authorization is still unknown. CI instead blocks oversized normal-Git binaries under `books/`.

The foundation groups closely related control-plane logic into focused modules rather than adding empty stage-specific placeholders. PR2 adds stage modules only for source intelligence, narrative validation, editorial QA, and bibles because those contracts are now executable.
