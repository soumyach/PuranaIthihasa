# DM02 resumable production checkpoint

Status: **AWAITING_CAMPAIGN_AUTHORIZATION**

Branch: `feature/book-factory-dm02-corrective-proofs`

Verified baseline: `7335973fa9f7e3a3104d388b060ec565807a57d1`

No model-generated illustration was created or edited; one deterministic composed-page preview was rendered from existing art. No approval record was created. No prior campaign counter was reset. DM04, DM08 and the source graph were not modified.

## 1. Page 11 gate

Page 11 (`page-b85332e92940926f67e6dd9d`, `p11-panel-01`) remains **ESCALATE_BEFORE_GENERATION**.

- The qualified human review template remains unsigned.
- Brahma, Vishnu, Shesha and Yoganidra convention records remain `PROPOSED` / `UNAPPROVED`.
- Page 11 is excluded from the next campaign.
- No existing Page 11 pixels were modified, approved, composed or promoted.
- Minimum Page 11 resume gate: a genuine qualified religious-iconography reviewer must sign an exact-scope decision; a separate fresh image authorization is still required afterward.

## 2. Remaining-unit classification

The locked storyboard has 44 panel units. The exact per-unit table is in `books/DM02/resumable-production/unit-readiness.v0001.json`.

| Classification | Count |
|---|---:|
| `ELIGIBLE_FOR_PRIVATE_ILLUSTRATION` | 0 |
| `ELIGIBLE_FOR_COMPOSITION_WITH_EXISTING_ART` | 3 |
| `REQUIRES_CAMPAIGN_AUTHORIZATION` | 4 |
| `REQUIRES_NEW_CHARACTER_REFERENCE` | 15 |
| `REQUIRES_SOURCE_OR_ICONOGRAPHY_REVIEW` | 13 |
| `BLOCKED_OTHER` | 9 |

Eligible or campaign-ready: **7/44**. Blocked before any new image execution: **37/44**.

`BLOCKED_OTHER` includes future reframes whose master does not yet exist and the two deterministic back-matter units for which the current composer still requires a non-fixture raster base. No renderer framework was added to work around that production limitation.

## 3. Selected four-operation batch

The lowest-risk contiguous batch completes the missing Page 1 view, Page 2's transition, and Page 3's environment-only establishment.

| Order | Unit | Action | Method | References | Retry |
|---:|---|---|---|---|---:|
| 1 | Page 1 `p01-panel-02` | Medium Medhas speaker view with both listeners | New 1086×1448 reference-conditioned generation | PR7 A/B plus existing Page 1 proposal-level continuity candidate | 0 |
| 2 | Page 2 `p02-panel-01` | Medhas hand, low fire and non-supernatural smoke transition | New 1086×1448 reference-conditioned generation | PR7 A/B plus existing Page 1 proposal-level continuity candidate | 0 |
| 3 | Page 2 `p02-panel-02` | Three neutral silhouettes and dark transition field | New 1086×1448 reference-conditioned generation | PR7 A/B plus existing Page 1 proposal-level continuity candidate | 0 |
| 4 | Page 3 `p03-panel-01` | Horizonless dissolution water with no ordinary landmark | New 1086×1448 reference-conditioned generation | PR7 A/B; no character reference; locked location bible only | 0 |

The Page 1 proof is not mislabeled as a canonical role-C or role-D asset. It is supplied only as a reviewed, proposal-level supporting continuity candidate. Each operation has an exact prompt hash, input path/hash/role list, source event, action, output size, private-clearance boundary and independent actual-pixel review criteria in the campaign request.

## 4. Authorization boundary

Exact campaign subject:

`820c1d0371f19ec0e44a5000c3012f29aab1e05501802ef324078841657211cd`

The request is non-inheritable and limited to four one-shot operations with zero retries. It requires built-in Codex image generation, included-allowance-first handling, exact reference receipts, independent actual-pixel review, no API key, no external provider, no intentional purchased-credit use, no automatic purchase or workspace overage, and zero authorized paid spend.

Observable allowance at preparation time: ordinary Codex usage allowed, 3% of the exposed 10,080-minute window used, purchased-credit balance `0`, and spend control not reported reached. Per-image allowance deduction and future incremental USD remain **UNKNOWN / not exposed**, so zero incremental USD is not claimed.

No approval record exists for this subject and `image_operations_executed` remains `0`.

## 5. Existing-page composition

The corrected PASS-reviewed Page 21 art was composed with the exact locked two-paragraph narration:

`books/DM02/private-page-previews/page-8619f3db280abbfd867eefe4/v0001/0021-page-8619f3db280abbfd867eefe4.png`

- PNG SHA-256: `868041b7cffb9fb9daf11f439bafc5af5ac74f2df0425d165630a58373341534`
- Composition hash: `bc61b13df29fb36f41cf0b2766f5ea52ae9ac828d872a44ba9ff9cd6adff8f74`
- Exact text rendered at 25 px; minimum 22 px; no overflow.
- Lettering does not cover any face, the discus, the action, or the earth/flood distinction.
- The source master retains its independent actual-pixel PASS.
- New composition QA is honestly recorded as `PASS_TECHNICAL_PENDING_INDEPENDENT_COMPOSITION_SEMANTIC_REVIEW`, because the composer did not self-issue an independent semantic approval.
- The preview is visibly labeled internal and remains publication-ineligible.

The pre-existing Page 1 preview remains a partial diagnostic only: its second crop does not replace the missing distinct `p01-panel-02` master. Page 14 has only one of three masters and was not represented as a complete page.

## 6. Private-book progress

- Complete rendered private page candidates from reusable art: **1/24** (Page 21; 4.17%).
- Partial diagnostic private pages: **1/24** (Page 1).
- Existing-art panel units eligible for private composition: **3/44** (6.82%).
- Additional panel units ready after exact campaign authorization: **4/44** (9.09%).
- Publication-ready pages: **0**.
- Full-book PDF: blocked until complete-book gates pass.

There are no approved canonical exact-pixel character references. Page 1, Page 14 and corrected Page 21 remain explicitly scoped proposal/reuse candidates and were not promoted.

## 7. Validation

- Source graph structural validator: PASS, 0 errors, 0 warnings.
- Source graph integrity suite: 15/15 PASS.
- Book Factory unit suite: 227/227 PASS.
- Full factory validation through the bundled workspace Python/Pillow runtime: PASS.
- Page 21 deterministic composition validation: PASS.
- Campaign invariants: PASS (44 classified units; four exact operations; zero retries; zero executed; all prompt, reference and subject hashes recomputed).

The system `./factory validate` interpreter lacks Pillow in this checkout, so it correctly failed closed on that local dependency. Running the same Book Factory interface through the app's bundled Python runtime, which supplied Pillow, passed.

## 8. Next resumable checkpoint

The authorized human user must explicitly approve subject `820c1d0371f19ec0e44a5000c3012f29aab1e05501802ef324078841657211cd` through the existing authenticated approval mechanism. Only after a matching non-inheritable approval record exists may the four listed one-shot operations run.

Page 11 proceeds on its separate qualified-review track and is not unblocked by authorizing this batch.
