---
name: book-factory-director
description: Orchestrate a Khatakshetra book run through the repository state engine when asked to inspect, plan, resume, or advance Book Factory work.
---

# Book Factory Director

Use the `factory` CLI as the sole control interface. Read `book-factory/README.md`, the active book state, and only the specialist contract needed for the next legal stage.

Never infer state from chat. Check rules, graph validation, dependencies, approvals, provider capability, lease, retry limit, and budget before dispatch. Record typed outputs through the state engine. Stop on `BLOCKED`, `FAILED`, `ESCALATE`, ambiguous external results, or any unavailable capability. Never publish, deploy, merge, or spend without the required separate authorization.

Treat `EXISTING_EDITION` records as references and exclude them from automatic selection. A controlled-pilot dossier is not publication clearance. Use `evaluate-catalogue` before selection and `prepare-pilot` only for dossier/Story Packet preparation.

For manuscript work, require a hash-bound private-draft clearance before `prepare-manuscript-handoff`. A Codex specialist subagent is valid only through the explicit request/response handoff: record its agent id, exact request hash, zero paid cost, capability, and the orchestrator's session-scoped attestation. Import with `factory`; never treat unrecorded chat prose as a provider result. Preserve every immutable version and keep source, manuscript, editorial, visual, and publication status separate.

For PR5, manuscript v3 must receive separate `SOURCE_FIDELITY` and `LITERARY_EXPERIENCE` reviews from specialists other than the writer. Do not prepare visual preproduction until both exact-hash reviews pass. Import character/location bibles, storyboard, page scripts, typography and four proof specs only through `prepare-preproduction-handoff` and `import-preproduction-handoff`. A passing specification review may record `VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED`; it is not a visual approval and does not authorize images, PDF, publication, paid calls, or DM08 regeneration.
