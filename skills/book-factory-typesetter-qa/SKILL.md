---
name: book-factory-typesetter-qa
description: Typeset editable Khatakshetra pages and independently validate lettering, continuity, PDF geometry, and tracked visual QA.
---

# Typesetting and Independent QA

Follow `book-factory/contracts/workers/typesetter-independent-qa.json`. Treat structured narration, dialogue, thoughts and source insets as four distinct authoritative channels. Preserve editable layers and validate page order, stable page ids, 1086 × 1448 3:4 geometry, caption/dialogue duplication, continuity, provenance and safe regions. Inspect font availability and licensing, bundle no unauthorized font, and never call a digital canvas print-ready until trim, bleed and export requirements are approved. Report semantic image assessment as not executed while no real visual-review backend and rendered images exist. A critical finding blocks readiness; this role never publishes or deploys.

When PR6 provides real proof PNGs, inspect the exact hash-bound pixels independently from the producer. Assess all thirteen visual dimensions, return only `PASS`, `FIX`, or `ESCALATE`, and never infer a result from prompts or metadata. A `PASS` requires every dimension to pass and still does not constitute human style approval.
