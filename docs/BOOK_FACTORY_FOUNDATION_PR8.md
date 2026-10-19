# Khatakshetra Autonomous Book Factory — Foundation PR8

## Result

PR8 implements an executable, deterministic comic-page composition, lettering and digital-reader PDF layer without generating story art. The authoritative artifact is editable JSON. Rendered PNGs and the PDF are hash-bound derivatives. A four-page synthetic technical demonstration is explicitly publication-ineligible and is not a DM04 edition.

## 1. Baseline and scope

- Branch: `feature/book-factory-page-engine-pr8`
- Required and verified baseline: `41d8cc3fbcc6755d4984a46a4f49570d01d6cf24`
- The local PR8 commit is reported at handoff because a commit cannot contain its own final hash.
- Preserved and uncommitted: `.DS_Store`, `books/.DS_Store`, `books/DM04/.DS_Store`.
- DM08 remains an immutable `EXISTING_EDITION` and is rejected by the production page-engine gate.
- The source graph remains read-only.
- No AI image generation, paid provider call, manuscript creation, final DM04 book, publication, deployment, push or merge occurred.

## 2. Rendering implementation

The engine uses:

- Pillow for deterministic RGB page rasterization, font measurement, wrapping and aspect-preserving image crops.
- ReportLab for reproducible digital-reader PDF assembly (`invariant=1`) with one native 1086 × 1448 raster per PDF page.
- pypdf for PDF page, media-box, embedded-image and pixel inspection.
- Poppler for an independent render-to-PNG inspection of the demonstration PDF.

The page canvas is 1086 × 1448 with the required navy, gold, parchment, speech-white, ink and burgundy palette. Frames, borders, corner ornaments, panel geometry, narration plaques, speech balloons, thought balloons, source-note insets and footers are drawn independently of the image assets.

## 3. Supported layouts

The reusable templates are:

1. `TWO_PANEL_SEQUENTIAL`
2. `THREE_PANEL`
3. `FOUR_PANEL_GRID`
4. `MIXED_WIDE_NARROW`
5. `CINEMATIC_HERO`
6. `SINGLE_PANEL_IMMERSIVE`
7. `QUIET_NEAR_SILENT`
8. `COVER`
9. `REFLECTION_SOURCE_NOTE`
10. `TWO_PAGE_SPREAD`

Templates supply default geometry but page scripts may provide bounded overrides. Reading order and panel IDs remain explicit. A spread is composed as a 2172 × 1448 editable/raster surface; a production book must define an explicit split or a uniform landscape reader profile before PDF export, so PR8 does not silently mix it into the portrait profile.

## 4. Editable lettering and typography

Every lettering object retains its stable ID, exact text, speaker/narrator, panel, channel, reading order, normalized box, font settings and source-script hash. Supported channels are numbered narration, dialogue, thought and expository/source inset.

Line breaking uses measured glyph bounds. The renderer may reduce text only to the configured minimum; it never edits the words. Overflow returns `FIX` and requires a layout, panel or page revision. Speaker tails require one supplied, in-panel anchor for the exact speaker, and an anchor hidden inside its own balloon is rejected.

`book-factory/config/page-renderer-fonts.json` is the font and license audit. STIXGeneral is preferred and is not copied from the system. The ReportLab-distributed Bitstream Vera family is the legal operational fallback. The exact resolved files and hashes are recorded in each composition. Font presence is not treated as publication clearance, and the fallback is not represented as the preferred final devotional typography.

## 5. Image preservation and approvals

Images are immutable path/hash references. Placement uses a computed aspect-preserving cover crop around an explicit normalized focal point; images are never stretched. Source dimensions, crop bounds, scale mode and focal point are recorded per panel.

Production requires an exact hash-bound `APPROVED` asset record plus approved manuscript, storyboard and series-standard gates. The rejected PR6 images are covered by a negative gate test and cannot be used as production art. Semantic crop safety—faces, limbs, divine hands, weapons and essential action—remains pending until an image-capable reviewer inspects actual pixels.

## 6. Page QA and repair

Deterministic validation covers page/panel/lettering identity and order, panel counts, exact text hashes, speakers and anchors, narration sequence, files and hashes, image readability and resolution, focal bounds, font availability, minimum size, overflow, lettering collisions, geometry bounds, fixture isolation, approvals, duplicate pages, PDF ordering, count, dimensions, orientation and embedded pixel identity.

`repair_page` permits bounded changes to panel, crop, lettering or layout records while retaining book, manuscript, storyboard, page and order identities. It records parent composition hash, changed fields, failure causes and retry number. `PageCompositionVersionStore` and `PdfArtifactVersionStore` provide immutable parent-linked production records. A page repair cannot change the locked narrative.

## 7. Lifecycle and CLI

The new commands are:

- `compose-page`
- `validate-page`
- `compose-book`
- `export-pdf`
- `inspect-pdf`
- `resume-layout`

Production `compose-book` requires `LETTERING` and advances to `PDF_LAYOUT` only after every page passes deterministic QA. Production `export-pdf` requires `PDF_LAYOUT` and advances to `VISUAL_QA` only after PDF inspection passes. `inspect-pdf` never advances to `READY_FOR_PUBLICATION`; semantic visual review remains a separate blocking gate.

Fixture mode is explicitly isolated, accepts only `SYNTHETIC_TEST_ONLY` assets, forces `publication_eligible: false`, cannot mutate production state and cannot be promoted by `resume-layout`.

## 8. Technical demonstration

The committed fixture contains:

- one dialogue-heavy two-panel page;
- one asymmetric mixed-panel action page;
- one full-page immersive page;
- one reflection/source-note page;
- one four-page digital reader PDF.

Every page visibly says `NON-PRODUCTION RENDERER TEST`; every source image visibly says `SYNTHETIC NON-PRODUCTION FIXTURE`. The geometry was generated locally with Pillow. No image model or benchmark page was used.

The PDF metadata title is `KHATAKSHETRA BOOK FACTORY — NON-PRODUCTION RENDERER TEST`. It contains four portrait pages, each 1086 × 1448 points, with one 1086 × 1448 embedded RGB raster whose decoded pixel hash matches the composed PNG. There is no white surround, rotation, extra page, duplicate or print-readiness claim.

## 9. Validation evidence

- PR8 acceptance suite: 27/27 targeted tests covering all 25 requested categories and actual rendering of every layout family.
- Full Book Factory Python suite: 131/131 pass.
- Existing source-graph integrity suite: 15/15 pass; standalone graph validation passes with no warnings.
- `factory validate`: pass, including four exact fixture pages, PDF embedded-pixel identity and the unchanged PR7 package.
- Boundary check: pass; both large reference PDFs retain their governed local-only status.
- Existing dependency-free JavaScript CI: 2/2 suites pass (28 internal assertions).
- Python compilation and `git diff --check`: pass.
- The demonstration PDF was independently rendered with Poppler and all four rendered pages were visually inspected for clipping, order, page labels and obvious technical layout defects.
- The artifact marker helper requested by the PDF workflow was not present in this repository or surrounding Codex workspace; the required command was attempted once before artifact authoring and failed with `MODULE_NOT_FOUND`. PDF construction and verification proceeded with the documented local toolchain.

## 10. Honest limitations and blockers

1. No approved DM04 scene-image set exists; all four latest PR6 proofs remain `FIX` and retry-exhausted.
2. Semantic judgments—iconography, cultural authenticity, depicted action, character continuity, composition, crop safety and illustration artifacts—cannot be certified deterministically.
3. A production font package, final devotional family, target-market license review, trim, bleed, DPI and color profile are unresolved. Print export remains unavailable.
4. Two-page spreads need an explicitly approved split or uniform landscape digital-reader profile before PDF assembly.
5. DM04 source and publication blockers from PR7 remain unchanged.
6. No automatic transition to publication exists.

## 11. Recommended PR9

PR9 should implement bounded end-to-end orchestration over already approved inputs: a page-asset approval registry, independently reviewed semantic visual reports bound to exact pixels and crops, restart-safe per-page job scheduling, page-local repair routing, explicit spread-splitting policy, and a release-candidate gate that can move `VISUAL_QA` to `READY_FOR_PUBLICATION` only when every deterministic and semantic requirement passes. It should first use synthetic fixtures and then a separately authorized, fully approved small real-page set. It must not reopen PR6 retries, invent approvals, select a print profile, or publish anything automatically.

Stop after PR8.
