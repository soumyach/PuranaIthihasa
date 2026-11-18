# Khatakshetra / PuranaIthihasa — Codex Account Migration Handoff

This document is the durable starting point for a completely new Codex account on a different device. Repository evidence, not prior chat history, is authoritative.

## 1. Repository authority and recovery

- Repository: <https://github.com/soumyach/PuranaIthihasa>
- Authoritative branch: `main`
- Last production-state commit before this migration document: `a327ff721f29f3c5c59f698e1b47da4b9e85d772`
- Authoritative migration commit: the tip of `origin/main` containing this document
- Source-graph hash: `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`
- Book Factory launcher: `./factory`
- Director skill: `skills/book-factory-director/SKILL.md`
- Repository rules: `AGENTS.md`

A Git commit cannot contain its own SHA without changing that SHA. Therefore the exact migration commit is deliberately represented by the immutable remote ref containing this file. On a fresh clone, resolve and verify it with:

```sh
git fetch origin
git switch main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

`HEAD` and `origin/main` must match before production resumes. The migration task's final delivery report also records the exact pushed SHA.

### Fresh-device setup

The project requires Python 3.9 or newer. From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
./factory validate
python -m unittest discover -s tests/book_factory -p 'test_*.py'
```

Runtime dependencies are declared in `pyproject.toml`: Pillow, ReportLab and pypdf. Poppler is needed only to re-extract pages from the original visual-benchmark PDFs; the exact extracted Gold Standard PNGs used by current DM02 requests are already tracked.

Useful read-only operating commands:

```sh
./factory status
./factory queue
./factory blocked
./factory approvals
./factory costs
./factory validate
./factory reconcile-book --book-id DM02
./factory resume --book-id DM02
./factory resume-book --book-id DM02
```

Do not use `--write`, import an approval, or invoke an image tool until the persisted evidence and pending authorization scope below have been checked. The generic Director projection may lag the newer versioned DM02 operational checkpoint; never allow an older projection to supersede the evidence in `books/DM02/zero-image-completion-v0001/`.

## 2. Product objective

Khatakshetra is an autonomous Book Factory intended to select eligible stories from an authoritative 78-title, 12-collection catalogue and produce source-faithful illustrated private storybooks. Its complete flow covers source readiness, Story Packet preparation, manuscript creation, independent editorial review, storyboard and visual bibles, bounded illustration, independent actual-pixel review, editable page composition and lettering, PDF assembly and inspection, and durable interruption recovery.

The objective is repeatable production of complete new books. Do not turn this into a sequence of manually improvised images, repeatedly remake an existing edition, or add more architecture merely because production crosses a host boundary.

## 3. What currently works

- **Catalogue and queue:** lossless catalogue import, source/readiness states, dependency-aware deterministic selection, resume-first behavior, and exclusion of existing editions.
- **Source packaging:** evidence-grounded Source Readiness Dossiers and Story Packets with explicit gaps, variants, claims, citations and adaptation boundaries.
- **Manuscript/editorial handoffs:** exact hash-bound Codex specialist requests and immutable responses; writers and independent reviewers remain separate.
- **Visual preproduction:** storyboards, page scripts, character/location bibles, typography records, proof specifications and approved private artistic conventions.
- **Codex-host orchestration:** the Director can persist exact handoffs and an active Codex session can dispatch the required specialist, record the real host identity, import the response and resume by request hash.
- **Image generation/editing:** built-in Codex image operations can execute exact approved requests with immutable input/reference receipts and operation ceilings.
- **Actual-pixel review:** an image-capable reviewer independent of the producer evaluates source fidelity, iconography, identity, anatomy, action, culture, composition, continuity, image artifacts and lettering compatibility.
- **Composition and editable lettering:** deterministic page composition preserves exact text, externalizes lettering, records crop geometry and supports page-local repair.
- **PDF assembly/inspection:** ordered page rasters can be assembled and inspected for count, order, dimensions, embedded pixels and hashes.
- **Budgets and gates:** campaign-level and per-unit limits, provider/cost checks, explicit approvals, retry ceilings and fail-closed behavior.
- **Immutable history:** source inputs, approvals, operation receipts, ledgers, reviews, parent lineage and superseding reassessments are preserved rather than rewritten.
- **Reconciliation/resume:** repository state and content-addressed evidence support deterministic resumption, subject to the projection warning above.

Image execution and semantic visual review are not standalone repository automation. They require an active Codex host with the built-in image capability and independent image-capable review. Shell/Python code must never pretend it spawned those host operations.

## 4. Historical safeguards

1. DM08 is registered as `EXISTING_EDITION`. Its PDF and Manuscript v2 are immutable reference assets, not newly produced output, and DM08 is excluded from automatic production unless explicitly requested.
2. DM04 is preserved but is not the active pilot. Do not resume or regenerate it while operating this DM02 checkpoint.
3. DM02 — *The Sleep That Held Vishnu* — is the active end-to-end pilot.
4. Private-production completion is distinct from source certification, theological certification, rights clearance and publication readiness.
5. `research/source-graph/` is strictly read-only. Do not silently normalize, rewrite or regenerate it.
6. Never fabricate a qualified reviewer identity, theological approval or semantic visual PASS.
7. Page 11 has an independent religious/iconography gate and remains blocked even if unrelated DM02 pages advance.
8. Use only built-in Codex image generation/editing for the pending campaign. No API key, external paid provider, intentional purchased-credit use, automatic credit purchase or workspace overage is authorized.
9. Zero incremental USD cannot be technically guaranteed by the tool interface. Stop if explicit payment, credit, overage, API-key or external-provider authorization is requested.
10. Historical campaign budgets and attempt counters are immutable and cannot donate unused capacity to a new campaign.

## 5. DM02 authoritative current state

The newest operational evidence supersedes older reconciler projections without deleting them:

- Execution report: `books/DM02/zero-image-completion-v0001/execution-report.v0001.md`
- Effective page projection: `books/DM02/zero-image-completion-v0001/effective-completed-pages.v0001.json`
- Unit reassessment: `books/DM02/zero-image-completion-v0001/unit-reassessment.v0001.json`
- Page 1 independent review: `books/DM02/zero-image-completion-v0001/independent-composed-page-review.v0001.json`
- Campaign request: `books/DM02/zero-image-completion-v0001/campaign-request.v0001.json`
- Authorization subject: `books/DM02/zero-image-completion-v0001/authorization-subject.v0001.json`
- Usage observation: `books/DM02/zero-image-completion-v0001/allowance-observation.v0001.json`

### Effective private-complete pages

`1, 2, 3, 4, 5, 22, 23, 24` — **8 of 24 pages**.

Page 1 was composed from existing pixels and locked text. Its rendered SHA-256 is `f82c4926890a2ba360b38ed37fe819b57f9e56e7e3ff0fc176b1cb6f8a26dd0b`; deterministic validation and independent actual-pixel/reading-size review passed. This is private-production completion only, not publication approval.

Page 19 panel 2 is reusable as-is, but Page 19 remains incomplete because its other panels require new pixels.

### Remaining work, excluding Page 11

- 21 localized image edits
- 6 new image generations
- 27 primary image operations total
- no retry, repair or edit-to-generation fallback allowance
- at most one operation per listed unit
- Pages awaiting the campaign: 6–10 and 12–21
- two derived crops, Page 8 panel 2 and Page 17 panel 2, become composition-only after their parent panels are corrected
- no other private-production blocker is currently recorded

The six genuine new-generation units are Page 6 panel 1, Page 10 panel 2, Page 12 panel 2, Page 19 panel 1, and Page 20 panels 1–2. The unit reassessment contains every exact page/panel ID, source event, parent image path/hash, defect, reference requirement and operation classification.

### Page 11

Page 11 remains exactly:

```text
ESCALATE_BEFORE_GENERATION
```

Its qualified review is unsigned. It is `QUALIFIED_REVIEW_REQUIRED`, excluded from the pending campaign and must not be generated, edited, approved or published until separately cleared and separately authorized.

### Preserved prior ledgers

- `books/DM02/book-level-production/provider-receipts/execution-ledger.v0001.json`
- `books/DM02/book-level-production/corrective-v0002/execution-ledger.v0001.json`
- `books/DM02/book-level-production/corrective-v0002/campaign-state.v0001.json`
- `books/DM02/two-localized-arm-repairs-v0001/execution-ledger.v0001.json`

The Page 4/5 arm-repair campaign is closed as `COMPLETED_EXACT_SCOPE_NO_RETRIES`. Do not reopen it, reset its counters or overwrite its image/review versions.

## 6. Pending remaining-book campaign

- Authorization subject: `6b9dc84b5796c79c0e1a6a68c6e5289e1c6b0795bf1a42900456b352a850aaa4`
- Status: `AWAITING_CAMPAIGN_AUTHORIZATION`
- Authorization received: false
- Approval record created: false
- Image operations executed under this subject: 0
- Exact scope: 21 localized edits plus 6 new generations
- Total ceiling: 27
- Maximum per unit: 1
- Retry/repair/fallback ceiling: 0
- Page 11 included: false
- Completed pages, DM04, DM08, source-graph changes, publication, deployment, push and merge: excluded
- Provider: built-in Codex image tooling only
- Spend authority: USD 0; included-allowance-first

The canonical subject binds the unit manifest SHA-256 `858691be877dc183c42183488fcf11f48ce7c1b136f8f1a87737550a9f48fe9f`, the approved private Vishnu/Brahma artistic-convention sheets, exact visual references, prior ledger hashes, and the then-current allowance observation.

Do not treat this handoff as authorization. Before any image operation, the new account must present the exact authorization request preserved in `campaign-request.v0001.json` and obtain explicit user confirmation through the existing approval boundary.

The persisted usage observation is historical and account-specific: primary 1% used/99% remaining, secondary 95% used/5% remaining, purchased-credit balance 0, no payment/overage request, and incremental USD cost unknown/unexposed. A different Codex account must perform a fresh read-only allowance check. If that check changes a bound campaign condition, prepare a new immutable authorization subject rather than silently mutating this one.

## 7. Production lessons already established

- Do not reject a recognizable multihooded Shesha merely because the hoods are visually countable unless the locked source/specification requires an exact count.
- Do not demand a generic empty top lettering band. Test the exact approved text with the deterministic composer and protect only essential imagery.
- Prefer composition/lettering/crop repair over changing pixels.
- Prefer a bounded localized image edit over complete regeneration when the existing scene, action, environment and most pixels remain valid.
- Preserve locked source-event chronology and approved series character identity.
- Where Vishnu is materially depicted in a readable full/medium figure, the approved private-production identity requires four visually accountable, anatomically coherent arms, stable deep-blue complexion, crown, U-mark, garments, ornaments and facial continuity.
- Brahma must remain distinguishable from a generic elderly sage and preserve the approved private-series convention and the navel-lotus relationship where the source event requires it.
- Do not impose unsupported fixed head, hood, arm, emblem, geography or anatomy claims.
- Historical failed reviews remain immutable. New evidence creates a versioned reassessment; it never retroactively rewrites the old review.
- Routine artistic variation is not a blocker. Stop only for a real source/iconography contradiction, failed identity/anatomy/action/readability gate, exhausted authorized operation, or explicit approval boundary.

## 8. Exact next action for a new Codex account

Do not repeat foundation audits, architecture work, prior image campaigns or completed pages.

1. Clone the repository, switch to `main`, fetch, and verify `HEAD == origin/main`.
2. Read this document, `AGENTS.md`, `skills/book-factory-director/SKILL.md`, `book-factory/README.md`, the zero-image checkpoint, and the four DM02 ledgers listed above.
3. Run `./factory validate` and the Book Factory tests. Inspect `./factory reconcile-book --book-id DM02` read-only.
4. Reconcile from the newest persisted evidence. If the generic projection still reports an older state, keep this versioned checkpoint authoritative and do not overwrite it with the stale projection.
5. Verify the canonical campaign subject, locked manifest hash, exact 21/6 operation lists, provider/spend rules and exclusions.
6. Perform a fresh read-only allowance/billing observation for the new account.
7. Request explicit authorization before any image operation. Never fabricate or infer approval from this handoff.
8. Once valid authorization exists, run the bounded 27-operation campaign autonomously in small routine batches within the exact manifest. No retries are permitted under the current subject.
9. Keep Page 11 excluded. After every operation, preserve the tool receipt, exact reference-image inputs/hashes/roles and immutable parent lineage.
10. Use a genuinely independent image-capable reviewer on the actual pixels. A failed unit stops without another operation under this subject.
11. Compose and independently review only pages whose required units pass. Preserve exact approved lettering and use page-local recovery.
12. Stop at any real source, religious/iconography, authorization, allowance, provider, cost or quality blocker.
13. Resolve Page 11 through its separate qualified-review and authorization path.
14. Once campaign pages and Page 11 pass, assemble and inspect the exact ordered 24-page private PDF. Do not claim publication approval.

## 9. Validation and repository boundaries

Before the migration push, the expected checks are:

```sh
./factory validate
python -m unittest discover -s tests/book_factory -p 'test_*.py'
python research/source-graph/validate_graph.py
python -m unittest discover -s research/source-graph -p test_integrity.py -v
python scripts/check_book_factory_boundaries.py
git diff --check
```

The source graph must retain hash `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`. The zero-image campaign request must remain unauthorized with zero operations.

Migration validation results on 2026-11-18:

- factory validation: `PASS`
- Book Factory suite: 241 tests, all passed
- source-graph structural validation: `PASS`, zero errors and zero warnings
- source-graph integrity suite: 15 tests, all passed
- repository boundary check: `PASS`; the intentionally local-only DM08 presentation PDF was reported as the expected warning

The original presentation-reference PDFs are intentionally not ordinary Git blobs. They are rights-sensitive local reference assets, and the DM08 combined PDF is above GitHub's 100 MB normal-blob limit. Their exact hashes and the eight extracted Gold Standard page PNGs used by production are tracked. Their absence does not remove any DM02 image target, receipt, composed page, review, ledger, campaign request or current A/B references required to resume the pending campaign.

No credentials, API keys or provider secrets belong in this repository.

## 10. Completion path

A. Complete now: Pages 1, 2, 3, 4, 5, 22, 23 and 24.

B. Pending bounded campaign: Pages 6–10 and 12–21, requiring exactly 21 edits and 6 generations under a future explicit authorization.

C. Independent Page 11 path: qualified review, separate authorization, image operation and independent review.

D. Other genuine private-production blockers: none currently recorded.

Once B and C pass, the deterministic composer can assemble the complete private 24-page PDF immediately. Public release, deployment and publication remain separate and unauthorized.
