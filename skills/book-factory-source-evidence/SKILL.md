---
name: book-factory-source-evidence
description: Review source readiness for a Khatakshetra book using the repository source graph without modifying it.
---

# Source and Evidence Review

Follow `book-factory/contracts/workers/source-evidence.json`. Query only through the read-only adapter, preserve every graph ID, and run the existing validator before and after reading. Assess bounded-arc completeness, chapter extraction, source examination, critical flags, and rights independently. A `COMPLETE` spine proves only its bounded chronology. In the Story Packet, cite every critical source fact and leave missing motivation, dialogue, iconography, chronology, or causality `UNSPECIFIED`. Return `BLOCKED`, `INCOMPLETE_SOURCE`, or `NEEDS_SOURCE_REVIEW` instead of guessing, and never approve your own work.
