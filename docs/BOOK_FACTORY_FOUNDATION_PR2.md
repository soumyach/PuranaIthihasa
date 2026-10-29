# Khatakshetra Book Factory — Foundation PR2

Foundation PR2 adds source intelligence, narrative contracts, and editorial quality gates to the PR1 offline control plane. It does not generate a manuscript, illustration, page, or PDF and does not publish or deploy anything.

## Authoritative input inventory

The repository-local workspace, Desktop, Downloads, Codex attachments, and an exact-name Spotlight search were inspected.

Imported without alteration:

- `MYTHOLOGY_COMIC_RULES.md`, registered as `authoritative-2026-10-15` with SHA-256 `0f47a1bb48b3b85c7442d67e51398a6a5fe0e379790a09ed0d852d4d3ab65070`.
- `Satyanarayana_Vrata_Katha_Complete_Illustrated_Storybook.pdf`, a seven-page visual benchmark with SHA-256 `82ae125d099ef2608adad705922567df6b553db40dd39af64b77c5de28dcadd2`.
- `The_Enemy_Who_Multiplied_Original_Size_Combined.pdf`, a 30-page visual benchmark with SHA-256 `3867fccdd8c8755d27ff06c7543d8002cefb7531c1d4f39c743a43bff9c4a29f`.

The PDFs are presentation references only and are not evidence for story facts. Their rights status remains `UNKNOWN_REVIEW_REQUIRED`. The Enemy benchmark is 122,897,487 bytes, above GitHub's normal 100 MiB object limit; a future push needs an approved Git LFS or alternate storage policy.

Not found:

- `Khatakshetra_Illustrated_Library_Catalogue_v0.1.json`; expected authoritative destination `books/catalogue.json`.
- `The_Enemy_Who_Multiplied_Manuscript_v2.md`; expected raw-input destination `book-factory/inputs/manuscripts/The_Enemy_Who_Multiplied_Manuscript_v2.md`.

The machine-readable inventory is `book-factory/reports/missing-inputs.json`. The catalogue remains empty, and no DM08 production book or manuscript was created.

## Source-readiness dossiers

`book_factory.source_intelligence.SourceReadinessAssessor` evaluates each candidate across separate dimensions:

- Bounded story-arc completeness.
- Chapter extraction coverage for passages used by that arc.
- Explicit source-examination status.
- Unresolved critical flags and unsupported source claims.
- Rights clearance.
- Exact rules availability and hash.

The result is one of `READY`, `NEEDS_SOURCE_REVIEW`, `INCOMPLETE_SOURCE`, or `BLOCKED`. A catalogue value of `READY` is never enough on its own. A source-graph spine marked `COMPLETE` still means only that its declared bounded chronology is complete; it does not claim exhaustive scripture verification.

Dossier versions are immutable and keyed by their content hash. Re-running the same dossier write returns the same path and does not duplicate the output.

## Story Packet structure

A Story Packet is a deterministic transform of a read-only graph packet. It contains:

- Source, witness, tradition, frame, graph hash, and bounded-completeness statement.
- Ordered events and event-grounded claims.
- Characters, relationships, conflicts and reversals.
- Source-recorded motivations or explicit `UNSPECIFIED` values.
- Manifestations, boons, powers, passages, and evidence citations.
- Variants, conflicts, and unresolved review flags.
- Explicit adaptation boundaries.

Every event claim classified `SOURCE_FACT` carries evidence IDs. A missing factual detail is classified `UNSUPPORTED_SOURCE_GAP`; the code never fills it. Future manuscript work may use such a gap only through an expressly labeled `DRISHTI` or `KALPANA` choice with an adaptation note and any required approval.

## Narrative and editorial contracts

The manuscript contract requires an opening, context, ordered beats, complete ending, claim map, structured dialogue, source-packet hash, creator identity, and a declaration that the ending completes before an optional next-book hook.

Deterministic checks identify:

- Missing required events.
- Unsupported `MULA` or `SAMPRADAYA` claims.
- Unlabeled `DRISHTI` or `KALPANA` adaptations.
- Missing beat targets.
- Unattributed verbatim quotations and missing speakers.
- A next-book hook that precedes a complete ending.

The independent editorial gate combines those checks with human or separately capable semantic review. It cannot return `PASS` unless the reviewer differs from the creator, declares independence, and attests clarity, pacing, age suitability, dignity, identity distinctness, and source fidelity. If that capability is unavailable, the gate returns `ESCALATE`; it never fabricates a semantic PASS.

## Character and location bibles

Separate schemas and validators now exist for character and location bibles. Character entries define identity, source scope, manifestation rules, visual constants, required and prohibited attributes, evidence, and explicit unspecified fields. Repeated identity records must remain consistent, and a manifestation cannot silently cross a source scope. Location entries similarly separate grounded features, prohibited features, continuity constants, evidence, and unspecified details.

These contracts describe future references; PR2 creates no actual production bible for an authoritative book because the catalogue and manuscript inputs are missing.

## Approval inheritance

PR2 adds typed approvals for series visual standards, collection styles, character families, book-specific theological exceptions, and manuscript source disputes. Inheritance requires:

- An exact subject hash.
- An explicitly allowed parent scope.
- Identical source scope, tradition, and edition.
- An unchanged evidence hash.
- No changed invalidator and no expiry.

Book theological exceptions, manuscript source disputes, source readiness, manuscripts, page composition, and theological resolutions are non-inheritable. Records preserve creator, approver, conditions, evidence references, boundaries, invalidators, and timestamps.

## Deterministic versus AI-assisted work

Implemented deterministically and offline:

- Rules/reference hash verification.
- Read-only graph validation and extraction.
- Dossier and Story Packet construction.
- Contract/schema checks, event coverage, provenance checks, bible consistency, approval lookup, and immutable version storage.
- Exact blocker reporting and synthetic tests.

Not implemented and never simulated as successful:

- Manuscript drafting or rewriting.
- Literary, theological, iconographic, family-reader, or visual judgment without an independent reviewer/capability.
- Illustration, lettering, layout, or PDF generation.
- Paid/network provider execution.
- Publication, deployment, pull-request creation, push, or merge.

## Future manuscript-worker consumption

The PR3 manuscript worker should accept exactly one approved manifest, dossier hash, Story Packet hash, rules hash, and audience contract. It should map each required packet event to one or more manuscript beats, create a claim-map entry for every material sentence or dialogue unit, preserve source evidence IDs, and label all artistic bridges. The resulting immutable manuscript version should enter deterministic validation before independent editorial review. No downstream stage should consume a mutable working draft.

## CLI

```sh
./factory status
./factory missing-inputs
./factory check-readiness
./factory source-dossier --book-id ID
./factory source-dossier --book-id ID --write
./factory story-packet --spine-id SPINE_ID
./factory validate
```

`source-dossier` is dry-run/read-only unless `--write` is present. `story-packet` never modifies the graph. Existing PR1 commands remain available.

## Risks and limitations

- No production candidates can be assessed until the authoritative 78-book catalogue arrives.
- DM08 manuscript evaluation cannot begin until Manuscript v2 arrives.
- Benchmark rights need review; their presence does not grant production rights.
- The 122.9 MB benchmark prevents a normal GitHub push unless large-file handling is approved.
- Graph coverage is substantial but deliberately bounded; unresolved source gaps must remain visible.
- Independent semantic and visual reviewer capabilities are not configured.
- Fonts, provider credentials, paid budgets, publishing, and deployment remain blocked.

## Recommended PR3 scope

1. Import and reconcile the authoritative catalogue while preserving all original IDs and collection relationships.
2. Import DM08 Manuscript v2 as an immutable source artifact.
3. Build dossiers and Story Packets for a small controlled candidate set; resolve rights and source blockers with named reviewers.
4. Implement a provider-neutral manuscript-draft adapter in dry-run mode with complete claim maps and no paid calls.
5. Run deterministic manuscript validation and independent editorial review; iterate through immutable versions.
6. Add approved large-file storage and font policies separately before any PDF or illustration work.

PR3 should not begin illustration or PDF production.
