# DM02 Brahma/Vishnu Series-Identity Review — Execution Report v0001

## Outcome

The current DM02 Brahma and Vishnu depictions are not coherent enough to serve as series references. Brahma usually reads as a generic single-faced elderly sage. Vishnu changes face, crown, hair, arm count, complexion, forehead mark, and costume treatment between repose, awakening, and battle. Page 11 briefly introduces a different four-arm/multi-face solution, but that proof is already blocked and does not establish a canonical identity.

This review proposes one consistent identity for each deity, preserves every prior image and review, and classifies all 41 affected raw raster versions. It does not generate, edit, approve, or promote pixels.

## Execution facts

- Baseline verified: `d1e59f36d1a9449cebf00aa9ccd2440245090054`.
- Branch verified: `feature/book-factory-dm02-production-unblocking`.
- Actual-pixel inspection: 41 immutable raster versions, 33 panel IDs, Pages 4–21.
- Image generation/edit operations: 0.
- New campaign or authorization record: none.
- Existing campaign counters/budgets changed: none.
- Source graph, manuscript, storyboard, Story Packet, character bible, DM04, and DM08 changed: none.
- Page 11 status: remains `ESCALATE_BEFORE_GENERATION`; its unsigned human-review decision remains unsigned.
- Publication, deployment, push, or merge: none.

Because the request did not identify the “two latest user-flagged images” by path or hash, no pair was guessed. The audit included every raw Brahma/Vishnu image and every latest panel version, so no repository image in scope was omitted.

## Validation

- `git diff --check`: passed.
- Inventory extraction: exactly 41 distinct raw asset paths.
- SHA-256 replay: all 41 inventory hashes match the preserved files.
- `./factory validate`: could not complete because the current environment lacks the declared Pillow dependency; the command returned `BLOCKED` before contract/source-graph validation. No package installation was attempted and no factory state was changed.

## Evidence read

| Input | SHA-256 / role |
|---|---|
| `books/DM02/story-packets/b7986e36746d67a2dc29b48db194ccd62845c09385603778c7357cb159c4bdfd.json` | `63195c77c26e324af9809f1cfde80131108d655b550ce137115e3337b3f84e84`; locked source and Story Packet evidence. |
| `books/DM02/source-clearance/483cc82d41b142878778e107deabd090ec623ccf4a48410b28d80a3c95f1213e.json` | `ddbbe4485c890408bb4a8f4a51c5e5490ebcf5e6e7b8a412ac5af6c11b539763`; existing clearance boundary. |
| `books/DM02/character-bibles/v0001.json` | `e15e42cb62fd2c17715d1acfcf95b09d7210bebb1afe4b7a06e0fb41b4cdc791`; existing character facts and deliberate visual uncertainty. |
| `books/DM02/storyboards/v0002.json` | `2ffc82651274e049bf8b20c270f5abde63841fb2abc40137d935b956990069f6`; exact affected panels and actions. |
| `books/DM02/iconography-review/page-0011/review-package.v0001.md` | `eaf85bd69d564a8bf2cac8fa09979fcadf4e417ee8546d606ad61d2a89031cae`; Page 11 textual floor and human-review boundary. |
| `books/DM02/iconography-review/page-0011/attribute-matrix.v0001.json` | `0d8e1a9833ebd0f1bfea33ac527fdde32953cbaef90992a42ce537c76f08eab5`; direct text versus tradition classifications. |
| `books/DM02/iconography-review/page-0011/proposed-visual-conventions.v0001.json` | `6a141167a9187665be79f8d78bd052eb19a9919f44a15d81d72c6cc8b238b3ec`; prior proposals, still unapproved. |
| `books/DM02/book-level-production/reviews/campaign-image-reviews.v0001.json` | `efb24d2ecdbe176e22324d4e9cfe7bbce13fe3b3adada0796c55385a49bb2dbf`; operation-level actual-pixel reviews. |
| `books/DM02/visual-proof-campaign/review-responses/p11-panel-01.v0001.json` | `50573743c45a03dd717602ef01d62bedf7510f04b0f652383f90d57d6fdf7473`; Page 11 `ESCALATE` evidence. |
| `books/DM02/visual-proof-campaign/review-responses/p14-panel-01.v0001.json` | `4c48f3887d5a4ff7dc83ebb00490aaee96fb0a222be76e18aa8a9cb0cf1ae01c`; Page 14 proof limits. |
| `books/DM02/visual-proof-campaign/review-responses/p21-panel-01.v0001.json` | `44fd37da737b2641f59f865ceb22afb4733f710f548466ee5913016f45a36bfe`; first Page 21 proof defects. |
| `books/DM02/corrective-proof-campaign/review-responses/p21-panel-01.v0002.json` | `64d0255a46745a5758dc6304a1c6d4c389b72d3bd1958ed8e15264e92c97b8e9`; corrected Page 21 source/action PASS with explicit noncanonical scope. |
| `MYTHOLOGY_COMIC_RULES.md` | `0f47a1bb48b3b85c7442d67e51398a6a5fe0e379790a09ed0d852d4d3ab65070`; fidelity, continuity, and human-review policy. |

## Direct requirements versus tradition

The locked DM02 evidence directly requires the narrative relationships and actions: Vishnu sleeping on Shesha under Yoganidra; Brahma on the lotus from Vishnu's navel; Brahma's appeal; the six Page 11 withdrawal loci; Vishnu's awakening; the long arm-to-arm battle; the condition involving unflooded earth; and the Page 21 discus consequence.

The locked passage does **not** directly specify Brahma's head/arm count, Vishnu's arm count/crown/garment colors, or an exact number of Shesha hoods. Museum records nevertheless document durable recognition conventions:

- The Met documents four-faced/four-armed Brahma and an Indian sculpture in which three of Brahma's four heads are visible.
- Cleveland documents Brahma on the lotus from Vishnu's navel in two Anantashayana works.
- Cleveland's Pahari *Vishnu Battles Madhu and Kaitabha* shows a four-armed Vishnu newly awakened on a multiheaded serpent in the same narrative cycle.
- The Met documents Vishnu's tall crown, four-arm structure, long garland, and recurring attribute family.

Those museum records support a coherent series convention; they do not convert visual tradition into a falsely quoted scriptural requirement. Regional differences in complexion, emblems, dress, and hood count were retained as evidence of variation.

## Proposed series identities

### Brahma

The preferred proposal uses four faces total, normally showing three and implying the fourth behind; four arms; a shared low gold diadem; white beard on each visible face; warm copper-gold complexion; crimson, saffron, and ivory garments; and stable ornaments. The front hands perform the scene action while the rear hands carry a small rosary and water vessel as non-narrative traditional identifiers. The navel-lotus stem must remain continuous whenever its origin is shown. Hamsa, books, additional implements, temples, and thrones remain excluded.

This solves the “generic elderly sage” problem without claiming that the locked DM02 passage mandates the chosen counts or attributes.

### Vishnu

The preferred proposal uses one stable youthful-adult face, deep divine-blue complexion, shoulder-length black hair, one unchanged tall gold `kirita-mukuta`, a restrained pale-gold U-shaped forehead mark, four arms, yellow pitambara, teal-green uttariya, and a fixed ornament set across sleep, awakening, dialogue, and battle. The sourced discus appears only where the event authorizes it; conch, mace, lotus, and other implements remain withheld from this DM02 proposal. Shesha is multihooded but count-neutral, using overlapping/partially occluded hoods instead of asserting five, seven, or another exact number.

All of these are proposals awaiting human approval. No prior pixel is promoted as the face or body reference.

## Correction inventory

The exact file paths, hashes, reviews, reasons, and page list are in `affected-illustration-inventory.v0001.md`.

- 8 superseded versions: preserve as immutable audit history.
- 20 current panels: candidates for localized character-region replacement while retaining usable action/environment pixels.
- 12 current panels: full regeneration required because identity changes are composition-wide or existing source/action blockers remain.
- Page 11: full regeneration required only after the existing qualified-review gate is cleared.
- 0 current complete Brahma/Vishnu rasters: eligible for unchanged canonical/final reuse.

The localized classification does not authorize an edit and does not promise that a future edit tool will preserve the background cleanly. A later campaign must treat each as a bounded candidate and independently review the resulting pixels.

## Approval boundary and next action

No theology or human approval is recorded. The two approval sheets are deliberately `PROPOSED_AWAITING_HUMAN_APPROVAL` and contain explicit checkboxes for decisions that the project cannot self-certify.

The minimum next action is human review of both identity sheets. If approved, the factory may prepare—but not execute without the applicable authenticated campaign authorization—a new correction plan using the affected-page inventory. Page 11 remains excluded until its separate qualified-review form is signed; approving either character sheet must not be interpreted as clearing its six-locus Yoganidra scene.
