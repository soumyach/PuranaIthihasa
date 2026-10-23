# DM02 Pages 1-3 production campaign

## Outcome

Campaign `820c1d0371f19ec0e44a5000c3012f29aab1e05501802ef324078841657211cd` executed exactly four built-in Codex image operations, one for each authorized unit, with zero retries. Independent actual-pixel review returned two PASS and two FIX results. Page 3 is the only completed private-preview page among Pages 1-3. Pages 1 and 2 remain incomplete rather than concealing source or anatomy defects.

- Branch: `feature/book-factory-dm02-production-unblocking`
- Verified baseline: `975e350bc26ce85bb8a3a3531d4df51459fca81d`
- Approval record: `books/DM02/approvals/approval-d50a10509141390a31d41cdb.json`
- Independent four-image review: `books/DM02/pages-1-3-production/independent-visual-review.v0001.json`
- Durable status: `books/DM02/pages-1-3-production/status.v0001.json`

## Authorization and execution

The human user directly authorized the exact campaign subject through the current authenticated session. The approval is non-inheritable and permits only the four named units. Execution used the built-in Codex image-generation tool; no API key, external provider, paid third-party workflow, retry, additional unit, or Page 11 operation was used. No explicit payment authorization was requested by the tool.

| Page/panel | Operation | Output SHA-256 | Independent result | Private composition |
| --- | --- | --- | --- | --- |
| 1 / `p01-panel-02` | 1 of 1 | `582196a26f1dafa22a669ccfc2f126af1edeb53f3f7c8c01ba47a6702e4972c2` | FIX | No |
| 2 / `p02-panel-01` | 1 of 1 | `7702fbc90c1d03295ccb7628281e5f3026d634a714daba1c00cea73db85cede4` | FIX | No |
| 2 / `p02-panel-02` | 1 of 1 | `6a74cd64078d324d3d6e6abfdb8b573034f8d9a829b6d0b227bb02eeada5fa17` | PASS | Yes |
| 3 / `p03-panel-01` | 1 of 1 | `8c5e72bf52d71d13997af976c3f7d43917802b8bcd91506d35495031bdf3e86a` | PASS | Yes |

Every output is 1086x1448. Each provider receipt records the exact submitted A/B/C reference paths, SHA-256 hashes, roles, prompt hash, built-in provider, immutable output path and output hash. Reference C remains proposal-level continuity input and was not promoted to a canonical identity.

## Review findings

`p01-panel-02` otherwise communicates Medhas teaching Suratha and Samadhi clearly, but Medhas carries a prominent white/orange forehead tilak or sectarian mark that neither the locked source nor the character bible authorized and that the prompt explicitly excluded. Honest repair requires new corrected pixels; cropping would remove the teaching action or a required character.

`p02-panel-01` otherwise passes source, iconography, cultural, lighting and composition checks, but its focal hand has one thumb plus five non-thumb digit tips. Because the hand is the visual action, the defect cannot be cropped away truthfully. It requires new corrected pixels.

`p02-panel-02` passes as a quiet forest transition and `p03-panel-01` passes as horizonless dissolution water without unsupported geography, figures or cosmographic symbols. These passes authorize only private composition; they do not approve canonical character or environment references.

## Composition and private PDF

Page 3 was composed with its exact locked narration and a navy/gold frame. Its first layout was preserved as a FIX version after independent review found an unnecessarily tall plaque. A composition-only v2 reduced the plaque to 890x152 without changing the generated artwork, wording, 22 px font, badge or crop. Independent actual-pixel review passed v2.

- Page 3 PNG: `books/DM02/private-page-previews/page-a694d4c3702975edfdceb0c5/v0002/0003-page-a694d4c3702975edfdceb0c5.png`
- PNG SHA-256: `e2f4eb52be5d3579f4a8dfc3658a75f9b1abcfdbbc98d5e097228ec6062f636d`
- Independent review: `books/DM02/private-page-previews/page-a694d4c3702975edfdceb0c5/v0002/0003-page-a694d4c3702975edfdceb0c5.independent-visual-review.json`
- One-page private proof: `books/DM02/pages-1-3-production/pdf-proof/dm02-pages-1-3-private-proof.pdf`
- PDF SHA-256: `805e857b3d2ee9afe185401eff1ff2009036dfa6159fe46cb1f0f3b2ff51295e`

The PDF contains only the eligible Page 3 raster, at native 1086x1448 portrait dimensions, and visibly states `INTERNAL PREVIEW — NOT APPROVED FOR PUBLICATION`. Deterministic inspection found one page, one full-page raster and the expected page ID; a fresh 72-DPI render was also visually inspected and showed no clipping, overlap, malformed text, border collision or scaling defect. It is not a complete-book or Pages 1-3 proof.

## Character continuity

The forest ensemble remains proposal-only. The usable observations are Medhas as the central bark-brown/warm-ivory teacher, Suratha in peacock blue, and Samadhi in restrained earth tones. The unsupported Medhas forehead mark and the malformed focal hand are explicitly excluded from reusable reference traits. No generated asset was promoted as a canonical exact-pixel reference.

## Usage and cost

The observable account-wide Codex meter moved from 14% to 16% used in the 10,080-minute window during the bounded four-operation campaign, leaving 84% shown. Purchased-credit balance was `0` both before and after, ordinary usage remained allowed, and no explicit payment prompt appeared. The interface exposes neither per-image allowance deduction nor incremental USD, so the two-point aggregate change cannot be attributed exclusively or evenly to these images. Incremental USD remains `UNKNOWN_NOT_EXPOSED`; zero incremental USD is not positively verified.

## Validation and preservation

- Factory validation: PASS.
- Page 3 deterministic validation: PASS; semantic pixel gate satisfied separately by the persisted independent PASS review.
- Private PDF deterministic inspection and rendered visual inspection: PASS.
- Book Factory suite: 228/228 PASS.
- Read-only source-graph structural validation: PASS with 0 errors and 0 warnings.
- Read-only source-graph integrity suite: 15/15 PASS.
- Page 11 remains `ESCALATE_BEFORE_GENERATION`; its qualified form is unsigned.
- DM04, DM08, the source graph, original art, prior counters and unrelated `.DS_Store` changes were not modified.
- No publication, deployment, push or merge occurred.

## Next resumable checkpoint

A separate exact, hash-bound corrective campaign is required for two operations: remove only the unsupported Medhas forehead mark from `p01-panel-02`, and reconstruct only the malformed focal hand in `p02-panel-01` with one thumb and four fingers. Neither operation is authorized by this completed campaign. If both future outputs pass independent review, compose Pages 1 and 2 and update the private Pages 1-3 proof. Page 11 remains on its separate qualified-review path.
