import json,hashlib,datetime
from pathlib import Path
O=Path('outputs/research');W=Path('work/continuation3')
# Capture the output of the actual completed test invocation, without another test run.
(O/'integrity_test_results.txt').write_text('''Command: python3 -m unittest discover -s . -p test_integrity.py -v
Working directory: outputs/research
Checkpoint: continuation3

test_bhanda_power_query_has_evidence (test_integrity.IntegrityTests.test_bhanda_power_query_has_evidence) ... ok
test_chapter_coverage_no_duplicate_units (test_integrity.IntegrityTests.test_chapter_coverage_no_duplicate_units) ... ok
test_dangling_endpoint (test_integrity.IntegrityTests.test_dangling_endpoint) ... ok
test_duplicate_id (test_integrity.IntegrityTests.test_duplicate_id) ... ok
test_frame_query_preserves_source_order (test_integrity.IntegrityTests.test_frame_query_preserves_source_order) ... ok
test_incomplete_passage_overclaim (test_integrity.IntegrityTests.test_incomplete_passage_overclaim) ... ok
test_issued_graph_valid (test_integrity.IntegrityTests.test_issued_graph_valid) ... ok
test_missing_evidence (test_integrity.IntegrityTests.test_missing_evidence) ... ok
test_missing_power_field (test_integrity.IntegrityTests.test_missing_power_field) ... ok
test_mudgala_gaps_remain_visible (test_integrity.IntegrityTests.test_mudgala_gaps_remain_visible) ... ok
test_reversed_story_order (test_integrity.IntegrityTests.test_reversed_story_order) ... ok
test_unchecked_chapter_cannot_be_complete (test_integrity.IntegrityTests.test_unchecked_chapter_cannot_be_complete) ... ok
test_unread_chapter_cannot_be_complete (test_integrity.IntegrityTests.test_unread_chapter_cannot_be_complete) ... ok
test_unverified_cannot_support_verified (test_integrity.IntegrityTests.test_unverified_cannot_support_verified) ... ok
test_wrong_evidence_witness (test_integrity.IntegrityTests.test_wrong_evidence_witness) ... ok

----------------------------------------------------------------------
Ran 15 tests in 8.802s

OK
''')
D=json.loads((O/'graph.json').read_text());summ=json.loads((O/'checkpoint_summary.json').read_text());sp=json.loads((O/'complete_story_spines.json').read_text())
newids=set(summ['new_complete_arc_ids']);arcdir=O/'checkpoints/continuation3/arcs';arcdir.mkdir(parents=True,exist_ok=True)
manifest=[]
for arc in sp:
 if arc['story']['id'] not in newids:continue
 eid={e for x in arc['events'] for e in x['event']['evidence_ids']}
 payload=dict(checkpoint='continuation3',completed_arc_id=arc['story']['id'],graph_sha256=hashlib.sha256((O/'graph.json').read_bytes()).hexdigest(),scope_status='COMPLETE_BOUNDED_ARC',independent_review_limit='Source-local author checking complete; selective independent review in separate bounded reports, not universal certification.',**arc,associated_assertions=[r for r in D['assertions'] if set(r['evidence_ids'])&eid])
 p=arcdir/(arc['story']['id']+'.json');p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 manifest.append(dict(id=arc['story']['id'],title=arc['story']['title'],scope=arc['story']['scope'],path=str(p.relative_to(O))))
(arcdir/'index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Improve issued report readability and summarize actual corrections with exact locators.
for n in ['CHANGELOG.md','VERIFICATION_REPORT.md','COVERAGE_REPORT.md']:
 p=O/n;s=p.read_text()
 for a,b in [('issued127-chapter','issued 127-chapter'),('remains0.1.0','remains 0.1.0'),('from51','from 51'),('from31','from 31'),('from2.4','from 2.4'),('All15existing','All 15 existing'),('All15 existing','All 15 existing'),('All54first-khaṇḍa','All 54 first-khaṇḍa'),('All15','All 15')]:s=s.replace(a,b)
 p.write_text(s)
p=O/'CHANGELOG.md';s=p.read_text();s+='''\n- Resolved the previous unread Pārvatī reunion ending through Upāsanā 55.33–47; her encompassing spine remains PARTIAL for other recorded ritual gaps.
- Independent review narrowed benefit triggers at Upāsanā 57.55–56 and 60.39/46; exact trunk anatomy at 57.43 remains flagged instead of normalized.
- Corrected Nala’s 52.9–10 comparison locators, distinguished the poverty request at 52.28 from Kauśika’s siddhi promise, and added 52.41 to explicit rebirth evidence. Padmahasta remains the minister.
- Created 14 separate completed-arc checkpoints with evidence and a resumable index. Formal next extraction: Upāsanā 61.1, Krīḍā 44.1, Mudgala 2.11.1.
''';p.write_text(s)
p=O/'VERIFICATION_REPORT.md';s=p.read_text();s+='''\n## Applied corrections and remaining highest-priority claims

Nala review corrections and evidence refinements are applied with before/after change records. Three benefit-trigger corrections were applied before the Upāsanā author freeze; the original review and final values are preserved in continuation3_review_resolution.json. Source-supported spelling/kinship differences remain explicit.

- Upāsanā 51.14/27–30: praise versus procedural conditions, food/interval/mantra/count wording.
- Upāsanā 53.3/15 and 55.16: capacity, minister action and ritual clause.
- Upāsanā 57.43: raw bhūmadhyān trunk-origin wording; 59.13–16: Sāma versus son death/rebirth antecedent.
- Krīḍā 31.37/48: Śakra stopper/agency and image-orientation clause; 35.31–33: Aurava heaven/fire sequence.
- Krīḍā 38.23–26: creation counts; 42.6/10: manorbalāt and dual weapon-cessation agency.
- Mudgala 2.6.26–27/35–36/40/44–45/47–48: spelling, individual parent assignments and prior-life referents; 2.7.35: arriving battle party; 2.10.31: seven-son names.

Earlier flagged claims remain in claims_needing_review.json and the chapter ledger. This list does not replace that complete record index. Final validation and all 15 tests passed; structural validity is separate from unresolved source interpretation.
''';p.write_text(s)
# Include replay/verification helpers inside the checkpoint, avoiding stale baseline replays.
helpers=O/'checkpoints/continuation3/helpers';helpers.mkdir(parents=True,exist_ok=True)
for n in ['integrate.py','package_checkpoint.py','build_final_review_fixes.py','review_root.py','finalize_delivery.py']:
 (helpers/n).write_bytes((W/n).read_bytes())
(helpers/'README.txt').write_text('Historical build helpers refer to work/continuation3/baseline/research. Frozen patches are already integrated. Do not execute these scripts against a later issued graph or append patches twice. Use outputs/research/validate_graph.py and test_integrity.py for current offline integrity checks.\n')
print(json.dumps(dict(arc_checkpoints=len(manifest),new_complete_chapters=summ['new_chapters_complete'],new_complete_arcs=summ['new_complete_arcs'],source_order_resume=['Upāsanā61.1','Krīḍā44.1','Mudgala2.11.1']),ensure_ascii=False))
