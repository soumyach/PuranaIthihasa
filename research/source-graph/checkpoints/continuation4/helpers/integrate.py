"""Incremental replay against the issued145-chapter checkpoint only."""
import json,copy,sys,datetime,collections
from pathlib import Path
W=Path('work/continuation4');BASE=W/'baseline/research';O=Path('outputs/research')
sys.path.insert(0,str(O));import validate_graph as V
D=V.load_graph(BASE);old=copy.deepcopy(D);changes=[];notes=[];tracks=[]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def update(t,i,fields,why,es,track):
    row=next(r for r in D[t] if r['id']==i);before=copy.deepcopy(row)
    for k,v in fields.items():
        if k in ['evidence_ids','aliases'] and isinstance(v,list):
            for z in v:
                if z not in row.get(k,[]):row.setdefault(k,[]).append(z)
        else:row[k]=copy.deepcopy(v)
    if row!=before:changes.append(dict(id=f'continuation4-change-{len(changes)+1:04}',track=track,table=t,record_id=i,before=before,after=copy.deepcopy(row),reason=why,evidence_ids=es))
ledger=copy.deepcopy(old['chapter_coverage'])
for name in ['gup5','gkr5','mud5','rfix4']:
    p=W/'patches'/f'{name}.json'
    if not p.exists():continue
    x=json.loads(p.read_text());tracks.append(name);notes.extend(dict(track=name,change=s) for s in x.get('changes',[]))
    for t in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']:
        ids={r['id'] for r in D[t]}
        for r in x.get(t,[]):
            if r['id'] in ids:raise RuntimeError(f'Collision {t}: {r["id"]}')
            row=copy.deepcopy(r)
            if t=='narrative_events' and not row.get('supporting_witness_ids'):row['supporting_witness_ids']=[row['witness_id']]
            D[t].append(row);ids.add(row['id'])
    for u in x.get('updates',[]):update(u['table'],u['id'],u['fields'],u['reason'],u.get('evidence_ids',[]),name)
    for r in x.get('chapter_coverage',[]):
        z=next((z for z in ledger if (z['source_id'],z['witness_id'],z.get('book'),str(z['chapter']))==(r['source_id'],r['witness_id'],r.get('book'),str(r['chapter']))),None)
        if z is None:ledger.append(copy.deepcopy(r))
        else:
            kh=z.get('khanda');z.update(copy.deepcopy(r));z['khanda']=kh
for u in json.loads((W/'reviews/central_updates.json').read_text()) if (W/'reviews/central_updates.json').exists() else []:
    update(u['table'],u['id'],u['fields'],u['reason'],u.get('evidence_ids',[]),'root-review-resolution')
D['chapter_coverage']=ledger;core=[r for r in ledger if r['source_id'] in ['gp-src-ganesha','gp-src-mudgala']];assert len(core)==675
for c in D['coverage']:
    ps=[p for p in D['passages'] if (p['source_id'],p['witness_id'])==(c['source_id'],c['witness_id'])]
    for k,pred in [('read_passage_ids',lambda p:p['reading_status'] in ['READ','PARTIALLY_READ']),('completely_extracted_passage_ids',lambda p:p['extraction_status']=='COMPLETE'),('partially_extracted_passage_ids',lambda p:p['extraction_status']=='PARTIAL')]:c[k]=[p['id'] for p in ps if pred(p)]
    c['counts']=dict(read_passage_records=len(c['read_passage_ids']),complete_passage_excerpts=len(c['completely_extracted_passage_ids']),partial_passage_records=len(c['partially_extracted_passage_ids']))
    if c['source_id'] in ['gp-src-ganesha','gp-src-mudgala']:
        cc=[r for r in core if r['witness_id']==c['witness_id']]
        c['narrative_extraction_complete']=all(r['state']=='COMPLETE' for r in cc)
        c['unexamined_sections']=['Current chapter_coverage.json and extraction_queue.json retain exact remaining body spans and semantic omissions. A complete excerpt is not a complete chapter.']
report=V.validate(D);assert report['passed'] and not report['warnings'],report
for t in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']:assert {r['id'] for r in old[t]}<={r['id'] for r in D[t]},t
reg=json.loads((BASE/'source_registry.json').read_text());reg.update(sources=D['sources'],witnesses=D['witnesses'],continued_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),continuation_scope='Fourth incremental checkpoint: source-order Upāsanā61, Krīḍā44 and Mudgala2.11 onward; wider registrations retained without expansion.')
dump(O/'source_registry.json',reg)
for t in V.TABLES+['passages','evidence']:dump(O/f'{t}.json',D[t])
cov=json.loads((BASE/'source_coverage.json').read_text());cov.update(records=D['coverage'],chapter_coverage=ledger);dump(O/'source_coverage.json',cov);dump(O/'chapter_coverage.json',ledger)
q=json.loads((BASE/'extraction_queue.json').read_text());q['tasks']=D['queue'];dump(O/'extraction_queue.json',q)
hist=json.loads((BASE/'change_records.json').read_text());hist['record_updates']+=changes;hist['track_changes']+=notes
hist.setdefault('continuation_sessions',[]).append(dict(session='continuation4',tracks=tracks,additions={t:len(D[t])-len(old[t]) for t in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']},record_update_ids=[r['id'] for r in changes]));hist['stable_ids_preserved']=True
dump(O/'change_records.json',hist);dump(O/'continuation4_change_records.json',changes);dump(O/'graph.json',dict(schema_version='0.1.0',**D))
report.update(counts=V.stats(D),core_chapter_states=dict(collections.Counter(r['state'] for r in core)),baseline_ids_preserved=True);dump(O/'verification_report.json',report)
print(json.dumps(dict(tracks=tracks,passed=True,chapter_states=report['core_chapter_states'],record_updates=len(changes),counts=report['counts']),ensure_ascii=False,indent=2))
