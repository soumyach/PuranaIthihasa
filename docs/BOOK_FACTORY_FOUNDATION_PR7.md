# Khatakshetra Autonomous Book Factory — Foundation PR7

## Result

PR7 reconstructs the strongest reusable visual-production lessons from the two registered benchmark editions without regenerating either edition. It creates an eight-page, provenance-bound Khatakshetra Visual Gold Standard; diagnoses the real PR6 execution path; compares all eight real DM04 proof images against actual reference pages; implements reference-first, cultural-authenticity, iconography, production-unit, lettering, and comparative-review contracts; and stores exactly four non-executable DM04 recovery requests.

The exact recorded outcome is:

`VISUAL_BENCHMARK_COMPLETE_RECOVERY_REQUESTS_PREPARED_GENERATION_NOT_AUTHORIZED`

No new image was generated or edited. No paid provider call, manuscript rewrite, page composition, PDF, DM08 production artifact, source-graph edit, publication, deployment, push, or merge occurred.

## 1. Branch and baseline

- Branch: `feature/book-factory-visual-benchmark-pr7`
- Required and verified baseline: `3baf3d92cc5b18f9527ca417bf4c71c56772462e`
- The final local PR7 commit is reported at handoff because a commit cannot contain its own final hash.
- Pre-existing `.DS_Store`, `books/.DS_Store`, and `books/DM04/.DS_Store` changes remain unstaged and uncommitted.
- Source graph: unchanged at `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`.
- DM08 remains an `EXISTING_EDITION`, excluded from automatic production.

## 2. Exact references and selected pages

Both local ignored PDFs were verified before benchmark-dependent work:

- Satyanarayana PDF: SHA-256 `82ae125d099ef2608adad705922567df6b553db40dd39af64b77c5de28dcadd2`, 7 pages, 8,222,659 bytes.
- DM08 PDF: SHA-256 `3867fccdd8c8755d27ff06c7543d8002cefb7531c1d4f39c743a43bff9c4a29f`, 30 pages, 122,897,487 bytes.

All pages of both PDFs were rendered and surveyed. The following eight actual pages were selected:

| Reference | Source PDF page | SHA-256 | Why selected |
| --- | ---: | --- | --- |
| `kgs-satya-p01` | 1 | `15c2cfaf37a379c8042105051ac432e3aba5ccc0594eef43dc95d157cee53a1b` | Cover and series identity: devotional hierarchy, layered depth, navy/gold framing, restrained title system. |
| `kgs-satya-p02` | 2 | `a0fa07b60d1b8b128b541300f3fb5e26358863e3153c719e2d0aacb0fd7858dd` | Conversation and sequential rhythm: assembly, question, response, close exchange, and distinct lettering roles. |
| `kgs-satya-p04` | 4 | `9b15d37505c7fcbecac144d031af2e52ed09c95d7e5e4f637abb800f2a66da2a` | Human interaction and Indian setting: village/home detail, gesture, family response, and ritual resolution. |
| `kgs-satya-p06` | 6 | `5f04b00c646e5c15d42b86cfd05ce36716b0bc6b2bf4c63be3b243118f64d985` | Emotional continuity across places: grief, prayer, release, storm, and reverent closure. |
| `kgs-dm08-p09` | 9 | `26f5a3d7fdc9c9432f0a793c6b50711a2bb4b1157cde79a7534c542a6c9bfa2d` | Intimate negotiation: speaker/listener staging, reaction close-ups, and a visible emotional turn. |
| `kgs-dm08-p12` | 12 | `d46f264508cf0283e56f14d1a02b6d66b37a49b8e2e66c7b3f31f16764fadfe4` | Divine manifestation and action: approach, emotion, reveal, and consequence separated into legible beats. |
| `kgs-dm08-p21` | 21 | `332b208d14df3d94139a3ab598e7e7e327e49bc9d4bbf5f41ddf20d8260291af` | Large battle storytelling: entrance, causal mechanism, narrator interpretation, and new clash. |
| `kgs-dm08-p28` | 28 | `7c57ff55122e1054aa36cc9c4a122c9c9245a71152068da3b0b6b2dd02f9fdb5` | Climactic page: action, completion, relief, and human aftermath in one coherent page system. |

The manifest records qualities to preserve and shortcomings not to copy. Examples of the latter include dense text, facial drift, generalized architecture or equipment, unsupported demonic-face flags, graphic battle treatment, and crowded limbs/weapons. The references are presentation references, not source authority and not blanket religious or historical approval.

The source PDFs remain ignored local files. `scripts/extract_visual_gold_standard.py` verifies their hashes and reproducibly extracts only these pages with Poppler at 72 dpi; no oversized Git blob was added.

## 3. Verified PR6 quality-gap diagnosis

The diagnosis inspected all eight requests, eight receipts, eight images, eight visual reviews, 16 ledger events, provider metadata, and the eight Gold Standard pages.

Verified findings:

- Every PR6 request had `reference_image_paths=[]`; no successful older page, character image, or setting image was supplied.
- Every call used `operation=generate`; reference conditioning and local editing did not execute.
- The character registry was `TEXT_ONLY_PENDING_STYLE_APPROVAL`, with no human-approved exact image asset.
- PR6 lacked a curated page manifest and role-aware reference package.
- Requests targeted one 1086×1448 portrait illustration using page-level narrative beats; they did not carry selected panel geometry and reading order. Only the full-page proof naturally matched that production unit.
- The earlier visual identity was represented only by a repeated textual style description. The provider never saw its page rhythm, expressions, panels, or lettering hierarchy.
- PR6 visual QA did not bind or compare exact reference-page IDs, paths, hashes, or a side-by-side artifact.
- All outputs were genuine readable 1086×1448 PNGs. Receipt normalization was `IDENTITY_COPY`, so later cropping or resizing did not create the composition gap.

Likely causes, explicitly not represented as proven model behavior:

- Long page-level prompts with many subjects, weapons, exclusions, and multiple temporal clauses encouraged emblematic poster composition.
- The common instruction to avoid an “extra limb” conflicted with a required many-armed Devī identity.
- The page 17 request combined the counter-arrow exchange with later equipment-loss consequences that the storyboard had separated into two panels.
- A uniform top-safe-region request encouraged blank-sky layouts without first designing the exact page lettering, and still failed to preserve exact geometry.

The largest gap is methodological: PR6 optimized one ornate painting per proof, while the benchmark books achieve storybook quality through changing shot scale, reactions, panel-to-panel causality, emotional staging, environmental continuity, and exact lettering hierarchy.

## 4. Unknowns and unsupported capabilities

- Model identity is unknown: PR6 records `NOT_SURFACED_BY_BUILTIN_TOOL`.
- Provider seed, internal model revision, sampling controls, safety transformations, and detailed conditioning behavior were not surfaced.
- Capability metadata declares generate, edit, and reference conditioning, but PR6 did not exercise edit or reference inputs. Future availability and exact behavior remain unproven.
- The repository cannot independently invoke the session-scoped built-in tool; it still requires a host-injected execution boundary.
- Deterministic code cannot judge emotional expressiveness, complex religious iconography, or cultural authenticity from pixels. Those decisions require an independent image-capable reviewer.
- There is no evidence that Codex used an inferior image model, so PR7 makes no such claim.

## 5. New reference-first generation method

Each future scene package separates:

- Reference A — series visual identity.
- Reference B — relevant page/panel composition.
- Reference C — human-approved character identity, if one exists.
- Reference D — approved setting/environment, if one exists.
- New story specification — only the current DM04 event, characters, source-supported facts, and approved artistic proposals.
- Exclusion rules — benchmark characters, deities, theology, plot, weapons, mounts, flags, dialogue, and other content that must not transfer.

The workflow resolves source and iconography first, selects exact role-labeled references, states one principal action, uses only participating identities, chooses composition and production unit, adds essential Indian conventions and critical exclusions, and keeps provenance/hashes outside the concise visual prompt. When the backend cannot prove image conditioning, the workflow must report that honestly rather than imply it occurred.

The unit is explicit:

- `CHARACTER_REFERENCE`: one controlled approved identity asset.
- `PANEL_ILLUSTRATION`: one narrative moment for a known panel, reading order, and lettering geometry.
- `FULL_PAGE_IMMERSIVE`: one uninterrupted major emotional, divine, or climactic composition selected by the storyboard.

Clean artwork contains no permanent dialogue or captions. Panel geometry, exact text, safe regions, speaker-tail anchors, framing, and crop priority are separate structured records. Full-page art is judged against its actual locked text, not an arbitrary generic blank mask.

## 6. Cultural and iconographic corrections

The reusable authenticity policy covers deities, manifestations, kings, courts, sages, devotees, Asura rulers and commanders, soldiers, helmets, crowns, garments, jewelry, shields, weapons, architecture, flags, mounts, animals, and environments. Every decision is one of `SOURCE_REQUIRED`, `TRADITION_SUPPORTED`, `ARTISTICALLY_APPROVED`, `SOURCE_SILENT`, or `FORBIDDEN`.

It does not invent one supposedly canonical Indian or Asura uniform. Source-silent proposals require review. Unless a separately reviewed setting authorizes them, the policy excludes Greek Corinthian, Roman/Hellenistic crested, Trojan/Spartan/Odyssey, European medieval plate, Viking, generic Western fantasy, RPG demonic equipment, unsupported flag emblems, and imported European castles.

Two PR6 pixel findings are now explicit `FORBIDDEN` DM04 failures:

- Attempt-one battle: red-crested Greco-Roman-looking helmet.
- Attempt-one battle: demonic-face flag emblem without demonstrated source support.

Devī requirements preserve event-appropriate many-armed identity, coherent anatomy, recognizable authorized weapons, Indian clothing/ornament, and event-correct lion continuity without unrelated goddess attributes. Mahiṣāsura is bound to the ordered buffalo → lion → armed human → elephant → returning buffalo → half-emergence sequence. Sequential transformations stay in separate panels; the source story is not changed to accommodate the image model.

## 7. Findings from all eight PR6 images

| Proof | Attempt | Exact pixel findings |
| --- | ---: | --- |
| Quiet conversation | 1 | Coherent intimate triangle and emotion, but an unauthorized sword, generic listening tableau, no scripted reaction panel, and occupied lettering region. |
| Quiet conversation | 2 | Sword corrected and figures remain expressive; still a single portrait tableau with excessive blank sky, no speaker/reaction rhythm, and no exact tail geometry. |
| Divine reveal | 1 | Ornate many-armed devotional poster, but body formation is conflated with later weapons, lion, and assembly; donor-to-body mapping, anatomy, and narration space are unclear. |
| Divine reveal | 2 | Clearer radiance mapping and central hierarchy; Devī becomes incorrectly fixed two-armed, later mounts/equipment and halo disks remain, donors are cropped, and exact narration is unplanned. |
| Battle | 1 | Spectacular but contradictory; counter-volley and ordered consequences are unclear, arms/weapons crowd, and the explicit Greco-Roman helmet plus demonic-face flag fail authenticity. |
| Battle | 2 | Removes those two explicit failures and improves defeated-chariot state; still merges cause/consequence, lacks opposing arrows, keeps bow/banner intact, reduces Devī to two arms, adds source-silent halo/flag, and does not fit the horizontal panel. |
| Decisive victory | 1 | Cinematic but generic; merged forms, unrelated lion/troops, dense armory, and unclear neck pin/trident/sword mechanism obscure the source event. |
| Decisive victory | 2 | Half-emergence and trident contact improve; sword goes toward the mouth rather than neck, foot pins the head rather than clear neck, gods/ridge are absent, halo and graphic red neck treatment remain, and exact narration geometry is crossed. |

The side-by-side artifact contains four rows of Gold Standard / attempt one / attempt two evidence and is not a claim of automated aesthetic measurement.

## 8. Four prepared recovery requests

All requests preserve manuscript, dossier, Story Packet, storyboard, character/location bible, proof-package, character-registry, rules, source-graph, parent request, latest image, and latest review hashes. They use role C only as a text-bound unavailable placeholder because no human-approved exact DM04 identity image exists.

| Proof | Recommendation | Unit | A — identity | B — composition | D — setting |
| --- | --- | --- | --- | --- | --- |
| Medhas, Suratha, Samādhi | `LOCAL_EDIT` | `PANEL_ILLUSTRATION` | `kgs-satya-p01` | `kgs-dm08-p09` | `kgs-satya-p02` |
| Devī from gathered radiance | `REGENERATE` | `FULL_PAGE_IMMERSIVE` | `kgs-satya-p01` | `kgs-dm08-p12` | no approved exact image |
| Cikṣura counter-arrow scene | `REGENERATE` | `PANEL_ILLUSTRATION` | `kgs-satya-p01` | `kgs-dm08-p21` | `kgs-dm08-p12` |
| Decisive victory | `REGENERATE` | `FULL_PAGE_IMMERSIVE` | `kgs-satya-p01` | `kgs-dm08-p28` | `kgs-dm08-p21` |

Each request contains one action, current-scene character IDs, exact reference hashes, cultural and iconographic constraints, composition goal, lettering key, prohibited transfers, and all eleven review dimensions. `generation_authorized` is false at campaign and request level.

## 9. Validation

- New PR7 acceptance suite: 18/18 pass using the real PDFs, extracted page pixels, all eight PR6 pixels, real ledger, and exact version records.
- Full Book Factory Python suite: 104/104 pass.
- `./factory validate`: pass, including all PR7 contracts, schemas, version chain, source graph, existing reference editions, and all eight PR6 receipts.
- Strict local benchmark verification with both source PDFs: pass.
- Source graph: no diff and exact original hash retained.
- Generation ledger: still 16 events, comprising eight intents and eight successful imports; no PR7 generation event exists.

## 10. Suggested PR8 recovery budget

PR7 recommends, but does not authorize:

- Maximum local edits: 1.
- Maximum full regenerations: 3.
- Maximum total image operations: 4.
- Maximum operations per proof: 1.
- Paid calls: disabled; maximum authorized paid spend: USD 0.00.
- Expected future cost: unknown until a PR8 capability and price recheck. PR6's USD 0.00 direct cost does not prove future price or availability.

PR8 would require explicit campaign approval, a fresh provider capability record, approval of exact request/reference hashes, and fresh priced authorization before any billable call. Stop after one operation for a proof, any stale binding, inability to prove submitted reference inputs, prohibited content transfer, forbidden cultural element, or `FIX`/`ESCALATE` in source fidelity, religious iconography, or cultural authenticity.

## 11. Remaining blockers

1. PR6 retry exhaustion remains intact; PR7 did not create a third-attempt loophole.
2. No DM04 character image has human exact-asset approval.
3. Future built-in tool availability, model identity, conditioning behavior, and cost remain unknown.
4. Worldwide or target-market DM04 publication rights are not cleared.
5. DM04 source extraction remains atomically partial; blanket full-arc theological approval is absent.
6. Human theological/iconographic reviewer identities are not configured.
7. A redistributable font, trim, bleed, export profile, final page composition, and actual-reading-size QA remain unresolved.
8. Full-book illustration, PDF assembly, deployment, and publication remain out of scope.

## 12. Backend recommendation

Do not abandon the current Codex image backend solely from the PR6 results; the evidence does not isolate the model from the flawed reference delivery and unit/prompt methodology. For PR8, first run the four-operation recovery canary on the current backend only if it can durably prove the exact role-labeled image inputs and operation type. In parallel or before authorization, capability-test one alternative reference-capable/edit-capable backend against the same locked request schema, rights constraints, cost cap, and independent review rubric. Select by controlled evidence—reference adherence, source/iconography accuracy, panel suitability, character consistency, recoverability, price, and rights—not by provider name or subjective reputation.

Stop after PR7. Do not automatically proceed to PR8.
