# DM02 production-unblocking report

Status: **AWAITING_CAMPAIGN_AUTHORIZATION**

Branch: `feature/book-factory-dm02-production-unblocking`

Verified baseline: `a10196aecf8744cf43db296849f3d1ac5df59d90`

No illustration was generated or edited. No paid provider was called, no approval was fabricated, no campaign counter was reset, no PDF was produced, and nothing was published, deployed, pushed or merged. Page 11 remains `ESCALATE_BEFORE_GENERATION`.

## 1. Dependency audit outcome

The locked storyboard contains **44 panel units**: 35 distinct raster masters, 7 derived reframes and 2 deterministic back-matter units.

| Classification | Before | Revised |
|---|---:|---:|
| `ELIGIBLE_FOR_COMPOSITION_WITH_EXISTING_ART` | 3 | 3 |
| `REQUIRES_CAMPAIGN_AUTHORIZATION` | 4 | 38 |
| `REQUIRES_NEW_CHARACTER_REFERENCE` | 15 | 0 |
| `REQUIRES_SOURCE_OR_ICONOGRAPHY_REVIEW` | 13 | 1 |
| `BLOCKED_OTHER` | 9 | 2 |

The apparent change to 38 authorization rows does not mean 38 image operations. It consists of **31 missing raster masters** that may proceed as production images or noncanonical reference proofs under exact campaign authorization, plus **7 zero-operation reframes** whose current primary dependency is authorization and successful review of their future master.

The previous matrix conflated final canonical reference approval with permission to prepare a private reference proof. It also counted seven future crops as seven independent blockers. The corrected sequencing is:

`PROPOSED_CHARACTER_REFERENCE` → `REFERENCE_PROOF_ELIGIBLE` → `APPROVED_CHARACTER_REFERENCE` → `PRODUCTION_IMAGE_ELIGIBLE` → `PUBLICATION_APPROVED`.

No DM02 asset is currently an approved canonical character reference or publication-approved image.

## 2. Genuine shared decisions

The 15 character-reference rows reduce to **three reusable ensemble decisions**:

1. Medhas, Suratha and Samadhi in the forest frame.
2. Vishnu, Madhu and Kaitabha in the combat sequence.
3. Vishnu, Brahma, Yoganidra and Shesha in the sacred repose/invocation sequence.

The task brief says “seven characters” but names nine identities; all nine are retained in the package.

The 13 source/iconography rows reduce to **two genuinely independent qualified decisions**:

1. A reusable, count-neutral sacred-ensemble convention for the DM02 Chapter 1 scene family.
2. The Page 11 six-locus visual grammar and sequence.

Because the sacred-ensemble decision overlaps the third character-reference decision, the total is **four distinct human decisions**, not five and not 28 panel-level decisions. Page 11 is the only unit that remains a hard source/iconography stop before generation.

## 3. Existing-art reuse

- Page 1 `p01-panel-01`, SHA-256 `3a51c5ab75ba4833bd66331cf038394cfd414de864fef8996b03d10a44e86a27`: private composition and proposal continuity only. It cannot substitute for the distinct `p01-panel-02` master.
- Page 14 `p14-panel-01`, SHA-256 `c3cf653e36e0d03a0d9b126ffeab56bee0b655ba752d8d988d9d057f8354170c`: private composition and proposal combat continuity only. The gold backlight is not an approved halo or sacred trait.
- Corrected Page 21 `p21-panel-01`, SHA-256 `c2289c8e85a02071388af597d25b17cde29b8f9a4b139f9e423676e9fb8ad65d`: reusable for private Page 21 composition. It remains noncanonical.
- Original Page 11, SHA-256 `aa2104618b9f4395c1f62cdba279974f5be3a38b4ff78242182cc9d13438fa6c`: preserved but excluded from source-valid composition/reference use.
- Original Page 21, SHA-256 `e7de39593aa71644f4c2a57fd577855a8611b2a0c8015b78497d84ecb759dbee`: preserved but excluded because layout cannot remove its invented island geography or anatomical impact claims.

All exact reuse scopes and withheld promotions are recorded in `books/DM02/production-unblocking/reuse-decisions.v0001.json`.

## 4. Page 21 layout repair

Final private preview:

`books/DM02/private-page-previews/page-8619f3db280abbfd867eefe4/v0004/0021-page-8619f3db280abbfd867eefe4.png`

- PNG SHA-256: `33658c7df3f95991d573919045902ee33032f930529433ca276379fec40e4f6f`
- Composition hash: `d8409815c910cf69180af050e55fc6d33f192cfa8685f96e57252bccb2d03bc9`
- Exact two-paragraph narration retained.
- Rendered STIX body text: 22 px, at the configured floor, `overflow=false`.
- Plaque: 848×181 = 153,488 px², **10.354% smaller** than v0001’s 171,216 px².
- Source art pixels were not modified.
- Deterministic page validation: PASS.
- Independent actual-pixel review: PASS. Badge clearance, faces, full discus/action, recoil, flood horizon, unflooded-earth plane, crop integrity, artifact absence and private label all passed.
- Publication eligibility remains false; no character or setting reference was promoted.

The only compositor change was a bounded `padding` option for lettering objects, validated as an integer from 8–60 px and recorded in render metadata. Engine version is now 0.8.2. This was necessary to correct the demonstrated plaque-padding defect without changing artwork or wording.

## 5. Page 11 preservation

Page 11 remains `ESCALATE_BEFORE_GENERATION`.

- The six source-named groups remain eyes, mouth, nose, arms, heart and breast.
- The existing proof does not make those six groups independently auditable.
- Brahma head/arm counts, Shesha hood count, Vishnu arm/crown/ornament treatment and Yoganidra’s exact body/radiance treatment remain source-silent choices.
- The qualified decision template is unsigned.
- No image operation, approval, composition, promotion or publication action was performed.

The consolidated human questions are in `books/DM02/production-unblocking/iconography-decision-questions.v0001.md`. The existing Page 11 template may resolve only the Page 11 decision; it must not be silently broadened to the full scene family.

## 6. Next campaign

The existing request remains the best next batch and was not replaced or modified:

`820c1d0371f19ec0e44a5000c3012f29aab1e05501802ef324078841657211cd`

It covers one operation each for `p01-panel-02`, `p02-panel-01`, `p02-panel-02` and `p03-panel-01`, with zero retries. It is contiguous, would complete Pages 1–3 if all outputs pass, exercises both frame continuity and an environment-only page, and has no Page 11 or sacred-iconography dependency. It remains `AWAITING_CAMPAIGN_AUTHORIZATION`; no approval record exists and zero operations were executed.

## 7. Practical completion budget

- Existing reusable private masters: **3 of 35**.
- Confirmed minimum remaining first-attempt image operations: **32**—31 currently source-bounded candidates plus one Page 11 correction after qualified clearance and fresh authorization.
- Derived reframes: **7**, requiring no extra operation if their masters support truthful crops and each derived crop passes actual-pixel review.
- Conditional extra image operations: up to **7** if any shared master cannot truthfully support its locked reframe; retries beyond first attempts are unknown and require new exact authorization.
- Currently authorized retry operations: **0**.

Private-book progress remains one complete page candidate (Page 21) plus one partial diagnostic page (Page 1) out of 24. No full-book PDF is allowed.

Minimum route to a complete private PDF:

1. Authorize and execute the unchanged four-operation Pages 1–3 batch; independently review every output.
2. Obtain the two ordinary ensemble continuity decisions and the two qualified sacred/iconography decisions; Page 11 stays separate until signed.
3. Authorize bounded later batches for the remaining missing masters; use proof-first status where final reference approval is pending.
4. Review every master and every derived crop; compose exact locked lettering without promoting proposal pixels.
5. Add one minimal deterministic assetless back-matter path for Pages 23–24, or supply separately approved non-fixture base assets.
6. Assemble and inspect the full private PDF only after all 24 private page gates pass. Publication remains a separate process.

No further coding is needed to execute the next image campaign. One small composer capability remains necessary before an art-complete private book can include Pages 23 and 24.

## 8. Validation and preservation

- Source graph structural validator: PASS, 0 errors, 0 warnings.
- Source graph integrity: 15/15 PASS.
- Book Factory tests: 228/228 PASS.
- Full `book_factory validate`: PASS.
- Page 21 deterministic validation: PASS; the engine’s generic semantic result correctly remains ESCALATE and is resolved for this exact PNG by the separate independent actual-pixel PASS.
- Source graph SHA-256 manifest remains `49d3e44643d028b64250656cfda4fd76b4d667184548737832380bf6a9e6870c`.
- Prior proof, corrective and full-book campaign status hashes remain unchanged.
- Unrelated `.DS_Store` changes were preserved and excluded from the commit.
