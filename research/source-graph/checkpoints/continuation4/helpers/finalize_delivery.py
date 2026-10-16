import json,hashlib,shutil
from pathlib import Path
O=Path('outputs/research');W=Path('work/continuation4')
assert (O/'integrity_test_results.txt').read_text().rstrip().endswith('OK')
D=json.loads((O/'graph.json').read_text());S=json.loads((O/'checkpoint_summary.json').read_text());sp=json.loads((O/'complete_story_spines.json').read_text())
ids=set(S['new_complete_arc_ids']);out=O/'checkpoints/continuation4/arcs';out.mkdir(parents=True,exist_ok=True);manifest=[]
for arc in sp:
 if arc['story']['id'] not in ids:continue
 es={i for e in arc['events'] for i in e['event']['evidence_ids']}
 payload=dict(checkpoint='continuation4',completed_arc_id=arc['story']['id'],graph_sha256=hashlib.sha256((O/'graph.json').read_bytes()).hexdigest(),scope_status='COMPLETE_BOUNDED_ARC',independent_review_limit='Source-local author checks complete; independent review selective. All declared interpretation gaps remain explicit.',**arc,associated_assertions=[r for r in D['assertions'] if set(r['evidence_ids'])&es])
 p=out/(arc['story']['id']+'.json');p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');manifest.append(dict(id=arc['story']['id'],title=arc['story']['title'],scope=arc['story']['scope'],path=str(p.relative_to(O))))
(out/'index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in ['CHANGELOG.md','VERIFICATION_REPORT.md','COVERAGE_REPORT.md']:
 p=O/n;s=p.read_text()
 for a,b in [('All15','All 15'),('All54first-khaṇḍa','All 54 first-khaṇḍa'),('remains0.1.0','remains 0.1.0')]:s=s.replace(a,b)
 p.write_text(s)
p=O/'CHANGELOG.md';s=p.read_text();s+='''\n- Extracted checkpoint3 read-only spans at Upāsanā61, Krīḍā44–46 and Mudgala2.11 before advancing source order.
- Clarified printed Upāsanā53.3 apeta as an absence qualifier without emending the source. Other53/55 gaps and alternate-print uncertainty remain.
- Separated the contextual manorbalāt/mantra-power gloss as INFERENCE. Withdrew an unsupported negative in Analāsura’s encounter; uncertain strategy keeps its full scope PARTIAL.
- Extended the existing Kīrti child spine through the teacher/name transition, coronation, actual reign, succession and final outcome while preserving its ID.
''';p.write_text(s)
helpers=O/'checkpoints/continuation4/helpers';helpers.mkdir(parents=True,exist_ok=True)
for n in ['integrate.py','package_checkpoint.py','build_root_gap_review.py','review_root.py','finalize_delivery.py']:
 shutil.copyfile(W/n,helpers/n)
(helpers/'README.txt').write_text('Historical builders use work/continuation4/baseline/research. Frozen patches are already integrated. Do not replay them against later checkpoints. Current offline checks are validate_graph.py and test_integrity.py in research/.\n')
vr=json.loads((O/'verification_report.json').read_text());vr['integrity_tests']=dict(command='python3 -m unittest discover -s outputs/research -p test_integrity.py -v',tests_run=15,passed=15,failed=0,log='integrity_test_results.txt');(O/'verification_report.json').write_text(json.dumps(vr,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(new_chapters_complete=S['new_chapters_complete'],new_complete_arcs=S['new_complete_arcs'],arc_checkpoints=len(manifest)),ensure_ascii=False))
