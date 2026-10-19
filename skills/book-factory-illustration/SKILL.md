---
name: book-factory-illustration
description: Produce versioned Khatakshetra illustration candidates through an approved provider after capability, approval, and budget gates pass.
---

# Illustration Production

Follow `book-factory/contracts/workers/illustration.json`. Require a durable idempotency key and cost reservation before any provider call. Preserve candidates and provider audit metadata; never bake narration or dialogue into art. Do not fall back to another provider, repeat an ambiguous billable request, or regenerate unaffected pages. A specification is not an image candidate: verify every image file and hash, enforce the two-attempt proof cap, and keep `BLOCKED_PROVIDER` explicit when the backend is unavailable.

PR6 may use the built-in Codex image tool only through the zero-direct-cost session bridge. Persist its locked request first, import the resulting real PNG and execution receipt, verify PNG CRC/pixel readability and exact 1086×1448 geometry, and retain every attempt under a hash-addressed filename. An image-generation response is not approval; wait for exact-image independent review and human style approval.

For PR7 and later recovery campaigns, follow `book-factory/contracts/reference-conditioning.json`, `image-prompt-workflow.json`, `visual-production-units.json`, `source-bound-iconography.json`, and `book-factory/policies/indian-cultural-authenticity.json`. Supply exact role-labeled reference images A–D only when the backend proves support, and explicitly separate permitted style/composition guidance from forbidden benchmark story content. Use the storyboard-selected `CHARACTER_REFERENCE`, `PANEL_ILLUSTRATION`, or `FULL_PAGE_IMMERSIVE` unit, one principal action, and the exact lettering geometry. If an approved character or setting image is absent, record that absence; never promote a rejected proof into a reference. PR7 recovery requests are preparation only and never authorize generation, editing, or spend.
