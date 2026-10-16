import json,pathlib
P=pathlib.Path(__file__).parent
OLD=json.loads((P.parent/'baseline/research/graph.json').read_text())
SID='gp-src-ganesha';WID='gp-wit-sd-upasana';URL='https://sanskritdocuments.org/doc_purana/gaNeshapurANam1.html'
d={k:[]for k in ['sources','witnesses','passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events','story_spines','variants_and_conflicts','coverage','queue','updates','chapter_coverage']}
names={}
for a in OLD['entities']:
 if a['source_scope']==SID and not a.get('documentary_node'):
  names.setdefault(a['name'],a['id'])
  for alias in a.get('aliases',[]):
   if isinstance(alias,dict):names.setdefault(alias['name'],a['id'])
existing_entity_ids={a['id']for a in OLD['entities']}
reuse={'Sūta':'gp-en-suta','Brahmā':'gp-en-brahma','Vyāsa':'gp-en-vyasa','Gaṇeśa':'gp-en-ganesha','Questioning sages':'gp-en-sages'}
names.update(reuse)
entityrows={}
def en(name,typ,e):
 if name in names:
  i=names[name]
  if i in existing_entity_ids:
   u=next((u for u in d['updates']if u['table']=='entities'and u['id']==i),None)
   if not u:
    prior=next(a for a in OLD['entities']if a['id']==i)
    u=dict(table='entities',id=i,fields={'evidence_ids':prior['evidence_ids'][:]},reason='Same Gaṇeśa Purāṇa source-scoped actor appears in Upāsanā body.',evidence_ids=[]);d['updates'].append(u)
   u['fields'].setdefault('evidence_ids',next(a for a in OLD['entities']if a['id']==i)['evidence_ids'][:])
   if e not in u['fields']['evidence_ids']:u['fields']['evidence_ids'].append(e)
   if e not in u['evidence_ids']:u['evidence_ids'].append(e)
  elif e not in entityrows[i]['evidence_ids']:entityrows[i]['evidence_ids'].append(e)
  return i
 i='gup6-en-'+str(len(d['entities'])+1).zfill(3);names[name]=i
 a=dict(id=i,name=name,type=typ,source_scope=SID,aliases=[],evidence_ids=[e]);d['entities'].append(a);entityrows[i]=a;return i
def ev(ch,verses,text,actors,story='gup6-story-kartavirya-recovery',cause=None,outcome=None,status='VERIFIED'):
 p='gup6-p-'+str(ch)+'-'+verses.replace('–','-').replace(' ','')
 e='gup6-e-'+str(len(d['evidence'])+1).zfill(3)
 d['passages'].append(dict(id=p,source_id=SID,witness_id=WID,book='Gaṇeśa Purāṇa',khanda='Upāsanākhaṇḍa',chapter=ch,verses=verses,url=URL,locator=f'Upāsanā {ch}.{verses}',reading_status='READ',extraction_status='COMPLETE'if status=='VERIFIED'else'PARTIAL',limitations='Witness-level bounded extraction; chapter completeness separately checked.'))
 d['evidence'].append(dict(id=e,source_id=SID,witness_id=WID,passage_id=p,locator=f'Upāsanā {ch}.{verses}',paraphrase=text,classification='DIRECT_TEXT',verification_status=status,verifier='Upāsanā continuation agent',verification_notes='Direct Sanskrit body reading; not independent edition verification. Uncertain Sanskrit clauses identified separately.'))
 ids=[en(n,t,e)for n,t in actors]
 i='gup6-event-'+str(len(d['narrative_events'])+1).zfill(3)
 d['narrative_events'].append(dict(id=i,source_id=SID,witness_id=WID,supporting_witness_ids=[WID],story_id=story,sequence=len(d['narrative_events'])+1,passage_ids=[p],participants=ids,setting=None,cause=cause,details=text,outcome=outcome,changed_relationship_ids=[],introduced_entity_ids=[],introduced_power_ids=[],consequences=[],evidence_ids=[e],verification_status=status))
 return e,i
def rel(s,p,o,e,kind=None):
 i='gup6-rel-'+str(len(d['relationships'])+1).zfill(3);a='gup6-a-'+str(len(d['assertions'])+1).zfill(3)
 row=dict(id=i,subject_id=names[s],predicate=p,object_id=names[o],evidence_ids=[e],verification_status='VERIFIED',assertion_id=a)
 if kind:row['kinship_kind']=kind
 d['relationships'].append(row)
 d['assertions'].append(dict(id=a,subject_id=names[s],predicate=p,object_id=names[o],value=None,evidence_ids=[e],verification_status='VERIFIED'))
 return i
def val(s,p,value,e):
 d['assertions'].append(dict(id='gup6-a-'+str(len(d['assertions'])+1).zfill(3),subject_id=names[s],predicate=p,object_id=None,value=value,evidence_ids=[e],verification_status='VERIFIED'))
def power(rec,e,event,typ='POWER',grant=None,**kw):
 a=dict(id='gup6-power-'+str(len(d['boons_and_powers'])+1).zfill(3),type=typ,recipient_id=names[rec],grantor_id=names.get(grant),worshipped_id=None,motive=None,austerity_or_circumstances=None,requested=None,granted=None,mechanism=None,trigger=None,restrictions=None,duration=None,counter=None,later_event_ids=[],evidence_ids=[e],field_evidence={},verification_status='VERIFIED',notes='Null means unstated in examined passage, not independently proven absent from whole work. Reported efficacy is a POWER unless an explicit personal boon is narrated.')
 a.update(kw)
 for k,v in a.items():
  if k in ['recipient_id','grantor_id','worshipped_id','motive','austerity_or_circumstances','requested','granted','mechanism','trigger','restrictions','duration','counter']and v is not None:a['field_evidence'][k]=[e]
 d['boons_and_powers'].append(a);next(z for z in d['narrative_events']if z['id']==event)['introduced_power_ids'].append(a['id']);return a

F='PERSON';S='SAGE';D='DEITY';C='CONCEPT';L='PLACE';T='TEXT';W='WEAPON';A='ASURA'
def update(table,i,fields,reason,eids):
 u=next((u for u in d['updates']if u['table']==table and u['id']==i),None)
 if u:u['fields'].update(fields);u['reason']+=' '+reason;u['evidence_ids']=list(dict.fromkeys(u['evidence_ids']+eids))
 else:d['updates'].append(dict(table=table,id=i,fields=fields,reason=reason,evidence_ids=eids))
def note_evidence(ch,verses,text,status='VERIFIED'):
 p='gup6-p-review-'+str(ch)+'-'+str(len(d['evidence'])+1)
 e='gup6-e-'+str(len(d['evidence'])+1).zfill(3)
 d['passages'].append(dict(id=p,source_id=SID,witness_id=WID,book='Gaṇeśa Purāṇa',khanda='Upāsanākhaṇḍa',chapter=ch,verses=verses,url=URL,locator=f'Upāsanā {ch}.{verses}',reading_status='READ',extraction_status='PARTIAL',limitations='Collation excerpt; whole chapter completeness separate.'))
 d['evidence'].append(dict(id=e,source_id=SID,witness_id=WID,passage_id=p,locator=f'Upāsanā {ch}.{verses}',paraphrase=text,classification='DIRECT_TEXT',verification_status=status,verifier='Upāsanā continuation6 author',verification_notes='Direct reread; transcription observed, unresolved interpretation not asserted.'))
 return e
def variant(i,text,e):
 d['variants_and_conflicts'].append(dict(id='gup6-var-'+i,type='SOURCE_LOCAL_READING_UNCERTAINTY',description=text,source_ids=[SID],evidence_ids=[e],status='OPEN',resolution=None))
KV='Kṛtavīrya';Q='Sugandhā (Kṛtavīrya wife)';SON='Kārtavīrya (child named in72)';DT='Dattātreya';S1='gup6-story-kartavirya-recovery'
# Formal extraction of the prior read-only72.1–30 fragment, before new body reading.
e,v=ev(72,'1–10','Śūrasena asks Indra for the detailed birth of the couple’s son after the vow. Indra says that through pleased Gaṇeśa’s favour the queen conceives and in the ninth month sees a son with two shoulders, beautiful face, nose and lotus eyes but no arms/hands, thighs/knees, lower legs or feet. She laments the gift, says remaining barren would have been better, questions removal of prior sin, the deity’s favour and Brahmin assurances, and repeatedly strikes her breast and forehead. The women weep; the king, ministers and townspeople hear and join the grief.',[('Śūrasena',F),('Indra',D),('Gaṇeśa',D),(KV,F),(Q,F),(SON,F),('Kṛtavīrya ministers','FAMILY'),('Women attending royal birth in72','FAMILY'),('Kṛtavīrya assembled public','FAMILY')],story=S1,outcome='Actual sonbirth and the detailed absence of limbs are narrated before the remedy; no normal-limbed birth is substituted.')
power(Q,e,v,grant='Gaṇeśa',mechanism='The queen conceives through the pleased deity’s favour and bears the described child in the ninth month.',notes='Actual narrative favour, not a new boon invitation/request/grant scene. Her lament questions efficacy; it is not narrator proof that all prior merit was absent.')
e,v=ev(72,'11–20','The king questions Gaṇeśa’s compassion and declares his japa, tapas, remembrance, gifts, worship, Brahmin feeding, observance and homa apparently wasted. He says fate is stronger and effort fruitless, comparing the son with a mouse gained by breaking a mountain. Ministers urge him to cease grief because what must occur cannot be changed: they cite Rāma following the deer and Dharmarāja entering forbidden dice and then forest exile despite knowledge. Crying will not make the child beautiful; good unseen merit could allow his later improvement and kingship with time, as trees bear flowers and fruit. The king steadies himself and tells his wife to rise without grief. The king’s first verse is printed1 before the numbering resumes12; this span follows its sequential position.',[(KV,F),(Q,F),(SON,F),('Gaṇeśa',D),('Kṛtavīrya ministers','FAMILY'),('Rāma in72 ministerial example',F),('Dharmarāja in72 ministerial example',F)],story=S1,outcome='Attributed fatalist complaint is answered by ministerial counsel and an explicitly prospective possible improvement.')
val('Kṛtavīrya ministers','attributed_counsel_72','Grief cannot restore beauty; if unseen merit is favourable the boy may later improve and become king72.16–20. Rāma/deer and Dharmarāja/dice are brief examples, not full retellings.',e)
e,v=ev(72,'21–26','The king calls Brahmins, performs Gaṇeśa worship, svastivācana and auspicious śrāddha, and gives garlands, ornaments, clothes, cows and jewels. He gives clothes and appropriate gifts to friends, relatives, servants, musicians, bards, Cāraṇas and poor, blind and destitute people, distributing betel and sugar house to house. On the eleventh day he names the son Kārtavīrya and feeds the city with enthusiasm. Twelve years of the son’s life pass; Dattātreya voluntarily comes to his house.',[(KV,F),(SON,F),('Gaṇeśa',D),('Royal birth Brahmins in72','FAMILY'),('Royal birth gift recipients in72','FAMILY'),('Cāraṇas',C),(DT,S)],story=S1,outcome='The boy receives an explicit name on day11 and reaches age12 before the voluntary sage visit.')
val(SON,'source_name_given','Kārtavīrya on eleventh day72.25; actual son’s explicit name does not silently emend earlier68.3/71.19 performer names.',e);val(SON,'age_at_dattatreya_visit','Twelve years72.26.',e)
e,v=ev(72,'27–30','The king explicitly named Kṛtavīrya bows with his head at Dattātreya’s feet. The sage rises and embraces him. The king seats and honours him with seat, foot-water, arghya, a cow, clothes, sacred thread, incense, lamp, offerings, varied fruit, rubbing powder, betel, jewels, gold dakṣiṇā and foot-massage. When the sage is pleased and comfortably seated the king addresses him; the read-only fragment stops before the request.',[(KV,F),(DT,S),(SON,F)],story=S1,outcome='The visitor is welcomed before the exact request and explanation; the next primary unread verse is31.')
rel(SON,'son_of',KV,e,'SOURCE_EXPLICIT_NAMING_AND_FATHER_CONTEXT');d['relationships'][-1]['evidence_ids'].append('gup6-e-003');d['assertions'][-1]['evidence_ids'].append('gup6-e-003')
# The source now names father and son locally; earlier anomalous performer words stay unresolved.
update('story_spines','gup5-story-krtavirya-dream',{'status':'PARTIAL','missing_sections':['68.3 and71.19 Kārtavīrya performer names remain uncollated;71 exact named outcome mapping remains under review.','Fuller sonbirth/remedy continuation starts72, now separately extracted in gup6; its ending is pending.']},'72.25 names the boy Kārtavīrya,27 names the visiting king Kṛtavīrya; local72 identity does not correct earlier printed names.',[e,'gup6-e-003'])
update('queue','gup5-queue-next',{'status':'IN_PROGRESS','passage_target':'Upāsanā72.31 onward;72.1–30 formally extracted in gup6.'},'Prior read-only fragment is now formally extracted; sequential body reading can resume31.',[e,'gup6-e-001','gup6-e-002','gup6-e-003'])
exec((P/'gup6_extend.py').read_text())
exec((P/'gup6_finish.py').read_text())
finish()
