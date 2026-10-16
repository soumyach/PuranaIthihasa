---
name: book-factory-illustration
description: Produce versioned Khatakshetra illustration candidates through an approved provider after capability, approval, and budget gates pass.
---

# Illustration Production

Follow `book-factory/contracts/workers/illustration.json`. Require a durable idempotency key and cost reservation before any provider call. Preserve candidates and provider audit metadata; never bake narration or dialogue into art. Do not fall back to another provider, repeat an ambiguous billable request, or regenerate unaffected pages. A specification is not an image candidate: verify every image file and hash, enforce the two-attempt proof cap, and keep `BLOCKED_PROVIDER` explicit when the backend is unavailable.

PR6 may use the built-in Codex image tool only through the zero-direct-cost session bridge. Persist its locked request first, import the resulting real PNG and execution receipt, verify PNG CRC/pixel readability and exact 1086×1448 geometry, and retain every attempt under a hash-addressed filename. An image-generation response is not approval; wait for exact-image independent review and human style approval.
