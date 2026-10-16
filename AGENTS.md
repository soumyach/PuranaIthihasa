# Khatakshetra repository instructions

## Book Factory boundary

- Use `factory` / `python -m book_factory` as the only Book Factory control interface. Durable files, not chat history, are the system of record.
- Treat `research/source-graph/` as strictly read-only. Run its existing validator and integrity tests; do not replace them or silently normalize IDs.
- A complete story spine is a complete bounded chronology, not exhaustive scripture verification.
- Keep controlled-pilot eligibility, source verification, rights clearance, editorial certification, and publication readiness as separate decisions.
- Treat `EXISTING_EDITION` assets as immutable references and exclude them from automatic production unless explicitly requested.
- Keep bounded-arc completeness, chapter extraction, source examination, critical flags, and rights as separate readiness dimensions.
- Every critical Story Packet fact needs evidence; leave missing details `UNSPECIFIED` unless an adaptation is explicitly classified and approved.
- Editorial semantic PASS requires an independent reviewer or capability; otherwise use `ESCALATE`.
- Approval inheritance must preserve source scope, tradition, edition, evidence hash, expiry, and provenance.
- Production must fail closed when `MYTHOLOGY_COMIC_RULES.md`, required evidence, approvals, provider capability, budget, rights, fonts, or storage policy is absent.
- Never report an unsupported production stage or unavailable visual backend as successful. Use `NOT_IMPLEMENTED`, `BLOCKED`, `FAILED`, `FIX`, or `ESCALATE` as applicable.
- Never use an interactive coding agent as an undeclared manuscript or editorial-review provider.
- Do not overwrite approved assets. Add immutable, content-addressed versions and invalidate only their dependents.
- Never call a paid provider, publish, deploy, merge, or make a book public without the corresponding explicit authorization.
- Foundation fixtures stay under `book-factory/fixtures/`; do not add them to the authoritative `books/catalogue.json`.
