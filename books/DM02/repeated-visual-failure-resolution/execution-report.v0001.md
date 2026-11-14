# DM02 Page 4–5 repeated visual failure resolution

Baseline: `main` at `174f492f55f17907e802cea245d92519f6f11ae3`.

This is a versioned reassessment. It does not rewrite any historical review, approval, image, hash, campaign counter or production state. No image operation ran and no source pixels were modified.

## Finding

The repeated blocker was mixed.

- **Genuine defect:** every reviewed Vishnu has exactly three visually accountable arms. The existing arms are anatomically coherent, but no image supplies a fourth shoulder/arm contour, hand, negative-space path or crop-based evidence that supports an invisible fourth. This conflicts with the human-approved DM02 private-production four-arm artistic convention; it is not a direct DM02 textual requirement or theological ruling.
- **Overly rigid findings:** all four Shesha canopies are recognizable, overlapping and multihooded. An approximate count is not, by itself, a defect because no exact hood count is fixed. Likewise, exact lettering fits without reserving the complete suggested top band.

## Four-image decision table

| Image | Independent result | Arms/anatomy | Shesha | Exact remaining correction | Production decision |
|---|---|---|---|---|---|
| Page 4 v0003 (`95e4af8…`) | `FIX` | Three accountable arms; shown limbs coherent | Pass; countability is noncritical | Deepen complexion, clarify fourth arm, soften mildly halo-like glow | Preserve as superseded history |
| Page 4 v0004 (`05c7786…`) | `FIX` | Three accountable arms; no plausible fourth-arm occlusion; shown limbs coherent | Pass; recognizable and overlapping | One localized fourth-arm clarification/addition | `LOCAL_IMAGE_EDIT_REQUIRED` |
| Page 5 v0003 (`431b379…`) | `FIX` | Three accountable arms; shown limbs coherent | Pass; countability is noncritical | Deepen complexion, clarify fourth arm, integrate Brahma's diadem | Preserve as superseded history |
| Page 5 v0004 (`f774f11…`) | `FIX` | Three accountable arms; no plausible fourth-arm occlusion; shown limbs coherent | Pass; recognizable and overlapping | One localized fourth-arm edit preserving the navel-lotus connection | `LOCAL_IMAGE_EDIT_REQUIRED` plus composition repair |

No image has fused, duplicated or serpent-merged limbs. No whole-scene regeneration is justified. Page 5 v0004 otherwise passes the approved Brahma identity and preserves a continuous, unambiguous navel-lotus connection.

## Lettering tests

The repository's deterministic composer rendered every exact Page 4 and Page 5 narration block at the 22-pixel minimum with no overflow.

- Page 4 diagnostic preview: independent composition `PASS`. The two plaques avoid Vishnu's face, crown and hands; the repose and Shesha support remain legible. This proves the fixed empty top band is unnecessary.
- Page 5 diagnostic preview: deterministic `PASS`, independent composition `FIX`. The main panel preserves the complete sacred relationship and all lettering is readable, but the secondary Brahma crop still hides front hands/most of the lotus and the closing crop needs a stronger water strip without the lotus fragment. Both findings are crop/plaque repairs using existing pixels, not new-art requirements.

These previews remain internal diagnostics. Neither page is art-approved because the fourth-arm defect remains.

## Production recommendation

- Page 4: retain v0004 and perform one localized fourth-arm edit.
- Page 5: retain v0004, perform one localized fourth-arm edit that does not disturb the stem/navel relation, then finish the secondary crop/plaque geometry with the deterministic composer.
- Qualified theological review: not required for these two corrections.
- Regeneration: not required.
- Pages fully recoverable without new pixels: zero.
- Pages whose lettering/layout is recoverable without new pixels: Pages 4 and 5.
- Effective private-complete count: unchanged at 5 of 24 (`2, 3, 22, 23, 24`). Diagnostic layouts do not promote a page.

The minimum corrective image budget is two operations, one localized edit per v0004 master. The affected units already exhausted their two-operation ceilings. The stopped campaign's numeric remainder—30 primary, seven fallback ceiling, five repair ceiling, 42 total ceiling—is preserved and frozen, not available for these edits.

## Resume checkpoint

Create a new exact hash-bound two-operation authorization for the two localized edits. After those pixels receive independent `PASS`, finish Page 5's composition-only crop repair and independently review both final pages. Do not reuse or reset the stopped campaign, and do not touch Page 11.

Validation completed: factory/source integrity `PASS`; both final diagnostic compositions deterministic `PASS`; 241 Book Factory tests `OK`. Page 11 remains `ESCALATE_BEFORE_GENERATION`; DM04, DM08, the source graph and manuscript remain unchanged. Nothing was published, deployed, pushed or merged.
