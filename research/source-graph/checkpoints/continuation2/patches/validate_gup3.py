import json,sys,copy,collections
from pathlib import Path
P=Path(__file__).parent
sys.path.insert(0,str(P.parents[2]/'outputs/research'))
import validate_graph as V
base=json.loads((P.parents[2]/'outputs/research/graph.json').read_text());d=copy.deepcopy(base);p=json.loads((P/'gup3.json').read_text())
prev=json.loads((P/'gup2.json').read_text())
# Overlay predecessor if parent has not integrated frozen gup2 yet.
for table in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']:
 ids={x['id']for x in d[table]}
 d[table].extend(x for x in prev.get(table,[])if x['id']not in ids)
for table in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']:
 d[table]+=p.get(table,[])
for u in p['updates']:
 r=next(x for x in d[u['table']]if x['id']==u['id'])
 for key,val in u['fields'].items():
  if key in ['evidence_ids','aliases']:
   for z in val:
    if z not in r.setdefault(key,[]):r[key].append(z)
  else:r[key]=val
for row in p['chapter_coverage']:
 ix=next((i for i,c in enumerate(d['chapter_coverage'])if (c['source_id'],c['witness_id'],c.get('book'),str(c['chapter']))==(row['source_id'],row['witness_id'],row.get('book'),str(row['chapter']))),None)
 if ix is None:d['chapter_coverage'].append(row)
 else:d['chapter_coverage'][ix]=row
report=V.validate(d)
report['patch_counts']={k:len(p.get(k,[]))for k in ['passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events','story_spines','variants_and_conflicts']}
report['new_chapter_states']=dict(collections.Counter(c['state']for c in p['chapter_coverage']if c['chapter']>=48))
(P/'gup3_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(not report['passed'])
