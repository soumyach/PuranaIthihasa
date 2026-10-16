# Portable source graph contract

Version 0.1.0. UTF-8 JSON; globally unique string IDs across record tables. References remain IDs rather than embedded duplicate records. `source_registry.json`, `source_coverage.json`, `extraction_queue.json` and `verification_report.json` are objects; the other graph tables are arrays. The Python validator is the executable integrity contract.

| Table | Required interpretation and key links |
| --- | --- |
| sources | Work or embedded work, Sanskrit title/variants, category/traditions, classification notes, URLs/library provenance, structure, access/examination status, relevant sections and uncertainties. Identification can rest on catalogue metadata; it cannot support narrative claims. |
| witnesses | `source_id`, editor/translator/language, date/publisher where known, `url`, edition and rights notes, `read_status`, `automated_extraction` (ALLOWED, DISALLOWED, NOT_ESTABLISHED). Unknown bibliographic values remain null or explicitly qualified. |
| passages | `source_id`, `witness_id`, book/khaṇḍa/chapter/verse bounds where available, `url`, human-readable `locator`, `reading_status`, `extraction_status` (UNEXAMINED, PARTIAL, COMPLETE). A bounded excerpt is not a whole chapter. |
| evidence | Same source/witness as referenced `passage_id`; precise `locator`, original concise `paraphrase` or permitted `excerpt`, `classification`, `verification_status`. |
| entities | `name`, allowed entity `type`, `source_scope`, supported aliases and `evidence_ids`. Source-scoped identities remain separate across texts. Generated documentary nodes have `documentary_node: true` and passage/event references. |
| assertions | `subject_id`, `predicate`, optional `object_id` or literal `value`, `evidence_ids`, `verification_status`. Free predicate vocabulary preserves precise textual distinctions. |
| relationships | Entity `subject_id` and `object_id`, `predicate`, `evidence_ids`, `verification_status`, optional `assertion_id` matching the endpoints and predicate. |
| boons_and_powers | BOON or POWER record; recipient/grantor/worshipped entity references, motive, circumstances, requested/granted, mechanism, trigger, restrictions, duration, counter, `later_event_ids`, `evidence_ids`, `field_evidence`, status and notes. Unstated fields are null. Field evidence must be included in record evidence. |
| narrative_events | `source_id`, primary `witness_id`, `supporting_witness_ids`, `story_id`, integer `sequence`, `passage_ids`, participants, setting, cause, details, outcome, changed relationships, introduced entities/powers, consequences and evidence/status. Supporting Sanskrit and translation witnesses may corroborate the same source event. |
| story_spines | Source/witness, title, scope, ordered `event_ids`, status, `completeness_basis`, missing sections and editorial notes. Events must belong to this source/spine and occur in strictly increasing narration order. |
| variants_and_conflicts | Distinct variant ID, description/type, `source_ids`, supporting evidence where read, status and resolution or explicit unresolved question. Metadata-only cautions do not become verified textual claims. |
| coverage | Separate read, complete-excerpt and partial-passage ID sets by source/witness; inventory completeness, narrative extraction completeness, known/unexamined sections, limitations and counts. |
| queue | Stable task IDs, source/target when identified, priority, task, status, dependencies and reason. Discovery targets without inspected witnesses remain separate from registered evidence. |

Evidence classifications: DIRECT_TEXT, TRADITION, COMMENTARY, SCHOLARLY_ANALYSIS, INFERENCE, UNVERIFIED. Verification states: VERIFIED, NEEDS_REVIEW, REJECTED. A VERIFIED relationship cannot depend on unverified/review evidence. Interpretative reports remain identified by classification even when the report itself has been checked.

Sequence numbers preserve the track's narration order. Devī Māhātmya uses global chapter-narration numbers; its frame spine therefore runs 1, 2, 3, 62, 63, 64. Gāṇapatya exempla use local story numbers. Numbers need not be contiguous inside a spine. They do not claim a single historical chronology across flashbacks, future promises, recensions or works. Cause/outcome may be concise text or null; consequences can be a list or text in this v0.1 snapshot. A future promise is preserved as a future statement, not a completed battle.

The evidence chain is claim → evidence → passage → witness → source. Documentary EVENT/PASSAGE/TEXT nodes and DOCUMENTARY_GRAPH_LINK relationships mirror existing records; they do not silently establish chronological causality or biological relationships. Counts distinguish them from extracted content.

`verification_report.json` records structural checks, counts, witness-level verification definition and the independent sample audit when available. `test_integrity.py` exercises guards with corrupted in-memory copies and checks offline queries. `SHA256SUMS.txt` inventories the issued files, excluding itself and Python cache files.
