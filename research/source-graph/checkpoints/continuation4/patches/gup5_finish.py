def finish(checkpoint=None):
 def source_key(z):
  p=next(p for p in d['passages']if p['id']==z['passage_ids'][0]);return(p['chapter'],int(p['verses'].split('–')[0].split(',')[0]))
 d['narrative_events'].sort(key=source_key)
 for seq,z in enumerate(d['narrative_events'],1):z['sequence']=seq
 seen={x['id']for x in OLD['entities']}
 for z in d['narrative_events']:
  z['introduced_entity_ids']=[i for i in z['participants']if i not in seen];seen.update(z['participants'])
  z['changed_relationship_ids']=[r['id']for r in d['relationships']if set(r['evidence_ids'])&set(z['evidence_ids'])]
 definitions=[
 ('moon-curse','Moon’s mockery, mitigation, tapas and Bhālacandra site','61.1–56','PARTIAL',['61.9 cintāmaye hṛde and adjacent epithets;61.35 daśadvādaśa count;61.50 nabhasyaśca qualifier remain unresolved.']),
 ('trio-rescue','Sulabha, Sumudrā and Madhusūdana: curses and inadvertent rescue','62.1–44','COMPLETE',[]),
 ('analasura','Analāsura origin, swallowing, cooling attempts and Vighnahara site','63.16–51;64.1–31','PARTIAL',['63.43 nodanīyo strategy remains unresolved; negative wording withdrawn.']),
 ('janaka-test','Janaka’s feeding test and the poor couple’s devotional gift','65.1–45;66.1–25','COMPLETE',[]),
 ('asraya-weighing','Aśrayā’s equal-weight trial and the couple’s abode','66.26–31;67.1–40','PARTIAL',['67.40 retrospectively describes equality contrary to26 and the trial; full weighing scope remains under review.']),
 ('durva-frame','The rescued-trio yogins and the nested dūrvā explanations','62.45–49;63.1–15;67.40–59','PARTIAL',['The outer teaching ends67.59, but67.26 versus40 scale wording remains unresolved.']),
 ('krtavirya-dream','Dream book, family-guru instruction and concise royal outcomes','68.1–35;70.26;71.18–29','PARTIAL',['68.3 and71.19 Kārtavīrya versus the explicit Kṛtavīrya king; exact named71 royal recipients await collation.','Chapter72 fuller sonbirth account remains unextracted.']),
 ('sankasta-procedure','Prescribed Sankaṣṭa worship and its completion protocol','69.1–62;71.1–17','COMPLETE',[]),
 ('vow-exempla','Brahmā’s brief earlier-practitioner reports and transmission rules','70.1–25','COMPLETE',[])]
 d['story_spines']=[]
 for suf,title,scope,state,missing in definitions:
  i='gup5-story-'+suf;events=[x['id']for x in d['narrative_events']if x['story_id']==i]
  if events:d['story_spines'].append(dict(id=i,title=title,source_id=SID,witness_id=WID,scope=scope,event_ids=events,status=state,completeness_basis='All bodies and named transitions in this bounded witness-local scope are read and extracted; its stated ending is present.'if state=='COMPLETE'else'Read transitions preserved, but significant semantic gaps or unfinished fuller narrative prevent COMPLETE.',missing_sections=missing,editorial_notes='Source-order embedded narration remains distinct from chronology. Brief reports are complete only as bounded reports in this witness, not exhaustive biographies or other-corpus arcs. Ritual formula claims do not become new narrated births.'))
 omissions={61:['61.9 retreat/referent clause,35 duration and50 monthly-second qualifier remain unresolved.'],63:['63.43 nodanīyo strategy requires grammatical or edition collation.'],67:['67.26 versus40 scale wording remains unresolved.'],68:['68.3 Kārtavīrya versus13/18 Kṛtavīrya; exact name variation requires collation.'],71:['71.19 Kārtavīrya performer naming and exact named royal outcome recipients require collation; fuller72 narrative remains unextracted.']}
 chapters=sorted({p['chapter']for p in d['passages']});d['chapter_coverage']=[]
 for ch in chapters:
  ps=[p['id']for p in d['passages']if p['chapter']==ch];es=[e['id']for e in d['evidence']if e['passage_id']in ps];partial=ch in omissions
  d['chapter_coverage'].append(dict(source_id=SID,witness_id=WID,book=None,khanda='Upāsanā',chapter=ch,state='PARTIAL'if partial else'COMPLETE',read_entire_chapter=True,narrative_extracted=True,characters_extracted=not partial,relationships_extracted=not partial,boons_powers_extracted=not partial,checked=not partial,passage_ids=ps,evidence_ids=es,omissions=omissions.get(ch,[]),blocking_reason='Important semantic clauses or exact actor mapping withheld.'if partial else None,independent_review_status='PENDING',independent_review_notes='Author whole-body checking; independent/root/edition review remains separate.'))
 d['chapter_coverage'].append(dict(source_id=SID,witness_id=WID,book=None,khanda='Upāsanā',chapter=72,state='IN_PROGRESS',read_entire_chapter=False,narrative_extracted=False,characters_extracted=False,relationships_extracted=False,boons_powers_extracted=False,checked=False,passage_ids=[],evidence_ids=[],omissions=['72.1–30 read incidentally but unextracted;31 onward unread.'],blocking_reason=None,independent_review_status='PENDING',independent_review_notes='Read-only fragment is not full chapter extraction.'))
 last=max(chapters);target='Upāsanā72.1–30 formal extraction first; unread primary body resumes72.31, then source order through92.'
 d['queue']=[dict(id='gup5-queue-next',source_id=SID,passage_target=target,task='Extract the read-only fragment before reading onward; complete the fuller Kṛtavīrya/son narrative and subsequent bounded endings.',priority='P0-C',status='OPEN',dependency_ids=[],reason='The92-chapter witness and fuller family arc remain incomplete.')]
 for ch,missing in omissions.items():
  d['queue'].append(dict(id=f'gup5-queue-review-{ch}',source_id=SID,passage_target='Upāsanā '+str(ch)+': '+ '; '.join(missing),task='Collate the precise printed clauses; preserve unresolved readings without guessed arithmetic, negative strategy or actor identity.',priority='P0-C',status='OPEN',dependency_ids=[],reason='Significant semantic gap prevents whole chapter and affected story COMPLETE.'))
 update('queue','gup4-queue-next',{'status':'IN_PROGRESS','passage_target':target},f'Before: continuation begins61. After: full61–{last} bodies read and new bounded records extracted; significant gaps remain PARTIAL.',[e['id']for e in d['evidence']])
 prior=next(x for x in OLD['coverage']if x['source_id']==SID and x['witness_id']==WID)
 complete=[p['id']for p in d['passages']if p['extraction_status']=='COMPLETE'];parts=[p['id']for p in d['passages']if p['extraction_status']!='COMPLETE']
 d['coverage']=[dict(source_id=SID,witness_id=WID,known_sections=list(range(1,93)),read_passage_ids=prior['read_passage_ids']+[p['id']for p in d['passages']],completely_extracted_passage_ids=prior['completely_extracted_passage_ids']+complete,partially_extracted_passage_ids=prior['partially_extracted_passage_ids']+parts,unexamined_sections=['72.1–30 read but unextracted;72.31–end and73–92 unread/unextracted.'],inventory_complete=True,narrative_extraction_complete=False,limitations=['Source-order full-body reading/extraction through71; important exact clauses remain partial.','Prior51/53/55/57/59 and earlier issued gaps retained; no full witness or print-edition certification.'])]
 d['changes']=['New gup5 records and explicit stable-ID evidence/queue updates against immutable continuation4 baseline.','Full61–71 bodies read: six COMPLETE chapters62/64/65/66/69/70; five PARTIAL61/63/67/68/71;72 IN_PROGRESS read-only fragment.','Four COMPLETE bounded witness-local scopes: trio rescue, Janaka/couple test, worship/completion protocol, brief vow-exempla report. Five other spines PARTIAL.','63.43 before: unsupported negative strategy. After: raw nodanīyo and no asserted push direction, NEEDS_REVIEW. Prior checkpoint001 remains immutable.']
 d['notes']='Original readable paraphrases of the primary Sanskrit.61.1–19 formally extracted before reading onward. Full61–71 bodies read;72.1–30 read incidentally but unextracted,72.31 onward unread. The near continuation71 was needed to finish the bounded completion protocol; the larger family narrative continues. Chapter67 is physically displaced after69 in HTML but extracted in chapter order. Existing source-scoped actors reuse IDs and evidence unions; Kauṇḍinya the sage is distinct from the previously registered city. Prior issues retain their status; the independently assessed53.3 literal gloss is root-owned and does not edit historical rows here. No prior outputs or tracks overwritten.'
 d['inspected_urls']=[URL]
 (P/'gup5.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 if checkpoint:
  cp=P.parent/'checkpoints/gup5'/f'{checkpoint}.json';cp.parent.mkdir(parents=True,exist_ok=True)
  if not cp.exists():cp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 counts={k:len(d[k])for k in ['passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events']}
 prose=['# Upāsanā continuation5','',d['notes'],'','Six whole chapters are COMPLETE; five are PARTIAL. Chapter72 remains an unextracted fragment. Four bounded scopes are COMPLETE; five spines are PARTIAL. These counts measure this patch only.','',str(counts),'','Next: '+target,'']
 for st in d['story_spines']:
  prose += ['## '+st['title'],'',st['status']+' — '+st['scope'],'']
  for ze in d['narrative_events']:
   if ze['story_id']==st['id']:
    e=next(e for e in d['evidence']if e['id']==ze['evidence_ids'][0]);prose += [e['locator']+' ('+ze['id']+' / '+e['id']+'). '+ze['details'],'']
  if st['missing_sections']:prose+=['Remaining: '+' '.join(st['missing_sections']),'']
 (P/'gup5.md').write_text('\n'.join(prose)+'\n');print(counts)
