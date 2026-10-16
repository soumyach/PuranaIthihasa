# Book Factory Foundation PR3 — Catalogue, reference edition, and new-book pilot

PR3 imports the authoritative 78-book/12-collection catalogue without changing its source bytes or original fields, reconciles reviewed catalogue-to-graph mappings, registers DM08 as an existing reference edition, and prepares DM04 as the first conditional new-book pilot. It does not generate a manuscript, illustration, or PDF.

## Immutable inputs

- Catalogue v0.1 SHA-256: `e80483a0c77e8453616868b85ce883407e7c5bfaa81fae5d6c605266764c2f5b`.
- DM08 Manuscript v2 SHA-256: `6684d61e7c8f58a3fc3d851d7e8cbc7d13eb1e42105dbb9d011c1e7453791865`.
- DM08 PDF SHA-256: `3867fccdd8c8755d27ff06c7543d8002cefb7531c1d4f39c743a43bff9c4a29f`; 122,897,487 bytes; local, ignored, and outside ordinary Git history.
- Satyanarayana reference PDF SHA-256: `82ae125d099ef2608adad705922567df6b553db40dd39af64b77c5de28dcadd2`; local, ignored presentation reference.

DM08 is `EXISTING_EDITION` / `PRE_EXISTING_IMPORT`, is excluded from automatic selection, and has separate `PENDING_SCOPE_RECONCILIATION` source verification and `PENDING_INDEPENDENT_REVIEW` publication readiness. Its manuscript covers chapters beyond the catalogue's chapter-8 scope, so existence is not treated as certification.

## Catalogue result

The original roadmap declares 22 `SOURCE_SPINE_READY`, 10 `PARTIAL_GRAPH`, 42 `SOURCE_WORK_NEEDED`, and four `ORIGINAL_FICTION` entries. Reconciliation records four exact mappings, 18 verified subset mappings, and 56 explicit unmapped entries. No unreviewed title-match mapping is inferred.

Strictly ready books: **0**. Rights clearance and independent review remain unresolved. Under the documented controlled-pilot policy, the top conditional finalists are:

1. DM04 — The Buffalo King
2. DM02 — The Sleep That Held Vishnu
3. DM01 — The King Who Could Not Let Go

DM04 is recommended because its exact 16-event Mahisha arc is self-contained and offers the broadest visual/narrative range for eventually exercising the full factory. This recommendation is not publication clearance.

## Prepared pilot boundary

Only DM04's immutable Source Readiness Dossier and book-bound Story Packet are stored under `books/DM04/`. The dossier remains `BLOCKED` on rights and records atomically partial chapter extraction. The Story Packet includes the exact selected event IDs, witness and rights evidence, graph hash, citations, characters, relationships, powers, variants, and adaptation boundaries.

`factory draft-manuscript --book-id DM04 --dry-run` returns `BLOCKED_PROVIDER`; `factory review-manuscript --book-id DM04` returns `BLOCKED_REVIEWER`. Neither command writes a manuscript or review. The interactive agent is not used as a hidden production provider.

## Commands

```sh
./factory evaluate-catalogue
./factory evaluate-catalogue --write
./factory prepare-pilot --book-id DM04
./factory draft-manuscript --book-id DM04 --dry-run
./factory review-manuscript --book-id DM04
./factory validate
```

## Safety and resumption

- `research/source-graph/` remains byte-for-byte read-only.
- Shared graph spines are scoped by exact candidate event IDs.
- Stored dossier/packet hashes are recomputed rather than trusted.
- Manuscript and review version stores are immutable, sequential, parent-linked, and idempotent.
- Semantic PASS requires a verified independent reviewer capability and exact reviewed-input hashes.
- Existing editions, blocked candidates, and active book IDs are not automatic production choices.
- No publish, deploy, provider call, or paid action exists in this milestone.
