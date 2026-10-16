def finish(checkpoint=None):
 def key(z):
  p=next(p for p in d['passages']if p['id']==z['passage_ids'][0]);return(p['chapter'],int(p['verses'].split('–')[0].split(',')[0]))
 d['narrative_events'].sort(key=key)
 seen={z['id']for z in OLD['entities']}
 for q,z in enumerate(d['narrative_events'],1):
  z['sequence']=key(z)[0]*1000+key(z)[1];z['introduced_entity_ids']=[i for i in z['participants']if i not in seen];seen.update(z['participants']);z['changed_relationship_ids']=[r['id']for r in d['relationships']if set(r['evidence_ids'])&set(z['evidence_ids'])]
 defs=globals().get('spines',[('kartavirya-recovery','Kārtavīrya’s expanded birth and remedy','72.1–30; remainder pending','PARTIAL',['Full chapter and actual remedy outcome pending.'])])
 d['story_spines']=[]
 for suffix,title,scope,state,missing in defs:
  sid='gup6-story-'+suffix;events=[z['id']for z in d['narrative_events']if z['story_id']==sid]
  if events:d['story_spines'].append(dict(id=sid,title=title,source_id=SID,witness_id=WID,scope=scope,event_ids=events,status=state,completeness_basis='Full bounded body and important named dialogue, relationships, requests/grants/powers checked; actual ending present.'if state=='COMPLETE'else'Incomplete body or important semantic gap retained without guessed chronology.',missing_sections=missing,editorial_notes='Source order is preserved.71 concise fulfilled-life summary precedes72 expanded sonbirth/remedy; local72 father/child naming does not harmonize anomalous68/71 performer names.'))
 d['chapter_coverage']=[];full=globals().get('full_chapters',set());omits=globals().get('chapter_omissions',{})
 for ch in sorted({p['chapter']for p in d['passages']}):
  ps=[p['id']for p in d['passages']if p['chapter']==ch];es=[e['id']for e in d['evidence']if e['passage_id']in ps];read=ch in full;complete=read and ch not in omits
  d['chapter_coverage'].append(dict(source_id=SID,witness_id=WID,book=None,khanda='Upāsanā',chapter=ch,state='COMPLETE'if complete else'PARTIAL'if read else'IN_PROGRESS',read_entire_chapter=read,narrative_extracted=complete,characters_extracted=complete,relationships_extracted=complete,boons_powers_extracted=complete,checked=complete,passage_ids=ps,evidence_ids=es,omissions=omits.get(ch,[]if read else['Chapter remainder not yet read/extracted.']),blocking_reason='Important source-local semantic gap.'if read and not complete else None,independent_review_status='PENDING',independent_review_notes='Author primary-witness checks; root/peer/print verification separate.'))
 if 80 in full:
  d['chapter_coverage'].append(dict(source_id=SID,witness_id=WID,book=None,khanda='Upāsanā',chapter=81,state='IN_PROGRESS',read_entire_chapter=False,narrative_extracted=False,characters_extracted=False,relationships_extracted=False,boons_powers_extracted=False,checked=False,passage_ids=[],evidence_ids=[],omissions=['81.1–9 read-only preview unextracted;10 first line only, remainder unread.'],blocking_reason=None,independent_review_status='PENDING',independent_review_notes='Preview is not complete body or formal extraction.'))
 nxt=globals().get('next_target','Upāsanā72.31 onward, after formally extracted72.1–30 fragment.');notes=globals().get('reading_notes','72.1–30 prior read-only body is now formally extracted;72.31 onward unread.')
 d['queue']=[dict(id='gup6-queue-next',source_id=SID,passage_target=nxt,task='Continue source-order whole bodies and actual bounded endings; preserve unresolved earlier names and semantic gaps.',priority='P0-C',status='OPEN',dependency_ids=[],reason='The92-chapter witness remains unfinished.')]
 update('queue','gup5-queue-next',{'status':'IN_PROGRESS','passage_target':nxt},'Prior72 read-only target is formally extracted and source order advances.',[e['id']for e in d['evidence']])
 prior=next(z for z in OLD['coverage']if z['source_id']==SID and z['witness_id']==WID)
 d['coverage']=[dict(source_id=SID,witness_id=WID,known_sections=list(range(1,93)),read_passage_ids=prior['read_passage_ids']+[p['id']for p in d['passages']],completely_extracted_passage_ids=prior['completely_extracted_passage_ids']+[p['id']for p in d['passages']if p['extraction_status']=='COMPLETE'],partially_extracted_passage_ids=prior['partially_extracted_passage_ids']+[p['id']for p in d['passages']if p['extraction_status']!='COMPLETE'],inventory_complete=True,narrative_extraction_complete=False,unexamined_sections=[nxt],limitations=['Earlier issued semantic gaps remain unresolved unless explicitly updated.','Whole chapter completeness differs from excerpt checks and independent edition verification.'])]
 d['changes']=['New gup6 records and explicit stable-ID updates against checkpoint4/continuation5 baseline.','Prior72.1–30 read-only body formally extracted before new reading.','New source narration positions use chapter-scaled numbers so older existing-spine continuations follow their prior events; this is not biological chronology.','Qualified frame labels discovered after002 retain historical IDs with explicit same-source identity links and canonical-reference updates; no silent deletion.'];d['notes']=notes;d['inspected_urls']=[URL]
 import hashlib
 d['base_snapshot_sha256']=hashlib.sha256((P.parent/'baseline/research/graph.json').read_bytes()).hexdigest()
 (P/'gup6.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 if checkpoint:
  cp=P.parent/'checkpoints/gup6'/f'{checkpoint}.json';cp.parent.mkdir(parents=True,exist_ok=True)
  if cp.exists():raise RuntimeError('Append-only checkpoint already exists: '+str(cp))
  cp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 out=['# Upāsanā continuation6','',notes,'','Chapter checks: '+str([(c['chapter'],c['state'])for c in d['chapter_coverage']]),'','Next: '+nxt,'']
 for s in d['story_spines']:
  out+=['## '+s['title'],'',s['status']+' — '+s['scope'],'']
  for z in d['narrative_events']:
   if z['story_id']==s['id']:
    e=next(e for e in d['evidence']if e['id']==z['evidence_ids'][0]);out+=[e['locator']+' ('+z['id']+' / '+e['id']+'). '+z['details'],'']
  if s['missing_sections']:out+=['Remaining: '+' '.join(s['missing_sections']),'']
 (P/'gup6.md').write_text('\n'.join(out)+'\n');print({k:len(d[k])for k in ['evidence','entities','assertions','relationships','boons_and_powers','narrative_events']})
