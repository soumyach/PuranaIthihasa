# Khatakshetra Book Factory — Final Integration Readiness

**Audit date:** 2026-10-28

**Audit baseline:** `feature/book-factory-dm02-production-unblocking` at `d77570e639b262a03f8a0e0cc4ba578975aa1422`

**Audit branch:** `audit/book-factory-final-integration-readiness`

**Decision:** **NO_GO** for the requested unattended, one-command factory across the 78-title catalogue. The repository is a functioning, fail-closed supervised production toolkit, but it is not yet one integrated autonomous production system.

No image, manuscript, storybook, paid-provider, source-graph, DM04, or DM08 operation was performed. The audit preserved the pre-existing `.DS_Store` changes.

## 1. Verified repository state

- The reported baseline was exact: branch `feature/book-factory-dm02-production-unblocking`, HEAD `d77570e639b262a03f8a0e0cc4ba578975aa1422`.
- The working tree initially contained only unrelated state: modified root `.DS_Store`, plus untracked `books/.DS_Store` and `books/DM04/.DS_Store`. They remain untouched and uncommitted.
- All local factory branches are ancestors of the baseline HEAD. The history from the planning commit through PR1–PR13 and the DM02 work is one linear, reachable chain. No implementation merge or consolidation branch is needed.
- The baseline is `0` commits behind and `28` commits ahead of `origin/main` (`dae505d`). A live read-only `ls-remote` found only remote `main`; none of the factory branches is delivered remotely.
- Factory version is `0.12.0`. The coherent HEAD contains 38 `book_factory/` files, 42 schemas, 13 skills, 16 Book Factory test modules, policies/contracts, 78-title catalogue configuration, source artifacts, production records, images, composed pages, and PDFs.
- There are 1,743 tracked files. Relevant tracked groups include 445 DM02 files, 323 DM04 files, 416 source-graph files, and 25 `output/` files.
- The source graph remained unchanged and valid: hash `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`; 19 sources, 34 witnesses, 1,025 passages, 3,515 entities, 1,118 events, and 149 story spines (93 complete, 56 partial).

### Integration lineage

All milestone tips are reachable from HEAD: foundation PR1–PR3 (`2c31b84`, `1a951c4`, `1c63c9c`), PR4–PR10 (`9dbb722` through `4c28c25`), PR11–PR13 (`dca733d`/`49b5e78`, `dd40102`, `b1574f8`), and the complete DM02 chain from `36d3c4d` through `d77570e`. The reported intermediate commits `79d123d`, `5db8b5f`, `8909cd8`, `7335973`, `975e350`, `d1e59f3`, and their intervening campaign commits are all present.

**Conclusion:** current HEAD already contains the complete local implementation and artifact history. Creating merges or copying work between local feature branches would duplicate history rather than integrate it.

## 2. Tests and direct evidence

| Check | Result |
|---|---|
| `python -m unittest discover -s tests/book_factory -p 'test_*.py'` | **PASS**, 232 tests in 44.135 s |
| `python -m book_factory validate` | **PASS**; schemas, references, 29 handoff responses, mappings, production receipts, and source-graph baseline validated |
| `research/source-graph/validate_graph.py` | **PASS**, no errors or warnings |
| Source-graph integrity suite | **PASS**, 15 tests |
| `scripts/check_book_factory_boundaries.py` | **PASS**; expected warning for the intentionally local-only DM08 reference PDF |
| Actual DM02 page 24 `factory validate-page --private-preview` | deterministic page/lettering **PASS**; semantic pixel review correctly **ESCALATE**s to an image-capable reviewer |
| Actual DM02 15-page PDF `factory inspect-pdf --private-preview` | **PASS**; manifest order, 1,086 × 1,448 page rasters, pixel hashes, PDF hash, and private-only state verified |

The tests establish strong deterministic coverage, but synthetic tests were not treated as proof of host-level autonomy. The classifications below also use actual catalogue, DM02, image-receipt, page, PDF, and Git state.

## 3. Actual capability matrix

| ID | Capability | Classification | Actual evidence and limit |
|---|---|---|---|
| A | Automatic source-ready selection | **WORKING_AUTONOMOUSLY** | The live 78-title queue is evaluated deterministically: 76 `BLOCKED`, DM02 `ELIGIBLE_RESUME`, and DM08 `EXCLUDED`; resume-first selection chooses DM02. No fresh title is currently source-ready, so selection cannot start a second new book. |
| B | Source Readiness Dossier and Story Packet | **WORKING_AUTONOMOUSLY** | Live `source-dossier --book-id DM02` and `story-packet --spine-id dm-story-madhu-kaitabha` read the real graph, produce hashed evidence, and fail closed. DM02's dossier remains blocked for broad production while its packet has 8 claims and 7 citations. |
| C | Manuscript and independent editorial handoffs | **WORKING_WITH_CODEX_HOST** | Request/import/schema/evidence gates and real DM02/DM04 records validate. The CLI has no configured manuscript, language-model, or editorial-review executor and cannot run the specialists itself. |
| D | Storyboard and character/location bibles | **WORKING_WITH_CODEX_HOST** | Real versioned DM02/DM04 storyboards and bibles exist and validate, but their semantic creation/review used active Codex orchestration, not an in-process repository worker. |
| E | Image handoff and reference binding | **WORKING_WITH_CODEX_HOST** | Hash-bound requests, A/B/C/D reference roles, approvals, immutable versions, and actual receipts exist. Pixel creation is a host-injected Codex image operation and additionally requires exact campaign authorization. |
| F | Image execution-receipt validation | **WORKING_AUTONOMOUSLY** | The validator checks actual files, hashes, dimensions, request/approval subjects, references, counters, and lineage without making an image call. |
| G | Page composition and editable lettering | **WORKING_AUTONOMOUSLY** | The repository page engine produces deterministic compositions, external lettering, rendered pages, and validation records from eligible art/scripts. Actual DM02 page validation passed. |
| H | Page image and lettering review | **WORKING_WITH_CODEX_HOST** | Deterministic geometry/lettering checks run locally. Crop meaning, action, anatomy, iconography, culture, and character continuity correctly require independent actual-pixel review. |
| I | PDF assembly and inspection | **WORKING_AUTONOMOUSLY** | Given an eligible page manifest, the repository engine assembles and inspects PDFs. The actual 15-page DM02 private proof passed. The generic `providers.pdf.available=false` status is stale/misleading; the page engine itself works. |
| J | Page-local repair | **WORKING_WITH_CODEX_HOST** | Re-lettering, layout, crop selection, re-composition, and revalidation are local. Any truthful new-pixel repair still needs the Codex image host, a valid bounded approval, and independent review. |
| K | Resumability after interruption | **BLOCKED** | Fixture mechanics pass, but real canonical DM02 state is stale: `run/state.json` remains at `ART_PROOFS` while later records show 39 operations and 15 composed pages, followed by a series-identity rejection affecting 33 panels. `produce-next` resumes the stale record, not the actual latest production truth. |
| L | Automatic continuation to the next book | **BLOCKED** | The queue algorithm exists, but the director cannot cross host boundaries or complete DM02 from one command, and all 76 non-DM02/non-DM08 entries are currently blocked. No real book-completion-to-next-book transition has occurred. |
| M | Artifact persistence and GitHub preparation | **SCAFFOLDED** | Local immutable artifacts, hashes, approvals, Git commits, and private/public labels are strong. Remote delivery is not complete: the chain is local-only, no remote feature branch exists, `gh` is absent, and write/PR permission is unverified. |

## 4. One-command finding

The exact intended command was run with the bundled Python runtime:

```text
./factory produce-next
```

It selected DM02, returned `ESCALATE`, stopped at `ART_PROOFS` with `APPROVED_EXTERNAL_IMAGE_PROVIDER_REQUIRED`, and reported `mutated:false` and `mutated_art:false`. SHA-256 hashes of `books/DM02/run/state.json`, `books/DM02/production-status.json`, and `books/DM02/book-level-production/status.v0004.json` were identical before and after; the working tree did not gain production changes.

This proves that the CLI safely selects and stops. It does **not** prove active orchestration. The process cannot invoke Codex specialist workers, the built-in image tool, or semantic pixel review. More importantly, it stopped on a pre-campaign state even though the repository contains the later 39-operation campaign and composed pages. `factory resume --book-id DM02` exposes the same stale PR5-era view.

A single Codex instruction can currently coordinate the missing host steps because the active session can read requests and call supported tools. That is active Codex-session orchestration, not capability of `./factory produce-next`. It still requires the agent to reconcile state and drive each host boundary correctly.

## 5. Current DM02 state

The latest campaign status before the user's Brahma/Vishnu rejection records:

- 39 of a 43-operation ceiling used: 29 necessary, 3 derived fallbacks, and 7 review-directed repairs; 4 reserve operations remained unspent and no more were planned.
- 24 planned pages; 15 marked complete for private preview and 9 blocked.
- Page 11 is `ESCALATE_BEFORE_GENERATION`, has no new image, and has no signed qualified review.
- The 15-page partial PDF is valid and explicitly not a complete-book claim (`d51e586753c35c41a8e25065af6e3f80dd62727dad21cf26ad833e98b9adb3db`).
- Actual incremental USD remains `UNKNOWN_NOT_EXPOSED`; repository records report no separately billed API-provider call.
- Publication is `BLOCKED_PRIVATE_INTERNAL_ONLY`.

The later identity audit at `d77570e` supersedes the reuse assumptions without erasing prior records. It inspected 41 raster versions across 33 current Brahma/Vishnu panels: 20 are localized character-replacement candidates, 12 require full regeneration, and Page 11 requires full regeneration only after qualified review. No complete divine-containing raster is eligible for unchanged canonical/final reuse. Of the formerly 15 complete preview pages, 10 (7–9, 13–18, and 21) contain now-affected panels; only pages 2, 3, 22, 23, and 24 are unaffected by that particular identity decision, subject to their other private-preview gates.

### Exact minimum path to a complete private DM02 PDF

1. Obtain human approval or amendment of the proposed series-level Brahma and Vishnu identity sheets. This is artistic/reference approval, not theological certification.
2. Obtain the scoped qualified review required for Page 11; otherwise a 24-page complete book is impossible.
3. Create and explicitly authorize a new hash-bound corrective campaign. Existing approvals cannot be repurposed after reference/source/unit invalidators changed.
4. Correct the 33 affected panels according to the preserved inventory (20 bounded replacement candidates, 12 full regenerations, and Page 11 after its gate), while also resolving still-blocked page 1 and pages 4, 5, 6, 10, 12, 19, and 20. Planning classifications are not guarantees that edits will pass.
5. Independently review actual pixels, recompose/review affected pages, build an exact 24-page manifest, then assemble and inspect a new private-only PDF.

No current campaign budget authorizes those operations.

## 6. True blockers

| Class | Affected capability | Evidence / impact | Smallest corrective action | Code change? |
|---|---|---|---|---|
| **CRITICAL_ENGINEERING** | K, L, one-command truth | Canonical `run/state.json` and `production-status.json` do not incorporate the later DM02 book campaign or identity invalidation. This prevents trustworthy resume, final-PDF gating, and queue continuation. | Add one narrow reconciliation/projection step that imports the latest immutable campaign, review, composition, and invalidation records into the canonical director state; test it against actual DM02 history. | **Yes** |
| **CRITICAL_ENGINEERING** | C–E, H, J, L from `./factory` | The CLI declares active-Codex stages but has no host driver and cannot invoke specialists/image/review. It only emits/stops. This blocks unattended private production. | Implement the smallest Codex-host director loop that consumes existing handoffs, calls only supported host tools, imports receipts, and resumes the existing state machine. Do not add another framework. | **Yes**, only if the CLI/single entrypoint must be autonomous |
| **CRITICAL_ENGINEERING** | Public publication | Publishing is explicitly `NOT_IMPLEMENTED`. | Keep private production separate; implement publishing only after legal/editorial policy is decided. | **Yes**, public only |
| **EXTERNAL_DEPENDENCY** | C–E, H, J | Models, built-in image execution, and semantic visual review are host capabilities, not repository executors; availability/cost exposure must be rechecked each session. | Run in an active Codex host and stop if the approved provider/policy is unavailable. | No repository algorithm required |
| **EXTERNAL_DEPENDENCY** | DM02 completion | New pixels need a new exact book-level corrective authorization. Prior campaign invalidators changed. | Approve one bounded corrective campaign after reference and Page 11 decisions. | No |
| **EXTERNAL_DEPENDENCY** | GitHub delivery | Read access works, but `gh` is absent and write/PR permission is unknown. | Verify authenticated write access, then push one ordinary review branch and open a PR; do not rewrite history. | No |
| **QUALITY_GATE** | DM02 private PDF | Page 11 qualified review is unsigned; proposed Brahma/Vishnu identities are not approved; affected pixels need independent review. | Complete only those scoped reviews and pixel corrections. | No |
| **QUALITY_GATE** | A, L across 78 titles | Queue is 76 blocked, 1 resumable, 1 excluded. Catalogue mapping outcomes are 4 exact, 18 subset, and 56 unmapped; readiness is 22 incomplete-source and 56 needs-review. | Curate source mapping/readiness in bounded batches; do not weaken gates. | Primarily evidence/editorial work, not new framework code |
| **QUALITY_GATE** | Public publication | Rights, full-arc source/theological review, typography/print specifications, and publication approval are not established. | Resolve per book/market before publication. | Usually no; publishing implementation remains separate |
| **OPTIONAL_ENHANCEMENT** | Status clarity | `status` calls old DM02 and DM04 durable records “active” despite `max_active_books=1`; generic PDF-provider status contradicts the working repository page engine. | Rename durable records and report the page engine separately. | Small, deferrable |
| **OPTIONAL_ENHANCEMENT** | Repository growth | Git LFS is not configured. It is not required for current files, but binary growth will increase clone cost. | Add an asset-size policy; introduce LFS/object storage prospectively before large-scale production, without rewriting current history during this audit. | Optional |

Routine artistic variation should not become a blocker: only source contradictions, series-identity violations, illegible storytelling, failed anatomy/composition, or an explicit review gate should stop a unit. Lettering-band occupancy alone is not a rejection criterion.

## 7. GitHub delivery readiness

- The local chain can be reviewed using an ordinary branch/PR: it is linear, only 28 commits ahead of `origin/main`, and does not require rebase, force-push, or history rewrite.
- Live remote evidence shows only `origin/main`. Local persistence is therefore **not** GitHub delivery.
- The Git object pack is 515.07 MiB; the worktree is about 1.3 GiB. The largest tracked object is the 21,824,118-byte DM02 partial PDF. No tracked object reaches GitHub's 50 MiB warning threshold or 100 MiB hard block.
- GitHub currently recommends a 10 GB maximum on-disk repository size and enforces 100 MB per normal Git object; its separate large-file guidance recommends repositories ideally remain below 1 GB and strongly below 5 GB. The current 515 MiB `.git` directory is deliverable but merits growth control. See [Repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits) and [About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
- Git LFS is not installed/configured. It is **not necessary for the current push**, because all tracked objects are below the hard limit. It becomes prudent for future high-volume raster/PDF growth, but LFS has plan/storage/bandwidth implications and should be adopted deliberately; see [About Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).
- The original Satyanarayana and DM08 combined PDFs are intentionally ignored local reference binaries. Their hashes and extracted Gold Standard pages are tracked. DM08 remains `EXISTING_EDITION` and excluded from automatic production.
- Repository write permission, rulesets, and PR creation are **UNKNOWN** because no authenticated write action was allowed and GitHub CLI is absent. A future push may also encounter server-side policy not visible through read-only Git.

## 8. Minimum safe production policy

1. Keep `max_active_books=1`; treat historical run records as durable history, not live leases.
2. Select in order: valid resumable book, then source-ready catalogue priority, then stable book ID. Keep DM08 excluded unless explicitly requested.
3. Require one hash-bound **book-level private-production authorization** covering an exact unit list, built-in Codex provider, included-allowance-first policy, total/per-unit operation ceilings, and at most one review-directed repair per unit. A changed source, prompt, reference, provider, or cost policy invalidates it.
4. Let the factory execute routine artistic choices inside approved series conventions. Escalate only genuine source/iconography conflicts, new reference identities, publication rights, or budget expansion.
5. Require independent semantic QA of actual pixels; keep deterministic source, receipt, lettering, layout, and PDF checks in-repository.
6. Recover locally: re-letter/recompose without new pixels where honest; otherwise pause only the affected page/unit. Preserve every version and counter.
7. Persist one canonical projection of campaign, unit, review, composition, and invalidation state after every imported receipt. Resume from that projection, never from an older milestone report.
8. Skip or pause blocked units; complete other eligible work. A complete PDF requires every page gate; a partial proof must remain explicitly partial/private.
9. Continue automatically to the next source-ready book only while the same explicit book/collection authorization permits it. Otherwise stop at a new book-level approval request.
10. Private production never implies theological certification, rights clearance, or publication approval. Public publication remains a separate gate and implementation.

## 9. Go/no-go answers

1. **Is the engineering foundation complete enough for production use?** Yes for supervised, private, fail-closed production slices; no for the requested unattended factory.
2. **Can it produce one complete private book without manually coordinating specialist sessions?** No. Active Codex orchestration is still required, and real resume state is stale.
3. **Can it autonomously recover from ordinary failures?** It can autonomously recover lettering/layout/composition failures. New-pixel and semantic failures require the Codex host, approval scope, and independent review.
4. **Can it operate within one book-level authorization?** The approval model supports this, but only within immutable scope. DM02 now needs a new campaign because identity/reference requirements changed.
5. **Can it advance to the next eligible title without a manually authored prompt?** No: DM02 cannot complete from the CLI, and there is no fresh source-ready next title.
6. **What blocks reliable operation across 78 books?** Canonical-state divergence, no CLI-to-host director loop, 76 catalogue readiness blocks, external model/image/reviewer availability, and book-specific quality/publication gates.
7. **Smallest remaining implementation scope:** (a) reconcile actual immutable production records into the canonical state; (b) add one thin Codex-host execution loop over existing handoffs/state, not a new framework; (c) demonstrate it on one newly source-cleared book through a complete private PDF and automatic next-book selection.

### Final verdict: NO_GO

This is a **NO_GO for claiming or operating an autonomous 78-book factory today**. It is not a rejection of the foundation: the source, governance, receipt, composition, PDF, persistence, and fail-closed pieces are real and substantially tested. The no-go is narrow and operational: the actual state is not unified, the CLI cannot cross host boundaries, and the catalogue has no new eligible title.

## 10. Minimal next execution plan

1. Land a narrowly scoped state-reconciliation fix and a regression test using the real DM02 record chain. The corrected `status`, `resume`, and `produce-next` must agree on the latest campaign, later identity invalidation, exhausted/remaining budgets, and Page 11 gate.
2. Add the thin active-Codex director loop around existing handoffs. It must be idempotent, approval-aware, provider-aware, and receipt-importing; no new schemas, agent hierarchy, or provider are needed unless a concrete gap is proved.
3. Separately clear one non-DM08 catalogue title's source readiness, then run one bounded book-level private campaign end to end. Success criteria: complete inspected private PDF, durable restart from an induced interruption, no manual specialist coordination, and automatic selection (or valid approval stop) for the next eligible book.
4. Only after those criteria pass, push the existing linear chain to a review branch and open an ordinary PR after verifying GitHub write permission and repository rules. Keep public publishing out of that readiness claim.
