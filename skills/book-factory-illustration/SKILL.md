---
name: book-factory-illustration
description: Produce versioned Khatakshetra illustration candidates through an approved provider after capability, approval, and budget gates pass.
---

# Illustration Production

Follow `book-factory/contracts/workers/illustration.json`. Require a durable idempotency key and cost reservation before any provider call. Preserve candidates and provider audit metadata; never bake narration or dialogue into art. Do not fall back to another provider, repeat an ambiguous billable request, or regenerate unaffected pages. A specification is not an image candidate: verify every image file and hash, enforce the two-attempt proof cap, and keep `BLOCKED_PROVIDER` explicit when the backend is unavailable.
