# Khatakshetra Autonomous Book Factory — Foundation PR5

## Result

Foundation PR5 completes the DM04 literary-quality revision, two-perspective independent review, and deterministic visual-preproduction milestone. The exact recorded state is:

`VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED`

This is a specification milestone. It does not claim that an image was rendered, visually inspected, approved, placed, typeset, exported to PDF, or made publication-ready.

## 1. Baseline and scope

- Branch: `feature/book-factory-visual-preproduction-pr5`
- Required PR4 baseline: `9dbb7225ca07b8f7d44a83cf6891a844385ab945`
- Pilot: DM04, *The Buffalo King*
- DM08 remains an `EXISTING_EDITION`; its registered manuscript and illustrated PDF were not regenerated or edited.
- The read-only source graph remains at `f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1`.
- No image, PDF, print file, publication action, or paid API call was produced by PR5.

Pre-existing Finder metadata changes (`.DS_Store`, `books/.DS_Store`, and `books/DM04/.DS_Store`) are unrelated to PR5 and are intentionally excluded from the commit.

## 2. Literary contract expansion

PR5 keeps the seven source-fidelity dimensions separate from six new literary dimensions:

1. `dramatic_scene_quality`
2. `character_engagement`
3. `emotional_rhythm`
4. `dialogue_quality`
5. `narrative_redundancy`
6. `visual_adaptability`

The executable review contract prevents a literary assessment from replacing source/theological checks. It also prevents the manuscript writer from self-certifying and requires distinct reviewers for the final source-fidelity and literary/family perspectives.

## 3. DM04 manuscript history

PR4 evidence remains immutable:

| Version | SHA-256 | Purpose |
| --- | --- | --- |
| v1 | `7979c89ca4d7f227bfab91c42c9191b269502e457bdeb3dd08e4ccee2827c4ba` | Original private draft |
| v2 | `40d02a77dedf68f8b9e216822293b8a5911ba9be8c644fe8ca6d434efbdba1fa` | PR4 reviewed manuscript and PR5 parent |

PR5 adds a parent-linked revision chain:

| Version | SHA-256 | Outcome |
| --- | --- | --- |
| v3 | `b4256fcb2d4bf24a9c04559f59c3f0985101ef42c6299392b159fba5e41cfdcd` | Full literary-quality revision preserving all 16 locked events; literary review found two issues |
| v4 | `23b478f91c17e3c9801784f0601077adea3076f4db917b0bbd95d4cbaf93ce38` | Removed in-scene meta-disclosure and redundant end recap; literary review passed; source review found four narrow fidelity defects |
| v5 | `25e25f0734d50c4d109ebf00d3bafb5b6abc9f0043c9951c38821743ff5a45f6` | Restored exact source bounds for offices/jurisdictions, noose/form transition, arrows, and the decisive beheading mechanism |

The bounded repairs after v3 are intentional immutable QA revisions, not a replacement of the requested v3 milestone. Every version retains claim provenance, event coverage, parent hash, creator attestation, locked packet hash, and source-clearance hash.

## 4. Independent review result

The final v5 manuscript passed both required perspectives:

- Source/theology: `PASS`, all seven dimensions and all 16 event checks; review hash `c05ba53f995882cdf3287ed38c33708e0e673ea04c85819ec9d627f388447a6d`.
- Literary/family: `PASS`, all source dimensions plus the literary experience dimensions; review hash `fc45110ca23273f9991a3d42b8c03273dcb8fb6d49cf41d7b605c02b179cf884`.

The final reviewers have different identities from the manuscript writer and from each other. Visual preproduction is gated on both reviews passing for the exact latest manuscript hash.

## 5. Character and location bibles

The versioned DM04 visual bible contains:

- 45 stable character entries, covering Devī, Mahiṣāsura, Devī's lion, the divine assembly, radiance contributors and divine donors, the two armies, the principal commanders and named chiefs, Medhas, Suratha, and Samādhi.
- Five separate Mahiṣāsura manifestation IDs: buffalo, lion, armed man, elephant, and half-emerged Asura.
- Per-character evidence, source scope, authoritative source record, explicitly proposed visual interpretation, required/prohibited attributes, arm/clothing/ornament/silhouette policies, authorized weapons, and continuity checks.
- Seven location entries: forest hermitage, displaced heaven, gods' gathering, manifestation space, battlefield, direct-confrontation space, and thanksgiving.
- Per-location source facts and separately labeled production proposals, palette, lighting, spatial anchors, prohibited features, and continuity checks.

Validators reject duplicate character, location, or manifestation IDs and reject a manifestation ID merged across different characters.

## 6. Storyboard and page scripts

The complete storyboard has 32 contiguous, deterministically identified pages and covers all 16 locked events from `dm-event-008` through `dm-event-023`.

- Required visual moments placed: 12/12.
- Full-page immersive scenes: pages 4, 9, 14, 23, 29, and 30.
- Page rhythm varies between one, two, and three panels.
- Each page contains exact editable lettering, source-claim links, character/location references, explicit reading order, panel count, continuity in/out, image instructions, safe regions, and validation requirements.
- Dialogue and thought require a known speaker ID.
- Narration/dialogue duplication is rejected deterministically.
- Weapons and manifestations are checked against the active character bible.
- Artwork and lettering remain separate; no text is requested inside generated artwork.

Each 32-page storyboard revision stores immutable page scripts separately, preserving the reviewed history while supporting later page-level rendering and retry.

## 7. Format and typography

- Canvas: exact `3:4`, `1086 × 1448` pixels.
- Palette: exact `#071F35`, `#D8AC4E`, `#F0CF76`, `#F6E8C6`, `#FFF9EF`, `#251C18`, `#692019`.
- Text channels: narration, dialogue, thought, and inset explanation.
- Candidate local fonts inspected: New York, Georgia, and Charter.
- Font files are recorded as system-installed candidates only. No bundling or redistribution right is inferred.
- Print readiness remains blocked until a redistributable font decision, trim, bleed, and export profile are approved.

## 8. Proof specifications and semantic review seam

Exactly four versioned proof specifications exist:

1. quiet conversation
2. divine reveal
3. battle
4. full-page immersion

Each binds the current manuscript and storyboard, 3:4 canvas, source boundaries, character IDs, setting, iconography, exclusions, safe regions, and the two-attempt retry policy.

All four are `SPEC_READY_PROVIDER_BLOCKED`. Their attempt lists and approval records are empty. The semantic visual-review interface requires iconographic accuracy, hands/anatomy, character continuity, facial consistency, scene correctness, clipped-artwork inspection, and lettering readability, but records `executed: false` because no rendered images or visual-evaluation backend exist.

An independent art/iconography specialist reviewed the preproduction specifications themselves. Two `FIX` passes caught and corrected generic panels, donor/equipment attribution, the thousand-arm image, battle action mappings, ending coverage, and typography status; the exact final package then received `PASS`. This specification review is not represented as semantic review of images.

## 9. Deterministic controls added

- Version stores for character bibles, location bibles, storyboards, typography, proof specifications, and preproduction reviews.
- A `VISUAL_PREPRODUCTION` handoff capability with locked manuscript, dossier, rules, packet, and review hashes.
- Current-manuscript and storyboard binding across every preproduction component.
- Immutable proof attempts with on-disk image/hash verification, explicit rejection records, and a maximum of two attempts.
- Approval validation bound to exact proof ID, proof-spec hash, package version, and rendered evidence; blocked-provider packages cannot contain approvals.
- Idempotent import and resume behavior.
- State progression through `EDITORIAL_QA → STORYBOARD → CHARACTER_BIBLE → ART_PROOFS` without advancing to layout, PDF, or publication.

## 10. Verification

- Python compilation: pass.
- Book Factory unit/acceptance suite: 70/70 pass.
- Repository Book Factory validation: pass.
- Source graph hash and DM08 no-regeneration assertions: pass.
- `git diff --check`: pass.
- Broad JavaScript tests: two suites pass, while eight unrelated browser-oriented suites cannot start because the repository has no installed `jsdom` dependency. PR5 does not add or change JavaScript runtime dependencies.

## 11. Precise blockers

1. Worldwide or target-market publication rights are not cleared.
2. DM04 chapter extraction remains atomically partial.
3. Independent full-arc source/theological publication approval is not established.
4. No image-generation provider is configured.
5. No rendered proofs exist, so semantic visual review cannot execute.
6. Font licensing/redistribution selection is pending.
7. Trim, bleed, and export profile are unspecified.
8. Full illustration, PDF generation, and publication are outside PR5.

## 12. Recommended PR6

Configure one approved image provider and one semantic visual-review backend, then render only the four proof specifications. Enforce exact image hashes, at most two attempts per proof, independent semantic review across all required visual dimensions, and approval records bound to the exact proof and character scope. Do not begin the remaining 32-page illustration run until all four proofs pass and the font/license/print-format decisions are resolved.
