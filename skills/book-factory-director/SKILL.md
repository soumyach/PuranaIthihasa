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

For PR6, use `prepare-proof-generation` before every image-tool call and `import-proof-image` after the real PNG exists. The Codex native tool is a session handoff, not an in-process API. Enforce two attempts per proof, eight total, zero paid spend unless a later explicit cap authorizes otherwise, exact 1086×1448 validation, immutable receipts, and duplicate rejection. Require a producer-independent `VISUAL_REVIEW` handoff that inspects exact pixels. Advance only the four-proof package to `AWAITING_STYLE_APPROVAL`; never self-approve style or begin full-book illustration.

For PR9, one `produce-next`, `produce-book`, or `resume-book` command advances every repository-executable stage until an exact external, Codex, or human boundary. Persist the stage job and handoff before stopping. Reuse completed jobs only when all input, policy, provider and approval hashes still match; invalidate dependent stages rather than the entire book. Prefer partial-run resumption, skip blocked titles when another candidate is eligible, honor title dependencies and collection style scope, and keep source readiness, editorial certification, visual completion, publication clearance and artifact readiness independent. Synthetic lifecycle outcomes are valid only in isolated fixture mode and are never publication evidence.

## Active Codex session execution

When this skill is running inside an active Codex session, do not stop merely because the next legal job is a `CODEX_SPECIALIST_SUBAGENT_HANDOFF`. Repository Python cannot create a host agent, but the Codex harness can. Use this exact loop:

1. Run `factory reconcile-book --book-id <ID> --write` when reconciliation evidence exists, then run the requested `produce-next`, `produce-book`, or `resume-book` command.
2. Read the exact persisted handoff request. Revalidate its request and handoff hashes. Never construct the specialist task from chat memory.
3. If a bound response already exists, do not dispatch again. Resume from that response. Otherwise dispatch exactly one Codex specialist with the required role and capability through the host's subagent tool.
4. Wait for that agent, persist its exact structured response, record the real host agent id, and validate the `CODEX_SPECIALIST_SUBAGENT_HANDOFF` execution receipt before importing it through `factory`.
5. For an independent review, dispatch a different agent and bind the reviewer request to the creator response hash. Reject matching creator/reviewer ids. A root-agent reread is not an independent review.
6. After every imported response, rerun `resume-book`. Continue only while the next action is repository-executable or a supported Codex handoff. Stop at image/provider work, human authorization, source/iconography qualification, spending ambiguity, retry exhaustion, or any other recorded approval boundary.

Interruption recovery is request-hash based: inspect `SessionHandoffStore.resume_status`, reuse a bound response, and never increment an attempt or dispatch a duplicate merely because the root session resumed. A missing, conflicting, or hash-invalid response is `ESCALATE`, not permission to improvise.

This host loop is the supported one-instruction operating path. Never claim that shell or Python code spawned the specialist; the execution receipt must identify the actual Codex host agent. Do not use external agent APIs, API keys, paid providers, or unrecorded assistant prose.

For complete-book campaign optimization, preserve the prior storyboard and campaign immutably. Freeze raster masters separately from illustrated panel slots: a reviewed shared master may serve bounded same-moment reframes, while text-only back matter remains deterministic layout. Require exact generation order, proof-first checkpoints, bounded batches, an explicit retry reserve, and fresh allowance inspection. No approval, pixel review, character reference, environment reference, or campaign authorization inherits to a revised storyboard hash.
