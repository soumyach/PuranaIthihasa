---
name: book-factory-source-evidence
description: Review source readiness for a Khatakshetra book using the repository source graph without modifying it.
---

# Source and Evidence Review

Follow `book-factory/contracts/workers/source-evidence.json`. Query only through the read-only adapter, preserve every graph ID, and run the existing validator before reporting readiness. A `COMPLETE` spine proves only its bounded chronology; surface wider gaps, variants, rights limits, and `NEEDS_REVIEW` flags. Produce typed dossier and QA outputs, and do not approve your own work.
