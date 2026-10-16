import json,hashlib,zipfile,sys
from pathlib import Path
O=Path('outputs/research');Z=Path('outputs/khatakshetra-source-graph-v0.1-continuation4.zip')
rows=json.loads((O/'chapter_coverage.json').read_text())
q=['# Resumable extraction queue', '', 'Current graph and chapter ledger are authoritative. Frozen patches are already integrated; do not append them twice or replay older baseline scripts.', '', '1. Gaṇeśa Upāsanā: resume formal extraction at 72.1. Verses 72.1–30 were read-only; 72.31 onward through 92 is unread. New61/63/67/68/71 and earlier semantic gaps remain. The displaced67 block was read at its actual location after69 in the digital witness; chapter-order narration is explicitly retained.', '2. Gaṇeśa Krīḍā: resume at 54.1. The whole body 54.1–64 was read-only; 55.1–14 was a fragment; 55.15 onward through 136 and 150–155 remains. Extract read-only chapters before advancing. EmbeddedGītā138–148 and137/149 context retained; earlier44/49/50/52 and other partials remain.', '3. Mudgala: resume at 2.19.1. Root read 19.1–23 and the first half of 24; the author only displayed 1–28 without systematic reading. No formal19 extraction. Continue19–74 then all indexed3–9; six partial chapters 11/13/14/15/16/17 and earlier1/2 uncertainties retained. Ninth khaṇḍa’s 41 chapters remains.', '4. Independent review: exact family/boon/counter/outcome uncertainties and before/after corrections are in verification and resolution reports. Source-local VERIFIED and chapter COMPLETE do not claim exhaustive second-author or alternate-print certification.', '', '## Exact PARTIAL chapter omissions', '']
for r in rows:
 if r['source_id'] in ['gp-src-ganesha','gp-src-mudgala'] and r['state']=='PARTIAL':q.append(f'- {r["witness_id"]} chapter {r["chapter"]}: '+'; '.join(r['omissions']))
q+=['', 'The complete registry with stable queue IDs is extraction_queue.json. No additional Purāṇas or wider-corpus extraction started in this continuation.']
(O/'RESUMABLE_QUEUE.md').write_text('\n'.join(q)+'\n')
sys.path.insert(0,str(O));import validate_graph as V
D=V.load_graph(O);report=V.validate(D);assert report['passed'] and not report['warnings'],report
stored=json.loads((O/'graph.json').read_text());assert all(stored[k]==v for k,v in D.items())
summary=json.loads((O/'checkpoint_summary.json').read_text());assert summary['new_chapters_complete']==14 and summary['new_complete_arcs']==13
cp=O/'checkpoints/continuation4';(cp/'RESUME.md').write_text((O/'RESUMABLE_QUEUE.md').read_text())
vr=json.loads((O/'verification_report.json').read_text());vr['integrity_tests']=dict(command='python3 -m unittest discover -s outputs/research -p test_integrity.py -v',tests_run=15,passed=15,failed=0,log='integrity_test_results.txt');(O/'verification_report.json').write_text(json.dumps(vr,ensure_ascii=False,indent=2)+'\n')
(O/'checkpoints/continuation4/helpers/archive.py').write_bytes(Path(__file__).read_bytes())
files=[p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS.txt']
lines=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(O)) for p in sorted(files)]
(O/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
for line in lines:
 h,n=line.split('  ',1);assert hashlib.sha256((O/n).read_bytes()).hexdigest()==h
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files+[O/'SHA256SUMS.txt']):z.write(p,Path('research')/p.relative_to(O))
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 for line in lines:
  h,n=line.split('  ',1);assert hashlib.sha256(z.read('research/'+n)).hexdigest()==h
print(json.dumps(dict(archive=str(Z.resolve()),files=len(files)+1,archive_bytes=Z.stat().st_size,crc_passed=True,sha256_contents_passed=True,validator_errors=0,validator_warnings=0,stable_ids_preserved=True,chapter_states=summary['core_chapter_states']),indent=2))
