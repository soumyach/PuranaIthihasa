# Khatakshetra Book Factory — Foundation PR4 execution report

## 1. Branch and baseline

- Baseline: `1c63c9c6677250266ab9e62b3d8540012854c5fc` (Foundation PR3), verified before work began.
- Branch: `feature/book-factory-manuscript-pr4`.
- Delivery: one local commit containing this report and the PR4 implementation; no push or merge is part of this milestone.

## 2. Actual generation mechanism

The direct `manuscript_generation` and `editorial_review` provider adapters remain unavailable. PR4 does not claim otherwise. The Director now supports a locked-file handoff that the active Codex session can execute with specialist subagents:

1. The Director prepares a hash-bound request containing the exact book, dossier, Story Packet, required-event, source-policy and rules inputs.
2. A `manuscript-story` specialist produces a structured response.
3. The Director validates the handoff, zero-cost execution receipt, event coverage, evidence references and schemas before storing an immutable version.
4. A different `family-editor` specialist reviews the exact stored manuscript hash and Story Packet hash.
5. A `FIX` result produces a targeted, hash-bound revision request; revised manuscripts and rereviews form immutable parent chains.

The recorded mechanism is `CODEX_SPECIALIST_SUBAGENT_HANDOFF`. Execution used zero paid API calls and zero cost. Agent identity is an orchestrator-session attestation, explicitly labeled `ORCHESTRATOR_SESSION_RECORD_NOT_CRYPTOGRAPHIC_IDENTITY`; it is not represented as cryptographic identity proof or a programmatic repository-side agent spawn.

## 3. DM04 manuscript result

DM04 — *The Buffalo King: The Divine Mother and Mahishasura* — was generated as a complete private editorial draft. It is not a publication-ready edition.

- Manuscript v1 content hash: `7979c89ca4d7f227bfab91c42c9191b269502e457bdeb3dd08e4ccee2827c4ba`
- Manuscript v2 content hash: `40d02a77dedf68f8b9e216822293b8a5911ba9be8c644fe8ca6d434efbdba1fa`
- v2 parent: the v1 content hash above
- Creator: `codex-subagent:/root/dm04_manuscript_writer`
- Audience: shared family reading; independent reading for ages 10 and up
- Literary benchmark: the registered DM08 Manuscript v2 was used only as a quality reference. Its story was not reproduced.

Both versions remain under `books/DM04/manuscripts/` as structured JSON, rendered Markdown, event-coverage maps and claim-provenance maps.

## 4. Chapters and approximate word count

The final v2 contains nine chapters and approximately 2,700 words of chapter prose:

1. The Empty Thrones
2. Light Becomes a Warrior
3. The Roar Across the Worlds
4. An Army from Breath
5. The Last Commanders
6. The Buffalo Enters
7. The Shape That Could Not Escape
8. After the Thunder
9. After the Story

The manuscript includes the Medhas framing device, the gods' displacement, Devi's manifestation and arming, the army and commander battles, Mahishasura's transformations and death, the gods' attributed hymn, the narrow boon, Devi's disappearance, an editorially labeled reflection and a post-resolution next-volume connection.

## 5. Event coverage and provenance

Deterministic manuscript validation is `PASS` for v2.

- Required events covered: 16/16, `dm-event-008` through `dm-event-023`.
- Structured source claims: 39.
- Locked Story Packet: `b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744`.
- Every `MULA` or `SAMPRADAYA` claim is bound to a required event and evidence ID from that packet.
- Adaptation material is separately classified; dialogue records do not claim invented literary dialogue as verbatim scripture.
- Unsupported evidence IDs, valid evidence cited against the wrong event, unlocked canonical events, missing event coverage, missing chapter links and packet-hash mismatches fail deterministic validation.

## 6. Independent editorial review

The independent reviewer was `codex-subagent:/root/dm04_family_editor`, distinct from the manuscript writer. Each review is bound to the exact manuscript and packet hashes and evaluates all 11 required semantic dimensions.

Review v1 returned `FIX` with four evidence-linked findings:

- `SOURCE_BELL_EFFECT_EXCEEDS_LOCKED_EVIDENCE`
- `UNSUPPORTED_INTERIORITY_STRATEGY_AND_ADDED_ACTION`
- `IN_STORY_EDITORIAL_DISCLAIMERS_BREAK_IMMERSION`
- `TARGET_AGE_BAND_UNRESOLVED_FOR_BATTLE_CONTENT`

Its review hash is `7bc5d05d5d3e2ae0d7f6593dc0bd4ceac4d0df96feee321fae41815a7641ae32`.

Review v2 returned `PASS`: all four earlier findings are recorded as resolved, all 11 dimensions pass, all 16 source events have evidence checks, and no new findings remain. Its review hash is `d75c3da76b645f037cb7ab68413370c65ecb614ee43f336723ec46cc4b68117f`.

This PASS certifies manuscript editorial review only. It does not certify rights, source readiness, theological authority, visuals, PDF quality or publication readiness.

## 7. Revisions completed

The Director preserved v1 and created revision request `9a748c9a3ff3335065af029befb1f48641112ed7ff78442dd29cb7873e24c519`. The writer then produced v2 as a child of v1. The revision:

- limited the bell's effect to confounding the enemy;
- removed unsupported motives, private tactical reasoning and added actions;
- moved adaptation/source-process cautions out of the literary story body; and
- made the audience contract explicit for the retained, non-graphic battle content.

The original `FIX` review, targeted revision request, revised manuscript and final `PASS` review are all retained for audit.

## 8. Source and rights status

The DM04 dossier remains `BLOCKED`; PR4 did not rewrite it to `READY`. A separate source-clearance record opens only `PRIVATE_DRAFT_PERMITTED_PUBLICATION_BLOCKED` and is bound to the exact dossier, packet, source-graph and rules hashes.

The evidence record identifies F. Eden Pargiter's 1904 Calcutta edition, his 1927 death, the assessed Indian life-plus-60 term and the U.S. Copyright Office's source-country/URAA guidance. The working determination is that an original private English adaptation may be drafted from the locked graph paraphrases and locators. It is an evidence-based operational determination, not legal advice or worldwide publication clearance.

Modern Wisdomlib presentation/OCR and the SanskritDocuments transcription are excluded from reuse. Events 008–013 and 016–019 have packet cross-witness records; events 014–015 and 020–023 remain single-English-witness records. No critical-edition collation, blanket theological approval or exhaustive scripture-verification claim is made.

Source-clearance hash: `d43a5f725e4ea595f49a55411eb88af1c65c3d0ca6bf397fdef0d6b7c54f7c7c`.

## 9. Tests passed and blocked

Executed successfully:

- 60 Book Factory Python regression tests, covering PR1–PR4.
- 15 existing source-graph integrity tests.
- Existing source-graph structural validator.
- Book Factory schema/config/artifact validator.
- Scope, binary and source-graph boundary checks.
- Existing dependency-free `diag` and `drip` Node tests (28 assertions total).
- Python compile check for the complete `book_factory` package.

The two dependency-free Node suites required by the Book Factory CI pass. A broader probe of all `tests/*.test.mjs` found eight unrelated browser/UI suites blocked before execution because this checkout has no `jsdom` installation or Node dependency manifest; no dependency was installed or invented for PR4. Provider-backed illustration, visual evaluation, PDF generation, publication and deployment were intentionally not invoked because they are outside PR4 and remain unavailable or unauthorized.

## 10. Exact production-state result

`PRIVATE_MANUSCRIPT_EDITORIALLY_REVIEWED_PUBLICATION_BLOCKED`

The state dimensions remain separate:

| Dimension | Result |
| --- | --- |
| Source readiness | `BLOCKED` |
| Private draft gate | `PRIVATE_DRAFT_PERMITTED_PUBLICATION_BLOCKED` |
| Manuscript draft completion | `COMPLETE` |
| Independent editorial review | `PASS` |
| Visual production | `NOT_STARTED_PR4_BOUNDARY` |
| Publication readiness | `BLOCKED` |

The run remains at `EDITORIAL_QA`; `resume` returns the same final PR4 status without mutation.

## 11. Remaining technical and publication limitations

- Worldwide or target-market publication rights have not been cleared.
- Source extraction is complete for the bounded story chronology but atomically partial at chapter level.
- Independent full-arc scripture/theological approval is not established.
- Direct repository-side manuscript and editorial provider adapters remain unavailable; the supported mechanism requires active-session orchestration.
- Session agent identity is not cryptographically attested.
- No character/location bible, page script, storyboard, visual continuity pass, illustration, lettering, font package, PDF, visual QA or publication artifact exists for DM04.
- No approved paid provider, credential, quota, price schedule or cost-reconciliation ledger is configured.

DM08 remains `EXISTING_EDITION`, excluded from automatic production. Its registered reference hashes are unchanged, and no DM08 manuscript, handoff or run artifact was created by PR4.

## 12. Recommended PR5 scope

PR5 should begin visual pre-production without generating final illustrations or a PDF:

1. Resolve target-market publication-rights review and identify the authorized review owner.
2. Add independent full-arc source/theological review for the remaining single-witness and disputed details.
3. Create hash-bound DM04 character, manifestation, weapon/iconography, lion and location bibles.
4. Convert manuscript v2 into a complete page script/storyboard with event, claim and dialogue provenance retained at scene and page level.
5. Define page-count, aspect-ratio, typography, font-license, lettering and caption/dialogue-duplication gates.
6. Implement visual-provider capability, zero/approved-cost budget enforcement, identity/continuity tests and a bounded proof-review-repair loop.
7. Produce only a small style/character proof set after explicit visual approvals; keep full illustration, PDF production and publication for later authorized milestones.

The PR5 acceptance boundary should be `VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED`, not a finished or public book.
