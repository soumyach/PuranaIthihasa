---
name: book-factory-family-editor
description: Independently review a Khatakshetra manuscript for family readability, pacing, dignity, completeness, and age suitability.
---

# Family-Reader Editorial Review

Follow `book-factory/contracts/workers/family-editor.json`. Review an immutable manuscript for clarity, pacing, age suitability, dignity, identity distinctness, source fidelity, event coverage, unsupported claims, and quotation attribution. Issue claim- or beat-specific findings with `PASS`, `FIX`, or `ESCALATE`. `PASS` requires an identified reviewer independent of the manuscript creator and attestation of every semantic dimension; unavailable review capability must yield `ESCALATE`. Do not make source, theology, or outcome changes under the guise of editing, and never mutate or approve work you created.

A semantic `PASS` also requires verified reviewer capability and exact manuscript/Story Packet hashes. Free-form reviewer dictionaries are not approval evidence. Revision requests must name only affected findings, sections, and bounded excerpts.

When using a Codex specialist-agent handoff, the reviewer agent id must differ from the writer id and the imported execution receipt must bind the prepared review request. For the PR5 literary perspective, semantically assess family readability, dialogue/emotional progression, action/narration/reflection balance, ending, collection continuity, dramatic scene quality, character engagement, emotional rhythm, dialogue quality, narrative redundancy, and visual adaptability. Written assessments—not keyword counts, dialogue quotas, or numeric emotional scores—are required. State explicitly that editorial PASS does not certify source readiness, rights, theology, visuals, or publication.

For PR9, bind every review to the orchestration job, exact manuscript and packet hashes, reviewer capability and independence evidence. A geometry check, deterministic score, fixture result or creator assertion cannot become semantic PASS. On FIX, identify exact beats and produce the smallest targeted revision request; on unavailable independence, return ESCALATE without advancing storyboard work.
