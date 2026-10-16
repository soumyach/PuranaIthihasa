import json,copy
from pathlib import Path
W=Path('work/continuation3')
D=json.loads((W/'baseline/research/graph.json').read_text())
for name in ['gup4','gkr4','mud4']:
 x=json.loads((W/'patches'/f'{name}.json').read_text())
 for t in ['sources','witnesses','passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events','story_spines','variants_and_conflicts','queue']:
  D[t].extend(x.get(t,[]))
 for u in x.get('updates',[]):
  r=next(r for r in D[u['table']] if r['id']==u['id'])
  for k,v in u['fields'].items():
   if k in ['evidence_ids','aliases']:
    for z in v:
     if z not in r.get(k,[]):r.setdefault(k,[]).append(z)
   else:r[k]=copy.deepcopy(v)
updates=[]
def get(t,i):return next(r for r in D[t] if r['id']==i)
def fix(t,i,fields,why,es=[]):updates.append(dict(table=t,id=i,fields=fields,reason=why,evidence_ids=es))
# Same-witness second-author locator corrections, without changing established IDs.
r=get('evidence','gup4-e-013');old='skilled in policy like Aṅgiras, tall like Meru and deep like the ocean.';new='skilled in policy like Aṅgiras.'
assert old in r['paraphrase']
fix('evidence',r['id'],dict(paraphrase=r['paraphrase'].replace(old,new)), 'Independent Nala review: Meru/ocean comparisons occur52.10, outside52.1–9. Move their prose to the existing52.10–20 evidence.', ['gup4-e-013','gup4-e-014'])
r=get('narrative_events','gup4-event-013');assert old in r['details']
fix('narrative_events',r['id'],dict(details=r['details'].replace(old,new)), 'Align event013 with exact52.1–9 evidence;52.10 comparisons move to event014.', ['gup4-e-013','gup4-e-014'])
r=get('evidence','gup4-e-014')
fix('evidence',r['id'],dict(paraphrase='Padmahasta is compared to Meru in height and the ocean in depth. '+r['paraphrase']), 'Independent Nala review:52.10 physical comparisons belong in this source span.', ['gup4-e-014'])
r=get('narrative_events','gup4-event-014')
fix('narrative_events',r['id'],dict(details='Padmahasta is compared to Meru in height and the ocean in depth. '+r['details'],participants=r['participants']+['gup4-en-023']), 'Move52.10 minister comparisons into the supported event span.', ['gup4-e-014'])
fix('entities','gup4-en-023',dict(evidence_ids=['gup4-e-014']), 'Add52.10 support for minister comparisons, retaining52.9 role evidence.', ['gup4-e-014'])
r=get('boons_and_powers','gup4-power-012');fe=copy.deepcopy(r['field_evidence']);fe['mechanism'].append('gup4-e-015')
fix('boons_and_powers',r['id'],dict(mechanism='Kauśika promises siddhi through the month-long Gaṇeśa vow; poverty relief is the sufferer’s requested purpose.',evidence_ids=['gup4-e-015'],field_evidence=fe), 'Independent Nala review: poverty request occurs52.28/e015; distinguish requested purpose from teacher’s explicit siddhi promise29–35/e016.', ['gup4-e-015','gup4-e-016'])
for t,i in [('assertions','gup4-a-016'),('relationships','gup4-rel-015')]:
 fix(t,i,dict(evidence_ids=['gup4-e-017']), 'Independent Nala review strengthens reborn_as with explicit death-and-Nala-birth52.41, retaining earlier former-birth dialogue.', ['gup4-e-015','gup4-e-017'])
r=get('boons_and_powers','mud4-power-moksa-unwanted-capture')
fix('boons_and_powers',r['id'],dict(restrictions='Sūta attributes the effect to these vicious, enjoyment-attached captors who do not desire liberation.',notes=r['notes']+' The explanation is attributed spiritual teaching; no universal physical head/foot-contact law is inferred.'), 'Root direct2.7.40–55 review: restriction field records the source-stated qualification; editorial nonliteral caution belongs in notes.', ['mud4-e-moksa-bhoga-explanation'])
# Reconcile old source-order queues with current work. Keep all IDs and old unresolved claims.
up_target='Upāsanā61.1–19 read fragment, unextracted;61.20–92 unread. Retain3/11/13/23/24/45–47 and new51/53/55/57/59 semantic gaps.'
for i in ['gp-queue-1','gup-queue-next','gup2-queue-next','gup3-queue-next']:
 fix('queue',i,dict(passage_target=up_target,task='Resume formal extraction at61.1, reread the unextracted fragment and continue source order. Preserve Somakānta/Vyāsa frames and all separately flagged Sanskrit gaps.',reason='Bodies51–60 read;52/54/56/58/60 COMPLETE and51/53/55/57/59 PARTIAL. Whole92-chapter witness incomplete.'), 'Reconcile retained source-order queue with continuation3 checkpoint.', [])
fix('queue','gkr2-queue-next-source-order',dict(passage_target='Krīḍā44.1–26 and45.1–39 read-only whole bodies;46.1–8 fragment;46.9 onward unread through136, then150–155. Keep prior semantic gaps and completed137–149 context/Gītā.',task='Resume extraction at44.1, then45 and46; do not skip read-only chapters. Complete later Kīrti/child frame outcomes before upgrading the encompassing spine.',reason='Source-ordered extraction through43;31/35/38/42 remain PARTIAL. Read-only work is not extraction completion.'), 'Reconcile retained earlier queue with continuation3 checkpoint.', [])
fix('queue','rmd2-q-next',dict(task='Resolve retained1.17/20/21 exact language while resuming new source-order body at2.11.1; do not duplicate already extracted2.4–10.',reason='All first-khaṇḍa bodies read; eight semantic/atomic chapter gaps remain.2.4/5/8/9 COMPLETE,2.6/7/10 PARTIAL.'), 'Reconcile stale next2.4 instruction, preserving targeted first-khaṇḍa gaps.', [])
(W/'reviews/central_updates.json').write_text(json.dumps(updates,ensure_ascii=False,indent=2)+'\n')
# Accurate read-only ledgers/passages; these carry no narrative assertions or evidence paraphrases.
rfix=dict(sources=[],witnesses=[],passages=[],evidence=[],entities=[],assertions=[],relationships=[],boons_and_powers=[],narrative_events=[],story_spines=[],variants_and_conflicts=[],queue=[],updates=[],chapter_coverage=[],changes=[])
for wid,c,span,readwhole,lim in [
 ('gp-wit-sd-upasana',61,'1–19',False,'Author read fragment61.1–19; no extraction.61.20 onward unread. Resume at61.1.'),
 ('gp-wit-sd-krida',46,'1–8',False,'Author read fragment46.1–8; no extraction.46.9 onward unread. Formal source-order extraction begins44.1.'),
 ('gp-wit-sd-mudgala-2',11,'1–4',False,'Author closely inspected2.11.1–4;5–42 and terminal colophon only displayed/skimming, not systematic reading. No formal extraction. Resume2.11.1.')]:
 r=copy.deepcopy(next(r for r in D['chapter_coverage'] if r['witness_id']==wid and r['chapter']==c));pid=f'rfix3-p-readonly-{wid}-{c}'
 url={'gp-wit-sd-upasana':'https://sanskritdocuments.org/doc_purana/gaNeshapurANam1.html','gp-wit-sd-krida':'https://sanskritdocuments.org/doc_purana/gaNeshapurANam2.html','gp-wit-sd-mudgala-2':'https://sanskritdocuments.org/doc_purana/mudgalapurANam2.html'}[wid]
 loc=f'{r["khanda"]} {c}.{span}'
 rfix['passages'].append(dict(id=pid,source_id=r['source_id'],witness_id=wid,book=r.get('book'),khanda=r['khanda'],chapter=c,verses=span,url=url,locator=loc,reading_status='PARTIALLY_READ',extraction_status='UNEXAMINED',limitations=lim))
 r.update(state='IN_PROGRESS',read_entire_chapter=readwhole,narrative_extracted=False,characters_extracted=False,relationships_extracted=False,boons_powers_extracted=False,checked=False,passage_ids=[pid],evidence_ids=[],omissions=[lim],blocking_reason=None)
 rfix['chapter_coverage'].append(r)
rfix['changes'].append('Root reconciliation registers three read-only fragments without narrative extraction, based on frozen author reports. Every such chapter stays IN_PROGRESS; no read-only body is skipped at resumption.')
(W/'patches/rfix3.json').write_text(json.dumps(rfix,ensure_ascii=False,indent=2)+'\n')
print('Wrote',len(updates),'explicit corrections/queue updates and three read-only ledger entries')
