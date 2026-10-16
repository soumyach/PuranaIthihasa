import json,pathlib
P=pathlib.Path(__file__).parent
OLD=json.loads((P.parents[2]/'outputs/research/graph.json').read_text())
SID='gp-src-ganesha';WID='gp-wit-sd-upasana';URL='https://sanskritdocuments.org/doc_purana/gaNeshapurANam1.html'
d={k:[]for k in ['sources','witnesses','passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events','story_spines','variants_and_conflicts','coverage','queue','updates','chapter_coverage']}
names={}
for a in OLD['entities']:
 if a['source_scope']==SID and not a.get('documentary_node'):names.setdefault(a['name'],a['id'])
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
   if e not in u['fields']['evidence_ids']:u['fields']['evidence_ids'].append(e)
   if e not in u['evidence_ids']:u['evidence_ids'].append(e)
  elif e not in entityrows[i]['evidence_ids']:entityrows[i]['evidence_ids'].append(e)
  return i
 i='gup2-en-'+str(len(d['entities'])+1).zfill(3);names[name]=i
 a=dict(id=i,name=name,type=typ,source_scope=SID,aliases=[],evidence_ids=[e]);d['entities'].append(a);entityrows[i]=a;return i
def ev(ch,verses,text,actors,story='gup2-story-grtsamada',cause=None,outcome=None,status='VERIFIED'):
 p='gup2-p-'+str(ch)+'-'+verses.replace('–','-').replace(' ','')
 e='gup2-e-'+str(len(d['evidence'])+1).zfill(3)
 d['passages'].append(dict(id=p,source_id=SID,witness_id=WID,book='Gaṇeśa Purāṇa',khanda='Upāsanākhaṇḍa',chapter=ch,verses=verses,url=URL,locator=f'Upāsanā {ch}.{verses}',reading_status='READ',extraction_status='PARTIAL',limitations='Witness-level bounded extraction; chapter completeness separately checked.'))
 d['evidence'].append(dict(id=e,source_id=SID,witness_id=WID,passage_id=p,locator=f'Upāsanā {ch}.{verses}',paraphrase=text,classification='DIRECT_TEXT',verification_status=status,verifier='Upāsanā continuation agent',verification_notes='Direct Sanskrit body reading; not independent edition verification. Uncertain Sanskrit clauses identified separately.'))
 ids=[en(n,t,e)for n,t in actors]
 i='gup2-event-'+str(len(d['narrative_events'])+1).zfill(3)
 d['narrative_events'].append(dict(id=i,source_id=SID,witness_id=WID,supporting_witness_ids=[WID],story_id=story,sequence=len(d['narrative_events'])+1,passage_ids=[p],participants=ids,setting=None,cause=cause,details=text,outcome=outcome,changed_relationship_ids=[],introduced_entity_ids=[],introduced_power_ids=[],consequences=[],evidence_ids=[e],verification_status=status))
 return e,i
def rel(s,p,o,e,kind=None):
 i='gup2-rel-'+str(len(d['relationships'])+1).zfill(3);a='gup2-a-'+str(len(d['assertions'])+1).zfill(3)
 row=dict(id=i,subject_id=names[s],predicate=p,object_id=names[o],evidence_ids=[e],verification_status='VERIFIED',assertion_id=a)
 if kind:row['kinship_kind']=kind
 d['relationships'].append(row)
 d['assertions'].append(dict(id=a,subject_id=names[s],predicate=p,object_id=names[o],value=None,evidence_ids=[e],verification_status='VERIFIED'))
 return i
def val(s,p,value,e):
 d['assertions'].append(dict(id='gup2-a-'+str(len(d['assertions'])+1).zfill(3),subject_id=names[s],predicate=p,object_id=None,value=value,evidence_ids=[e],verification_status='VERIFIED'))
def power(rec,e,event,typ='POWER',grant=None,**kw):
 a=dict(id='gup2-power-'+str(len(d['boons_and_powers'])+1).zfill(3),type=typ,recipient_id=names[rec],grantor_id=names.get(grant),worshipped_id=None,motive=None,austerity_or_circumstances=None,requested=None,granted=None,mechanism=None,trigger=None,restrictions=None,duration=None,counter=None,later_event_ids=[],evidence_ids=[e],field_evidence={},verification_status='VERIFIED',notes='Null means unstated in examined passage, not independently proven absent from whole work. Reported efficacy is a POWER unless an explicit personal boon is narrated.')
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
 p='gup2-p-review-'+str(ch)+'-'+str(len(d['evidence'])+1)
 e='gup2-e-'+str(len(d['evidence'])+1).zfill(3)
 d['passages'].append(dict(id=p,source_id=SID,witness_id=WID,book='Gaṇeśa Purāṇa',khanda='Upāsanākhaṇḍa',chapter=ch,verses=verses,url=URL,locator=f'Upāsanā {ch}.{verses}',reading_status='READ',extraction_status='PARTIAL',limitations='Collation excerpt; whole chapter completeness separate.'))
 d['evidence'].append(dict(id=e,source_id=SID,witness_id=WID,passage_id=p,locator=f'Upāsanā {ch}.{verses}',paraphrase=text,classification='DIRECT_TEXT',verification_status=status,verifier='Upāsanā continuation2 author',verification_notes='Direct reread; transcription observed, unresolved interpretation not asserted.'))
 return e
def variant(i,text,e):
 d['variants_and_conflicts'].append(dict(id='gup2-var-'+i,type='SOURCE_LOCAL_READING_UNCERTAINTY',description=text,source_ids=[SID],evidence_ids=[e],status='OPEN',resolution=None))
# Direct rereads of the earlier flagged loci. No conjectural emendation is promoted.
e=note_evidence(3,'25–27,33','Reread confirms positive paropakāra instruction followed by contradictory negative paropakāra clause25; enumerated prohibited conduct26 lacks a securely attached negative in27, where own-wife abandonment wording also appears.33 describes marching at another’s distress and spies/messengers/ready punishment; reading adhamaṃ remains textually problematic. Neither ethical reversal nor a corrected Sanskrit reading is silently supplied.')
variant('chapter3-negative','3.25–27,33 remain malformed/ambiguous in the electronic witness; alternate chapter links were not accessible. Earlier NEEDS_REVIEW event remains unchanged.',e)
e=note_evidence(11,'24–28','Mantra disclosure is forbidden to atheistic, censorious, cruel, misconduct-prone, wicked and deceitful recipients24; positive list25 includes firm devotion, faith, humility, Vedic profession, desire, śāstra knowledge and the printed niranukrośe. Its ordinary uncompassionate sense conflicts with the list; no corrected recipient quality is established.27–28 separately promise offspring, wealth/grain, pure knowledge, enjoyment and final liberation to devotional reciters.')
variant('chapter11-recipient','Printed niranukrośe11.25 retained as an unresolved recipient criterion, without translating it into compassion or cruelty as authoritative policy.',e)
e=note_evidence(13,'25–27,44–46','13.26 contains malformed gaṇaśonyāṃ and matdyam strings in the Brahmā knowledge gift.44 describes Brahmā’s extraction;45 mentions nasal route and Hari following Brahmā, while45–46 continues Hara joined with Viṣṇu and ear-route extraction. Joint Sanskrit syntax does not independently fix each god’s route; the secure extraction and rest outcome remains separate.')
variant('chapter13-gift-route','Electronic witness13.26 gift word and13.44–46 route attachment require an alternate transcription/scan; prior gift/vision records retain their qualified content.',e)
e=note_evidence(23,'34–45','Reread preserves the tension:34 addresses Indumatī as next-life mother of this afflicted son;35 names Kalyāṇa/Vallabha and future Kamalā;36 names Dakṣa and Vallabha’s twelve-year attempt to cure him.45 confirms her Kamalā rebirth and only names the male a kṣatriya chief. No unambiguous mapping resolves the promised mother/son relationship against the named Vallabha role.')
u=next(x for x in OLD['variants_and_conflicts']if x['id']=='gup-var-ballala-rebirth')
update('variants_and_conflicts',u['id'],{'evidence_ids':u['evidence_ids']+[e],'resolution':'Direct reread confirms role tension; alternate accessible body not obtained. Remains OPEN; no biological/rebirth mapping promoted.'},'Rechecked23.34–45 without harmonization.',[e])
e=note_evidence(24,'5–8','Mudgala’s one-syllable mantra governs Dakṣa’s worship5. The electronic text6 explicitly prints twelve-year wording, followed by21days elapsed8 before the dream. The passage gives no connector establishing two distinct consecutive practices. Both statements remain recorded without a synthesized interval.')
u=next(x for x in OLD['variants_and_conflicts']if x['id']=='gup-var-daksa-duration')
update('variants_and_conflicts',u['id'],{'evidence_ids':u['evidence_ids']+[e],'resolution':'Direct reread confirms both expressions; no alternate body secured and no cumulative chronology asserted. Remains OPEN.'},'Rechecked24.5–8 without inferred duration.',[e])
# Mukundā and Gṛtsamada: actual parentage, attributed claims and social father separated.
e,v=ev(36,'1–11','Vyāsa asks about Mukundā after hearing Rukmāṅgada’s ascent. She remains consumed by desire, abandons food/water and sleeps exhausted in the forest. Indra knows her longing, assumes Rukmāṅgada’s form and has intercourse with her; she returns home believing the prince was her partner. Indra vanishes. She conceives and bears a beautiful son in the ninth month.',[('Vyāsa',S),('Brahmā',D),('Mukundā',F),('Rukmāṅgada',F),('Indra',D),('Gṛtsamada',S)],cause='Mukundā’s desire persists after the real prince’s departure.',outcome='Impersonation yields pregnancy; her belief is explicitly mistaken.')
rel('Gṛtsamada','child_of','Mukundā',e,'EXPLICIT_PARENTAGE');rel('Gṛtsamada','child_of','Indra',e,'NARRATED_BIOLOGICAL_PARENTAGE')
power('Indra',e,v,mechanism='Assumes the form of Rukmāṅgada.',trigger='Knowing Mukundā’s longing.',notes='Actual impersonation; Rukmāṅgada is not the narrated biological father.')
e,v=ev(36,'12–21 (17 printed7)','Birth resounds through earth, sky and directions and startles birds. Vācaknavi leaves his daily rites and, unaware of Mukundā’s conduct, joyfully performs birth rites and donations. After ten days he names the child Gṛtsamada with astrologer Brahmin approval; in the fifth year initiates him and performs four Vedic vows. The boy learns from a single utterance. Vācaknavi, called father in this social/ritual setting, teaches the Vedic Gaṇānāṃ tvā mantra, prescribing steady Gaṇeśa contemplation for success and fame.',[('Gṛtsamada',S),('Vācaknavi',S),('Mukundā',F),('Birth-rite Brahmins','FAMILY'),('Gaṇānāṃ tvā Vedic mantra',T),('Gaṇeśa',D)],cause='Vācaknavi believes the child belongs to his household.',outcome='Naming, initiation, learning and mantra instruction completed.')
rel('Vācaknavi','ritual_social_father_of','Gṛtsamada',e,'EXPLICIT_SOCIAL_FATHER_LABEL');rel('Vācaknavi','initiates','Gṛtsamada',e);rel('Vācaknavi','teaches_mantra','Gaṇānāṃ tvā Vedic mantra',e)
power('Gṛtsamada',e,v,mechanism='Learns Vedic material after a single utterance through brahmic radiance.',notes='Actual narrated learning capacity, separate from teacher’s prospective mantra-success assurance.')
e,v=ev(36,'22–32','Gṛtsamada practices mantra/meditation. King Magadha of Magadha, generous, martial and learned, with two unnamed learned ministers and devoted curse/grace-capable wife Ambikā, hosts his father’s śrāddha. Invited sages include Vasiṣṭha and Atri, and Gṛtsamada. His boast in śāstra discussion provokes Atri’s rebuke: ascetic merit earns respect, but alleged birth from prince Rukmāṅgada excludes equal sage-honour. Gṛtsamada flares with rage, others flee, and he threatens to burn the sages by curse if he proves not Rukmāṅgada’s son.',[('Gṛtsamada',S),('Magadha king',F),('Magadha',L),('Magadha’s two ministers','FAMILY'),('Ambikā (Magadha’s queen)',F),('Vasiṣṭha',S),('Atri',S),('Rukmāṅgada',F),('Invited śrāddha sages','FAMILY')],cause='Boast during learned discussion produces parentage rebuke.',outcome='He leaves to interrogate his mother; alleged parentage is attributed speech.')
rel('Magadha king','spouse_of','Ambikā (Magadha’s queen)',e,'EXPLICIT_MARRIAGE');rel('Magadha’s two ministers','minister_of','Magadha king',e)
val('Atri','attributed_parentage_claim','Claims Gṛtsamada is Rukmāṅgada’s son36.29; contradicted by narrator36.7–11,44.',e)
power('Ambikā (Magadha’s queen)',e,v,mechanism='Narrator characterizes the devoted queen as capable of curses and blessings.',notes='Characterized capacity; no specific curse/grace outcome by this queen enacted here.')
power('Gṛtsamada',e,v,mechanism='Threatens curse-fire reduction of sages to ashes.',trigger='Conditional proof he is not Rukmāṅgada’s son.',notes='Conditional threat only; no sages are actually burned in this passage.')
e,v=ev(36,'33–40','Gṛtsamada demands his father’s identity and threatens to burn Mukundā if she refuses. Frightened, she admits longing for the hunting prince while husband Vācaknavi was practicing, and believes Rukmāṅgada his father. Ashamed and angry, the son curses her to be a thorny forest plant with countless fruits shunned by all living creatures.',[('Gṛtsamada',S),('Mukundā',F),('Vācaknavi',S),('Rukmāṅgada',F),('Mukundā badarī tree',C)],cause='Alleged excluded lineage causes confrontation.',outcome='Mother receives curse; her father-identification remains attributed mistaken belief.')
val('Mukundā','attributed_parentage_belief','Says Rukmāṅgada is Gṛtsamada’s father36.38; narrator identifies Indra36.44.',e)
power('Mukundā',e,v,grant='Gṛtsamada',granted='Becomes thorny forest plant with innumerable fruits and avoidance by living creatures.',motive='Gṛtsamada’s anger at her conduct/parentage disclosure.',notes='Curse POWER; not voluntary boon.')
e,v=ev(36,'41–45','Mukundā counters that her son disregarded motherhood: he will father a terrible mighty daitya frightening three worlds. She immediately abandons her body and becomes a forest badarī avoided even by birds. Heavenly speech reveals Gṛtsamada was born from Indra. He leaves for austerity. Hearing this account promises freedom from distress and fulfilment.',[('Mukundā',F),('Gṛtsamada',S),('Mukundā badarī tree',C),('Indra',D),('Heavenly parentage voice',C),('Gṛtsamada-account listeners',C)],cause='Mother responds to curse with countercurse.',outcome='Plant transformation realized; true paternity revealed; future-son promise remains future.')
rel('Mukundā','transforms_into','Mukundā badarī tree',e);rel('Gṛtsamada','child_of','Indra',e,'HEAVENLY_VOICE_CONFIRMATION')
power('Gṛtsamada',e,v,grant='Mukundā',granted='Will father a mighty terrible daitya frightening three worlds.',motive='Disregarding motherhood by cursing mother.',notes='Countercurse; future son is not yet born within36.')
power('Gṛtsamada-account listeners',e,v,mechanism='Hearing this account averts distress and fulfils wishes.',trigger='Hearing account.')
e,v=ev(37,'1–8','Gṛtsamada reaches flower-rich Puṣpaka forest, bows to resident sages and stays with permission. Bathing, he fixes mind on Gaṇeśa, stands on a toe, restrains senses/breath/self, looks toward nose-tip and takes air. After1,000 divine years, opened eyes emit fire distressing gods who fear whose office he seeks. He then subsists on one fallen leaf, immobile, for a further15,000 as stated (the later clause gives number without repeating years).',[('Gṛtsamada',S),('Puṣpaka forest',L),('Puṣpaka sages','FAMILY'),('Gaṇeśa',D),('Gods',C),('Gṛtsamada eye-fire',W)],cause='Parentage humiliation drives intense austerity.',outcome='Long austerity and emitted fire draw divine attention.')
power('Gṛtsamada',e,v,mechanism='Opened eyes release fire distressing gods during austerity.',trigger='Opening eyes after1,000 divine years.')
e,v=ev(37,'9–23','Compassionate Gaṇeśa appears quickly, radiant, moon-browed, lion-mounted, ten-armed with serpent sacred cord and lotus garland, accompanied by Siddhi/Buddhi. His radiance overwhelms Gṛtsamada, who faints, resumes inward contemplation and fears his practice wasted; he begs rescue and recalls exclusion from sage honours. Gaṇeśa identifies himself as arriving for grace, praises toe-supported austerity and asks desired boon. The sage bows joyfully.',[('Gṛtsamada',S),('Gaṇeśa',D),('Gaṇeśa lion (Upāsanā37)','VAHANA'),('Siddhi (dakṣiṇā maiden)',F),('Buddhi (dakṣiṇā maiden)',F),('Sanaka',S),('Gaṇeśa lotus garland',C),('Gaṇeśa serpent sacred cord',C)],cause='Compassion rewards rigorous austerity.',outcome='Overwhelming vision becomes understood as grace, enabling request.')
rel('Gaṇeśa','rides','Gaṇeśa lion (Upāsanā37)',e);rel('Siddhi (dakṣiṇā maiden)','accompanies','Gaṇeśa',e);rel('Buddhi (dakṣiṇā maiden)','accompanies','Gaṇeśa',e)
e,v=ev(37,'24–34','Weeping and dancing, Gṛtsamada calls birth/austerity fulfilled. By deity’s command he asks Brahman-knowledge and knowledge, firm devotion and unforgetting remembrance, supremacy among devotees, exclusive devotional standing able to draw three worlds, worldwide honour by gods/humans. He asks Puṣpaka forest/city fame as Gaṇeśapura, continued divine residence and fulfilment of devotees’ wishes.',[('Gṛtsamada',S),('Gaṇeśa',D),('Puṣpaka forest',L),('Gaṇeśapura (Puṣpaka site)',L)],cause='Divine boon invitation.',outcome='Personal knowledge/devotion/honour and site requests articulated.')
e_req=e
e,v=ev(37,'35–43 (35 printed36)','Gaṇeśa affirms all requested things and grants rare Brahmin standing. Because he recited Gaṇānāṃ tvā, Gṛtsamada becomes that Vedic mantra’s ṛṣi; he gains supreme honour before Brahmā and Vasiṣṭha’s sages. Remembering him first then Gaṇeśa at undertakings yields success; ritual without deity/ṛṣi/metre knowledge is fruitless. A mighty famous son will terrify gods, be undefeatable by all except Rudra and remain Gaṇeśa-devoted. Site names are Puṣpaka in divine/Kṛta era as printed devayuga, Maṇipūra in Tretā, Bhānaka in Dvāpara and Bhadraka in Kali; bathing/giving there grants wishes.',[('Gṛtsamada',S),('Gaṇeśa',D),('Brahmā',D),('Vasiṣṭha',S),('Śiva',D),('Gaṇānāṃ tvā Vedic mantra',T),('Gaṇeśapura (Puṣpaka site)',L),('Maṇipūra',L),('Bhānaka',L),('Bhadraka',L),('Future Gṛtsamada son',A),('Gṛtsamada/Gaṇeśa remembrancers',C),('Puṣpaka bath/donation practitioners',C)],cause='Knowledge/devotion/site requests receive personal reply.',outcome='Personal and ritual standing granted; future son specified with Rudra exception.')
rel('Gṛtsamada','rsi_of','Gaṇānāṃ tvā Vedic mantra',e)
p=power('Gṛtsamada',e,v,typ='BOON',grant='Gaṇeśa',requested='Brahman/other knowledge, firm devotion/remembrance, supreme devotional honour and exclusive devotion, three-world attraction, city/forest fame, deity residence and devotees’ wish fulfilment.',granted='All requests affirmed; rare Brahmin standing, mantra-ṛṣi designation and supreme divine/sage honour explicitly added.',austerity_or_circumstances='Toe-supported air-diet1,000divine years then one-leaf immobility15,000 numbered interval37.1–8.',notes='Requested site and future-son effects are separately registered. Brahmin status personal grant; no retroactive biological-parentage alteration asserted.')
p['evidence_ids'] += [e_req, next(x['id']for x in d['evidence']if x['locator']=='Upāsanā 37.1–8')];p['field_evidence']['requested']=[e_req];p['field_evidence']['austerity_or_circumstances']=[p['evidence_ids'][-1]]
power('Future Gṛtsamada son',e,v,typ='BOON',grant='Gaṇeśa',requested=None,granted='Might, three-world fame, terror to gods and Gaṇeśa devotion; undefeatable by all gods except Rudra.',restrictions='Rudra explicitly excepted from invincibility.',notes='Unrequested future-son grant; realized birth begins38.')
power('Gṛtsamada/Gaṇeśa remembrancers',e,v,mechanism='Success at undertaken tasks through remembering Gṛtsamada first, then Gaṇeśa.',trigger='Prescribed ordered remembrance.',restrictions='Deity/ṛṣi/metre knowledge required for effective ritual as stated40.')
power('Puṣpaka bath/donation practitioners',e,v,mechanism='All wishes through bathing and giving at this site.',trigger='Bathing/donation there.')
e,v=ev(37,'44–48','Gaṇeśa vanishes after giving boons. Gṛtsamada installs his image, builds a fine temple, establishes enduring Varada name and worships devotedly. Site becomes a siddhi-place/Puṣpaka through divine favour. Listening to boon-account promises all wishes and firm Gaṇeśa devotion freeing transmigration.',[('Gṛtsamada',S),('Gaṇeśa',D),('Varada Gaṇeśa',D),('Puṣpaka forest',L),('Gaṇeśapura (Puṣpaka site)',L),('Varada-account listeners',C)],cause='Boon site request is realized through installation.',outcome='Actual temple, named cult image and worship close recognition/site arc.')
rel('Gṛtsamada','installs','Varada Gaṇeśa',e);rel('Gṛtsamada','worships','Gaṇeśa',e);rel('Varada Gaṇeśa','installed_at','Gaṇeśapura (Puṣpaka site)',e)
power('Varada-account listeners',e,v,mechanism='All wishes and firm liberating Gaṇeśa devotion through hearing this account.',trigger='Hearing Varada boon account.')
def finish():
 seen={x['id']for x in OLD['entities']}
 for z in d['narrative_events']:
  z['introduced_entity_ids']=[i for i in z['participants']if i not in seen];seen.update(z['participants'])
  z['changed_relationship_ids']=[r['id']for r in d['relationships']if set(r['evidence_ids'])&set(z['evidence_ids'])]
 for i,title,scope,status,missing in [('gup2-story-grtsamada','Gṛtsamada parentage, exclusion, curses, recognition and Varada site','Upāsanā36–37; child-promise continuation38 separate','COMPLETE',[]),('gup2-story-tripura','Tripura birth, boon, conquest and divine counterstrategy','Upāsanā38–47 and48.1–8festival boundary','PARTIAL',['46atomic names/implications and47.40chariot lexical collation pending; major warfare transition sequence through liberation/restoration read'])]:
  events=[x['id']for x in d['narrative_events']if x['story_id']==i]
  if not events:continue
  d['story_spines'].append(dict(id=i,title=title,source_id=SID,witness_id=WID,scope=scope,event_ids=events,status=status,completeness_basis='36–37 complete source bodies: paternity revelation, social exclusion, mother transformation, personal recognition/knowledge/devotion grant and actual temple installation37.45–47 close this bounded recognition/site arc; future son continues separately.'if i.endswith('grtsamada')else'Major source-order war transitions through actual liberation47.47, office/ritual restoration47.49–54 and festival boundary48.1–8 extracted; full46atomic-name claims and47.40chariot details unresolved, so formal arc remains PARTIAL.',missing_sections=missing,editorial_notes='Source narration order, including attributed mistaken father-identifications, does not turn reported belief into biological parentage.'))
 chapters=sorted({p['chapter']for p in d['passages']if p['chapter']>=36})
 for ch in chapters:
  ps=[p['id']for p in d['passages']if p['chapter']==ch];es=[e['id']for e in d['evidence']if e['passage_id']in ps]
  d['chapter_coverage'].append(dict(source_id=SID,witness_id=WID,book=None,khanda='Upāsanā',chapter=ch,state='PARTIAL'if ch in [45,46,47,48]else'COMPLETE',read_entire_chapter=False if ch==48 else True,narrative_extracted=False if ch==48 else True,characters_extracted=False if ch in [46,48]else True,relationships_extracted=False if ch in [46,48]else True,boons_powers_extracted=False if ch in [45,46,47,48]else True,checked=False if ch in [45,46,47,48]else True,passage_ids=ps,evidence_ids=es,omissions={45:['45.10 negative in without-remembrance clause requires alternate collation.'],46:['Whole body read; full1000name segmentation, kinship/śakti/weapon/numeric implications and21name inventory incomplete.'],47:['47.40 chariot material/driver clause malformed; alternate Sanskrit collation needed.'],48:['Only48.1–8 extracted;48.9–19and20first-line fragment read, no reunion extraction;48.20continuationonward unread.']}.get(ch,[]),blocking_reason=None,independent_review_status='NOT_INDEPENDENTLY_REVIEWED',independent_review_notes='Author direct body checking; alternate witness and independent review not claimed.'))
 for ch in [3,11,13,23,24]:
  row=next(c for c in OLD['chapter_coverage']if c['witness_id']==WID and c['chapter']==ch).copy()
  ps=[p['id']for p in d['passages']if p['chapter']==ch];es=[e['id']for e in d['evidence']if e['passage_id']in ps]
  row['passage_ids']=list(dict.fromkeys(row['passage_ids']+ps));row['evidence_ids']=list(dict.fromkeys(row['evidence_ids']+es));row['omissions']+=['Continuation2 targeted reread retains uncertainty; requested alternate chapter body not secured.']
  d['chapter_coverage'].append(row)
 last=max(chapters)if chapters else 35
 target='Upāsanā48.9–19and20first-line (read fragment, extraction pending);48.20continuationonward unread;then49–92;3/11/13/23/24/45/47collation;46atomic names/claims'
 d['queue']=[dict(id='gup2-queue-next',source_id=SID,passage_target=target,task='Continue sequential full bodies and nested arcs; complete Tripura war and Somakānta/Vyāsa outer frames; collate unresolved earlier readings against an actual alternate witness.',priority='P0-C',status='OPEN',dependency_ids=[],reason='Sequential progress continues; whole92-chapter witness remains incomplete.')]
 update('queue','gup-queue-next',{'status':'IN_PROGRESS','passage_target':target},f'Current checkpoint source-ordered extraction now extends through{last}; prior36 target superseded, whole request remains open.',[e['id']for e in d['evidence']if next(p['chapter']for p in d['passages']if p['id']==e['passage_id'])>=36])
 update('queue','gup-queue-ch3',{'status':'IN_PROGRESS'},'Five flagged chapters directly rechecked; no alternate body secured and none promoted COMPLETE.',[e['id']for e in d['evidence'][:5]])
 prior=next(x for x in OLD['coverage']if x['source_id']==SID and x['witness_id']==WID)
 d['coverage']=[dict(source_id=SID,witness_id=WID,known_sections=list(range(1,93)),read_passage_ids=prior['read_passage_ids']+[p['id']for p in d['passages']],completely_extracted_passage_ids=prior['completely_extracted_passage_ids'],partially_extracted_passage_ids=prior['partially_extracted_passage_ids']+[p['id']for p in d['passages']],unexamined_sections=['48.20continuationonward;49–92'],inventory_complete=True,narrative_extraction_complete=False,limitations=[f'Whole bodies1–47 read;48.1–19plus20first-linefragment only; existing30COMPLETE plus{sum(c['state']=='COMPLETE'for c in d['chapter_coverage']if c['chapter']>=36)}new COMPLETE chapters author-checked.','3/11/13/23/24 remain PARTIAL after direct reread; alternate chapter-body fetches unsuccessful.','No whole witness status upgrade; chapter author checking separate from independent review.'])]
 d['changes']=[f'Only new gup2 records plus explicit existing evidence/queue/conflict updates. New sequential extraction36–{last}.','Earlier five flagged chapters remain PARTIAL: no conjectural correction or role/duration harmonization promoted.']
 d['notes']='Current issued graph is baseline; prior IDs retained. Concise Sanskrit paraphrases only; no full text ingestion. Source order and nested past/future statements distinguished.'
 d['inspected_urls']=[URL,'https://sanskritdocuments.org/purana/','https://sarvakosh.com/hi/granth/ganesha-purana-gita-press/adhyay/तीसरा-अध्याय','https://sarvakosh.com/hi/granth/ganesha-purana-gita-press/adhyay/ग्यारहवाँ-अध्याय']
 (P/'gup2.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
 for key,ends in [('grtsamada-recognition-001',37),('tripura-war-transitions-002',48)]:
  cp=P.parent/'checkpoints/gup2'/f'{key}.json'
  if last>=ends and not cp.exists():cp.write_text(json.dumps(d,ensure_ascii=False,indent=2))
 counts={k:len(d[k])for k in ['passages','evidence','entities','assertions','relationships','boons_and_powers','narrative_events']}
 (P/'gup2.md').write_text('# Upāsanā continuation2\n\n'+str(counts)+f'\n\nNew whole bodies36–47read;36–44COMPLETE,45–47PARTIAL;48only1–8extracted/fragment read; earlier3/11/13/23/24 remain PARTIAL. No independent certification or whole92completion.\n\n'+ '\n'.join(f'- {s["title"]}: {s["status"]}; {s["scope"]}'for s in d['story_spines'])+'\n\nExact next: '+target+'\n\nBiological Indra parentage36.7–11/44, Vācaknavi social/ritual fatherhood36.14–21, and Atri/Mukundā mistaken prince-parentage statements36.29/38 remain separate. Gṛtsamada recognition ends37.45–47; son-promise belongs to continuation. Earlier checkpoints are append-only historical states; latest patch includes all explicit corrections.\n')
exec((P/'gup2_more.py').read_text())
exec((P/'gup2_finalwar.py').read_text())
finish()
