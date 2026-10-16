# Khatakshetra Autonomous Book Factory — Foundation PR6

## Result

PR6 executed the four locked DM04 illustration-proof specifications through a real image backend and an independent actual-pixel review loop. It generated eight genuine PNGs: two attempts for each proof, the maximum permitted by policy. Every file passed deterministic integrity, hash, format, size, and aspect-ratio validation. Every latest image nevertheless received independent `FIX`.

The exact recorded status is:

`ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED`

The run remains at `ART_PROOFS`. It did not enter `AWAITING_STYLE_APPROVAL`, and no human approval is claimed.

## 1. Branch and baseline

- Branch: `feature/book-factory-illustration-proofs-pr6`
- Required and verified baseline: `2ee09d97379ccbee60264931f584ef71e701ff57`
- The local PR6 commit is reported at handoff because a commit cannot reliably contain its own final hash.
- Pre-existing Finder metadata changes at `.DS_Store`, `books/.DS_Store`, and `books/DM04/.DS_Store` remain unstaged and uncommitted.
- DM08 remains an immutable `EXISTING_EDITION`; no DM08 production artifact was created or changed.
- The source graph remained read-only at `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`.

## 2. Selected provider and model

The selected provider was the Codex built-in image-generation tool, exposed to this execution session through a host-injected adapter and durable file-handoff boundary.

- Provider ID: `codex-built-in-image-gen`
- Model: `NOT_SURFACED_BY_BUILTIN_TOOL`
- Operations: generation, editing, and reference conditioning
- Repository credential: none required for the built-in session tool
- Direct billable repository operation: no
- Actual cost: USD 0.00
- Native result for all eight calls: exact 1086 × 1448 PNG
- Availability scope: this PR6 Codex execution session only; it is not represented as a reusable repository credential

The OpenAI Image API was also inventoried, but `OPENAI_API_KEY` was absent and paid spend was unauthorized. No local diffusion runtime was detected. Neither fallback was invoked.

## 3. Executable production boundary

PR6 adds:

- a host-injected Codex native image adapter that fails closed when no executor is supplied;
- capability discovery with provider, operation, conditioning, dimensions, pricing, credentials, limits, integration, and executable-status evidence;
- intent-before-call JSON requests and an append-only generation ledger;
- operation-key replay protection, two attempts per proof, and eight attempts total;
- cost estimates and actual-cost receipts guarded by the checked-in zero-spend policy;
- PNG signature, chunk CRC, decompression, readability, dimension, aspect ratio, duplicate, and hash validation;
- controlled crop/resample into 1086 × 1448 without stretching when a provider result differs;
- immutable proof receipts and aggregate proof records;
- exact-image independent review handoffs across all 13 required dimensions;
- a self-contained SVG contact sheet embedding the latest real PNG pixels.

No response metadata alone can create a successful proof record.

## 4. Exact real images generated

Eight real images were generated and preserved. Four are latest representative proofs; four rejected first attempts remain immutable generation history.

| Proof | Attempt | SHA-256 | Repository path |
| --- | ---: | --- | --- |
| Quiet conversation | 1 | `f90ca2afd035933a462275ad0cd770f8fdac8fcf4fd91952ebe7dd7927d39a19` | `books/DM04/illustration-proofs/images/dm04-proof-quiet-conversation/attempt-01-f90ca2afd035933a.png` |
| Quiet conversation | 2 | `578e0fcdb4dcf016b7b85a50736e498859528560f569885ddf0f8060003f32fc` | `books/DM04/illustration-proofs/images/dm04-proof-quiet-conversation/attempt-02-578e0fcdb4dcf016.png` |
| Divine reveal | 1 | `19b0b1f7ff0d0e4f8b9b4087ccb35a875ef490c2980fd43292c3764d31266a54` | `books/DM04/illustration-proofs/images/dm04-proof-divine-reveal/attempt-01-19b0b1f7ff0d0e4f.png` |
| Divine reveal | 2 | `21af6bf894e1abc6d63f6d797ccebebda569e65f372658ff4cc126164f3a7139` | `books/DM04/illustration-proofs/images/dm04-proof-divine-reveal/attempt-02-21af6bf894e1abc6.png` |
| Battle | 1 | `42cfdd660d064fddb289c38f7f404ab0232ed1234f66ffa66dfdd8ae8c47ddef` | `books/DM04/illustration-proofs/images/dm04-proof-battle/attempt-01-42cfdd660d064fdd.png` |
| Battle | 2 | `016faa6b34b5c1addeffd634554015033c1dbacd0ba6718dba1c767a17f3a619` | `books/DM04/illustration-proofs/images/dm04-proof-battle/attempt-02-016faa6b34b5c1ad.png` |
| Full-page immersion | 1 | `3d5b13effd92448c4f1f93b14d1772c1eb2c3463cbd1984d41ff9f02ac9ffd2a` | `books/DM04/illustration-proofs/images/dm04-proof-full-page/attempt-01-3d5b13effd92448c.png` |
| Full-page immersion | 2 | `18f850fb0ba3accaf956cc7d74cec34af610e174b8f68890e1ebdf87e9b54d32` | `books/DM04/illustration-proofs/images/dm04-proof-full-page/attempt-02-18f850fb0ba3acca.png` |

All eight are 1086 × 1448, portrait 3:4, readable PNGs with `PASS_CRC_AND_PIXEL_STREAM`. Together they occupy 26,521,620 bytes; no individual asset approaches GitHub's normal per-file limit.

## 5. Character-consistency mechanism

The versioned DM04 character-reference registry contains 45 stable IDs. Every entry separates source-supported textual facts from proposed artistic choices and records authorized weapons, mounts, clothing, ornament, silhouette and arm-count policies, forbidden attributes, and continuity constraints.

No proof received a reusable image reference because no visual asset has human approval. Generation therefore used the exact text-bound registry with `TEXT_ONLY_PENDING_STYLE_APPROVAL`. The adapter supports reference conditioning, and an exact approved proof can be bound later without treating its religious or character decisions as transferable to unrelated subjects.

Continuity improved between attempts, but did not pass: the quiet scene removed Suratha's unauthorized sword; the divine and battle scenes still lost Devī's locked many-armed identity; and scene-specific equipment/action continuity remained incomplete.

## 6. Independent visual review

The reviewer was `/root/dm04_visual_preproduction`, distinct from producer `codex-native-image-tool`. Every verdict attests inspection of the exact image pixels and covers source fidelity, religious iconography, character identity, limbs, weapons/mounts, anatomy, composition, environment, crop/clip, lighting/color, series identity, scripted-page suitability, and lettering-safe regions.

Attempt one produced four `FIX` decisions. Their findings were persisted and inserted into the exact attempt-two requests. Attempt two also produced four `FIX` decisions:

- Quiet: the unauthorized sword was resolved; tree crowns still intrude into the exact top lettering-safe rectangle.
- Divine reveal: the donor/body stream map improved and the lion was removed; Devī is reduced to an ordinary two-arm form, unsourced halo disks and later-stage donor equipment/mounts remain, and the safe region is occupied.
- Battle: the disabled horses/driver and on-foot Cikṣura improved; opposing counter-arrows, broken bow/banner, Devī's many-armed identity, Cikṣura's full silhouette, and the safe region remain unresolved.
- Full-page: mouth emergence and hand anatomy improved; the sword is not making the sourced neck stroke, the neck pin is unclear, rejoicing gods and ridge anchor are absent, the treatment is too graphic, an unsourced halo remains, and the safe region is occupied.

No review is represented as human theological, iconographic, or style approval.

## 7. Cost and attempt controls

- Paid calls authorized: no
- Monetary cap: USD 0.00
- Actual total spending: USD 0.00
- Attempts: 8/8 total
- Per proof: 2/2
- Duplicate requests after interruption: prevented by durable operation keys
- Third attempt: rejected by policy

## 8. Contact sheet

- SVG: `books/DM04/illustration-proofs/contact-sheets/pr6-proof-contact-sheet.svg`
- Metadata: `books/DM04/illustration-proofs/contact-sheets/pr6-proof-contact-sheet.json`
- Contact-sheet SHA-256: `c5a14a3c41ed186bef03290d274d4b8ab117af46ddcf58048f79074d68612e95`
- Format: self-contained SVG with four embedded latest PNGs
- Included metadata: proof/page IDs, generation version, proof-spec hash, image hash, and exact `FIX` status

This is an internal review artifact, not a comic-book page.

## 9. Approval state

Current state: `ART_PROOFS`.

`prepare-style-approval` correctly fails with `style approval requires independent PASS review for every exact proof image`. Consequently:

- no style-approval request was persisted;
- no transition to `AWAITING_STYLE_APPROVAL` occurred;
- no proof or character image was marked approved;
- no inheritance path was opened.

This deliberately overrides the nominal deliverable of a persisted approval request because the stronger gate requires a passing package first.

## 10. Verification

- Python compilation: pass with a repository-local bytecode cache.
- Required PR6 acceptance suite: 16/16 pass.
- Full Book Factory Python suite: 86/86 pass.
- Existing source-graph integrity suite: 15/15 pass; standalone graph validator passes with no warnings.
- Factory schema/config/source validation: pass.
- Dependency-free CI Node suites: 2/2 suites pass (28 internal assertions).
- Broad Node discovery: 2 pass and 8 cannot start because the repository has no installed `jsdom` package; this is the unchanged pre-existing dependency blocker and PR6 adds no JavaScript dependency.
- Repository scope/binary boundary check: pass; the existing large DM08 reference remains correctly governed as local-only.
- Source graph: exact original graph hash retained.
- `git diff --check`: pass at final handoff.
- Style-approval negative gate: pass; the `FIX` package cannot advance.

Synthetic PNGs are used only inside validator unit tests. They were never substituted for production artwork.

## 11. Remaining blockers

1. All four latest proof images require repair, and the PR6 retry ceiling is exhausted.
2. A human decision is needed before changing provider/model, proof specification, safe-region strategy, or attempt budget.
3. The built-in image backend is session-scoped, not a reusable repository credential with provider-side recovery.
4. Worldwide or target-market publication rights are not cleared.
5. DM04 chapter extraction remains atomically partial; blanket independent full-arc source/theological approval is absent.
6. A redistributable font choice, trim, bleed, and export profile remain unresolved.
7. Full-book illustration, lettering, PDF assembly, deployment, and publication remain outside this milestone.

## 12. Recommended PR7

PR7 should be a bounded proof-repair decision milestone, not a 32-page production run. First obtain human direction on one of three paths: revise the locked composition specifications, select a more controllable/reference-capable provider, or explicitly authorize a fresh capped proof run. Before any new call, add visible machine-checkable safe-region overlays, split temporally dense battle beats into renderable single-frame requirements, strengthen many-arm/iconography controls, and define exact non-graphic thresholds. Only after four representative proofs independently pass should the system prepare an exact-asset human style-approval request.

Do not begin full-book illustration or PDF production in PR7 unless that approval is separately obtained.

## 13. Scope confirmation

PR6 did not generate the other 28 pages, generate a PDF, create or edit a manuscript, change DM08, change the source graph, deploy, publish, push, or merge.
