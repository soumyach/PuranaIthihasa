import json,copy
from pathlib import Path
W=Path('work/continuation4');D=json.loads((W/'baseline/research/graph.json').read_text())
for name in ['gup5','gkr5','mud5','rfix4']:
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
U=[]
def update(t,i,f,why,es=[]):U.append(dict(table=t,id=i,fields=f,reason=why,evidence_ids=es))
update('entities','gup5-en-052',dict(type='DEVOTEE'), 'Independent whole65–66 review: Triśiras is a Brahmin/devotee; SAGE is not stated in the checked spans. Preserve ID and evidence.', ['gup5-e-033','gup5-e-034'])
for t,i in [('assertions','gup5-a-027'),('relationships','gup5-rel-023')]:
 update(t,i,dict(evidence_ids=['gup5-e-033']), 'Independent whole65–66 review strengthens named spouse linkage with65.44, retaining66 evidence.', ['gup5-e-033','gup5-e-034'])
for t,i,k in [('evidence','gup5-e-047','paraphrase'),('narrative_events','gup5-event-043','details')]:
 r=next(r for r in D[t] if r['id']==i)
 a='The father says he recorded the instructions, gives the book,'
 b='The father says the book was written according to Brahmā’s instructions, gives it,'
 assert a in r[k]
 update(t,i,{k:r[k].replace(a,b)},'Independent whole68 review:68.10 passive writing does not securely identify the father as writer; delivery11 retained.',['gup5-e-047'])
update('boons_and_powers','mud5-power-pulaha-hymn-benefits',dict(recipient_id='rfix4-en-pulaha-hymn-audience'), 'Independent2.18 review: hymn beneficiaries are mortal readers/hearers, not the existing cosmography audience. Benefit wording and triggers retained.', ['mud5-e-pulaha-devotion-boon'])
update('boons_and_powers','mud5-power-vighnaraja-grace-reflection',dict(recipient_id='rfix4-en-vighnaraja-reflection-beneficiaries'), 'Independent2.18 review: attributed reflection addresses Śiva/Viṣṇu and all beings; retain reflection status rather than creating a new personal boon.', ['mud5-e-bharata-deer-body-ending'])
up='Upāsanā72.1–30 read-only and unextracted;72.31–92 unread. New61/63/67/68/71 partials and all earlier chapter/print gaps remain separate.53.3 literal apeta resolved,53.15 still pending.'
kr='Krīḍā54.1–64 read-only whole body;55.1–14 fragment,55.15 onward unread through136, then150–155. Keep44/49/50/52 and earlier partials; completed137–149/Gītā context retained.'
mud='Mudgala2.19.1–23 root read-only,24a seen, author19.1–28 only displayed; no formal extraction. Continue2.19–74 then indexed3–9. New2.11/13/14/15/16/17 and earlier1/2 gaps remain.'
sets=[(up,['gp-queue-1','gup-queue-next','gup2-queue-next','gup3-queue-next','gup4-queue-next']), (kr,['gp-queue-2','gkr-queue-source-order','gkr2-queue-next-source-order','gkr3-queue-next-source-order','gkr4-queue-next-source-order','gkr-queue-read-unextracted']), (mud,['gp-queue-5','mud-queue-khandas2to9','mud2-queue-kh2-next','mud3-queue-forward-handoff','rmd2-q-next'])]
for target,ids in sets:
 for i in ids:
  r=next(r for r in D['queue'] if r['id']==i)
  if r.get('status') in ['DONE','COMPLETE','CLOSED','RESOLVED']:continue
  fields=dict(passage_target=target)
  if i.startswith('gup'):fields['task']='Resume formal source-order extraction at72.1; re-read/extract the fragment, preserve enclosing frames and all recorded semantic gaps.'
  elif i.startswith('gkr'):fields['task']='Resume formal extraction at54.1; extract read-only54/55 before new source-order bodies. Preserve every existing ID, earlier uncertainty and completed Gītā context.'
  elif i.startswith(('mud2','mud3')):fields['task']='Resume formal extraction at2.19.1 while retaining targeted earlier gaps and all nine khaṇḍas. Do not duplicate11–18 extracted bodies.'
  elif i=='rmd2-q-next':fields['task']='Resolve targeted first-khaṇḍa residual language while resuming next source-order body at2.19.1.'
  update('queue',i,fields,'Reconcile preserved source-order queue with continuation4 frozen tracks. Read-only work is not extraction completion.')
(W/'reviews/central_updates.json').write_text(json.dumps(U,ensure_ascii=False,indent=2)+'\n')
# Resolve only the withdrawn negative; semantic strategy uncertainty explicitly stays pending.
p=W/'reviews/root_strategy_finding.json';review=json.loads(p.read_text());f=review['findings'][0]
f.update(status='CORRECTION_APPLIED_WITH_RETAINED_GAP',applied_before_author_freeze=True,author_checkpoint='checkpoints/continuation4/checkpoints/gup5/durva-strategy-correction-002.json',semantic_remaining='Exact intended force/action remains NEEDS_REVIEW; chapter63 and full Analāsura spine PARTIAL.',after_records=[dict(table=a['table'],id=a['id'],after=next(r for r in D[a['table']] if r['id']==a['id'])) for a in f['records']])
p.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(U),'explicit final corrections/queue reconciliations')
