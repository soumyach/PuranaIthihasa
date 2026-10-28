# Book Factory production-unblocking report

## Scope and baseline

- Branch: `feature/book-factory-production-unblocking`
- Audited parent: `67bdd61f4d9740845d80cb319ab93456e9665d72`
- Scope: canonical production-state reconciliation and active-Codex specialist execution only
- Media produced: none
- Paid/provider operations: none
- Publication, deployment, push and merge: none

The pre-existing `.DS_Store` changes were left unmodified by the implementation and are excluded from the commit.

## Root cause

`AutonomousFactoryDirector._load_run` and `ProductionQueue` consulted only `orchestration/run.json`, the historical `run/events.jsonl`/`run/state.json`, and the old `production-status.json`. DM02's later book-level campaign ledger, page acceptance records, independent reviews, exact approval and the subsequent Brahma/Vishnu identity invalidation were never projected into the Director's effective state. The old materialization therefore reported `ART_PROOFS` even though 39 book-level image operations had executed.

## Reconciliation fix

`ProductionStateReconciler` consumes a versioned, hash-pinned evidence manifest. It:

- replays the immutable historical event log and requires it to equal the historical materialization;
- validates the exact campaign subject and non-inheritable approval;
- validates all 39 contiguous execution receipts, provider identifiers, output hashes, operation classes and per-unit attempt ceilings;
- validates accepted composed pages and their deterministic and independent reviews;
- applies later active invalidations without deleting or rewriting accepted artifacts;
- derives ordinary and separately qualified resume units from evidence rather than a DM02 code override;
- fails on missing hashes, record disagreement, conflicting manifest chains or duplicate evidence;
- writes only a deterministic `orchestration/effective-state.json` projection when explicitly requested.

`produce-next`, `produce-book`, `resume-book`, legacy `resume`, queue and factory status now consult that projection. Repeated reconciliation is byte-stable and does not spend, generate or increment attempts.

## Actual DM02 state

- Effective stage: `ILLUSTRATION`; effective status: `BLOCKED`
- Historical stage retained: `ART_PROOFS`, version 7
- Campaign: 39/43 operations executed: 29 necessary, 3 conditional-derived fallbacks and 7 review-directed repairs
- Operations authorized for resume: 0
- Unspent conditional reserve: 4, but the campaign scope is closed and cannot be repurposed
- Recorded complete before later invalidation: 15 pages
- Effective complete after identity invalidation: pages 2, 3, 22, 23 and 24
- Effective blocked: 19 pages; every blocked page retains recovery requirements
- All 15 previously accepted page artifacts remain recorded and hash-bound
- Page 11: `ESCALATE_BEFORE_GENERATION`, not generated, qualified review unsigned, separately gated
- Ordinary corrective candidates after required approvals: 33 units, including the pre-existing page-1 correction; none is currently authorized
- Effective blockers: closed campaign scope, new exact campaign authorization, Brahma/Vishnu character-reference approval, and Page 11 qualified review

`produce-next` evaluates all 78 catalogue entries and reports no currently eligible book; its DM02 row is `ILLUSTRATION/BLOCKED` with the same four blockers. `resume-book --book-id DM02` returns the same effective state and does not repeat work. Catalogue evaluation still ranks DM04, DM02 and DM01 as conditional finalists; none is strictly source-ready, so the queue correctly does not start a different title.

## Active-Codex mechanism and live demonstration

Repository Python still does not claim to spawn a Codex agent. The Director skill now runs the supported active-session loop: read a persisted handoff, use the Codex host's specialist tool, persist and validate the exact response and receipt, dispatch a different reviewer when required, then resume by request hash. This follows the documented Codex multi-agent boundary: the harness supplies the agent tools when enabled rather than the application declaring them itself ([OpenAI multi-agent documentation](https://developers.openai.com/api/docs/guides/agents-api/multi-agent)).

The live non-production demonstration used real host agents, not fixture results:

1. `/root/production_state_diagnostic` executed the locked production-state diagnostic and returned `PASS` with zero paid calls and zero recorded cost.
2. Its exact response was validated and persisted as response `cb715bc83748f2233708c89144c90ca2169616bd06f362aee84c5687c811a4a2`.
3. The loop deliberately stopped after import. A fresh `SessionHandoffStore` resumed as `SPECIALIST_RESPONSE_AVAILABLE` with `dispatch_required: false`, proving no duplicate specialist dispatch.
4. `/root/production_state_independent_review`, a different recorded agent id, independently recomputed the state and returned `PASS`.
5. Its exact response was validated against creator independence and persisted as response `c0c69bdec66673aa08c484cea1fa68e47d30ef270424c0b5953988c160836a4f`.
6. The next Director step stops at the real missing approvals. No image or provider handoff is legal.

These are session-scoped orchestration attestations, not cryptographic identity claims. The host loop is supervised and available only while Codex supplies the specialist tools; the repository remains safely resumable when they are absent.

## Verification

- 241 tests pass with the Codex workspace runtime.
- The new tests cover historical replay through reconciliation, the actual 39-operation campaign, readiness projection, evidence tamper/conflict rejection, attempt preservation, repeat invocation, production-asset immutability, host receipt validation, reviewer independence, interruption recovery and the missing-approval stop.
- `python -m book_factory validate`: `PASS`
- `git diff --check`: clean
- Source graph, DM04 and DM08: byte-for-byte unchanged by reconciliation and resume tests
- New images, manuscripts and PDFs: none

Apple's bare system Python lacks Pillow, reportlab and pypdf, so media-related legacy tests must use the Codex workspace Python runtime. This is an environment dependency, not a product-test failure.

## Delivery readiness

The configured remote is `https://github.com/soumyach/PuranaIthihasa.git`. A read-only `ls-remote` succeeds, and `git push --dry-run` reports that the new branch can be created. No push occurred. The GitHub CLI is not installed, so PR creation must use the web compare page or an environment with `gh`.

After review, delivery commands are:

```sh
git push -u origin feature/book-factory-production-unblocking
```

Then open:

`https://github.com/soumyach/PuranaIthihasa/compare/audit/book-factory-final-integration-readiness...feature/book-factory-production-unblocking?expand=1`

## Assessment

`CONDITIONAL_GO` for a supervised, one-instruction private-book run.

Canonical recovery and actual supported Codex specialist execution now work without manual worker coordination. The run remains correctly conditional on source and human approvals, qualified iconography review, a hash-bound image campaign and an available authorized host image tool. It is not an unattended service and it is not authorized to publish or spend.
