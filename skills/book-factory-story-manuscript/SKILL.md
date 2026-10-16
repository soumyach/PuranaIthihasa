---
name: book-factory-story-manuscript
description: Create or import a source-grounded Khatakshetra manuscript after source readiness and rules are approved.
---

# Manuscript and Story Direction

Follow `book-factory/contracts/workers/manuscript-story.json`. Work only from the approved dossier, Story Packet, active manifest, and exact rules hash. Map every required event to a beat. Label each material claim `MULA`, `SAMPRADAYA`, `DRISHTI`, or `KALPANA`; cite source claims and explain adaptations. Attribute verbatim quotations, structure narration and dialogue separately, and complete the story ending before any next-book hook. Preserve supplied manuscripts unless rewriting is explicitly authorized. Return a new immutable version rather than overwriting an approved artifact.

Draft only through a verified `manuscript_generation` provider. If it is unavailable, return `BLOCKED_PROVIDER` and create no draft. Literary benchmarks guide quality only and must not be copied or treated as source evidence.
