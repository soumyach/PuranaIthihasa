"""Offline research validation. No network or third-party dependencies."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTITY_TYPES = set('DEITY DEVI_FORM MANIFESTATION ASURA PERSON SAGE DEVOTEE FAMILY ARMY WEAPON YANTRA BOON POWER PLACE VAHANA TEXT PASSAGE EVENT NAME EPITHET CONCEPT TRADITION'.split())
EVIDENCE_TYPES = set('DIRECT_TEXT TRADITION COMMENTARY SCHOLARLY_ANALYSIS INFERENCE UNVERIFIED'.split())
STATUSES = {'VERIFIED', 'NEEDS_REVIEW', 'REJECTED'}
TABLES = ['entities','assertions','relationships','boons_and_powers','narrative_events','story_spines','variants_and_conflicts']

def load_graph(root=ROOT):
    registry=json.loads((root/'source_registry.json').read_text())
    d={k:registry[k] for k in ['sources','witnesses']}
    for k in TABLES+['passages','evidence']:
        d[k]=json.loads((root/f'{k}.json').read_text())
    coverage=json.loads((root/'source_coverage.json').read_text())
    d['coverage']=coverage['records']
    d['chapter_coverage']=coverage.get('chapter_coverage',[])
    d['queue']=json.loads((root/'extraction_queue.json').read_text())['tasks']
    return d

def validate(d):
    errors=[]; warnings=[]; idx={}
    def err(message): errors.append(message)
    for table in ['sources','witnesses','passages','evidence']+TABLES:
        values=d.get(table,[])
        if not isinstance(values,list): err(f'{table}: expected array'); continue
        ids=[r.get('id') for r in values]
        for key,n in Counter(ids).items():
            if not isinstance(key,str) or not key: err(f'{table}: missing/string ID')
            elif n>1: err(f'{table}: duplicate {key}')
        idx[table]={r.get('id'):r for r in values}
    all_ids=[x for table in idx.values() for x in table]
    for key,n in Counter(all_ids).items():
        if n>1: err(f'Global ID collision: {key}')
    def ref(row,key,table,required=True):
        value=row.get(key)
        if value is None and not required: return
        if value not in idx.get(table,{}): err(f'{row.get("id", "coverage")}: {key}={value} missing from {table}')
    def refs(row,key,table,nonempty=False):
        values=row.get(key,[])
        if not isinstance(values,list): err(f'{row.get("id")}: {key} must be array'); return
        if nonempty and not values: err(f'{row.get("id")}: missing {key}')
        for value in values:
            if value not in idx.get(table,{}): err(f'{row.get("id")}: {key} references absent {table} {value}')
    def evidence(row,required=True):
        refs(row,'evidence_ids','evidence',required)
        status=row.get('verification_status')
        if status is not None and status not in STATUSES: err(f'{row.get("id")}: invalid verification status {status}')
        if status=='VERIFIED':
            for eid in row.get('evidence_ids',[]):
                e=idx['evidence'].get(eid,{})
                if e.get('verification_status')!='VERIFIED' or e.get('classification')=='UNVERIFIED': err(f'{row["id"]}: VERIFIED without verified supporting evidence {eid}')
    for w in d['witnesses']:
        ref(w,'source_id','sources')
        if w.get('automated_extraction') not in {'ALLOWED','NOT_ESTABLISHED','DISALLOWED'}: err(f'{w["id"]}: invalid extraction-access status')
    for p in d['passages']:
        ref(p,'source_id','sources'); ref(p,'witness_id','witnesses')
        if idx['witnesses'].get(p.get('witness_id'),{}).get('source_id')!=p.get('source_id'): err(f'{p["id"]}: witness/source mismatch')
        if not p.get('url') or not p.get('locator'): err(f'{p["id"]}: missing precise accessible locator')
        if p.get('extraction_status') not in {'UNEXAMINED','PARTIAL','COMPLETE'}: err(f'{p["id"]}: invalid extraction status')
    for e in d['evidence']:
        for key,table in [('source_id','sources'),('witness_id','witnesses'),('passage_id','passages')]: ref(e,key,table)
        p=idx['passages'].get(e.get('passage_id'),{})
        if any(p.get(k)!=e.get(k) for k in ['source_id','witness_id']): err(f'{e["id"]}: evidence/passage mismatch')
        if not e.get('locator') or not(e.get('paraphrase') or e.get('excerpt')): err(f'{e["id"]}: missing locator or evidence text')
        if e.get('classification') not in EVIDENCE_TYPES: err(f'{e["id"]}: invalid evidence classification')
        if e.get('verification_status') not in STATUSES: err(f'{e["id"]}: invalid verification status')
        if e.get('classification') in {'INFERENCE','UNVERIFIED'} and e.get('verification_status')=='VERIFIED': warnings.append(f'{e["id"]}: interpretation verified as interpretation; not direct-text certainty')
    for n in d['entities']:
        if n.get('type') not in ENTITY_TYPES: err(f'{n["id"]}: invalid entity type {n.get("type")}')
        ref(n,'source_scope','sources'); evidence(n)
        for alias in n.get('aliases',[]):
            if isinstance(alias,dict): refs(alias,'evidence_ids','evidence',True)
            else: warnings.append(f'{n["id"]}: bare alias lacks individual evidence')
    for r in d['assertions']+d['relationships']:
        ref(r,'subject_id','entities'); ref(r,'object_id','entities',r in d['relationships']); evidence(r)
        if not r.get('predicate'): err(f'{r["id"]}: missing predicate')
        if r in d['relationships'] and r.get('assertion_id'): ref(r,'assertion_id','assertions')
        if r in d['relationships'] and r.get('assertion_id') in idx['assertions']:
            a=idx['assertions'][r['assertion_id']]
            if any(a.get(k)!=r.get(k) for k in ['subject_id','predicate','object_id']): err(f'{r["id"]}: relationship/assertion mismatch')
    for b in d['boons_and_powers']:
        evidence(b)
        for key in ['recipient_id','grantor_id','worshipped_id']: ref(b,key,'entities',key=='recipient_id')
        refs(b,'later_event_ids','narrative_events')
        for key in ['requested','granted','mechanism','trigger','restrictions','duration','counter','motive','austerity_or_circumstances']:
            if key not in b: err(f'{b["id"]}: missing boon/power field {key}; null required if unstated')
            if b.get(key) is not None and not b.get('field_evidence',{}).get(key): err(f'{b["id"]}: populated {key} lacks field evidence')
        for key,values in b.get('field_evidence',{}).items(): refs({'id':b['id'],'evidence_ids':values},'evidence_ids','evidence',True)
        for key,values in b.get('field_evidence',{}).items():
            if not set(values).issubset(b.get('evidence_ids',[])): err(f'{b["id"]}: field evidence outside record evidence for {key}')
    by_story=defaultdict(list)
    for ev in d['narrative_events']:
        for key,table in [('source_id','sources'),('witness_id','witnesses'),('story_id','story_spines')]: ref(ev,key,table)
        for key,table in [('passage_ids','passages'),('participants','entities'),('changed_relationship_ids','relationships'),('introduced_entity_ids','entities'),('introduced_power_ids','boons_and_powers')]: refs(ev,key,table,key=='passage_ids')
        evidence(ev)
        for key in ['cause','details','outcome','consequences','setting']:
            if key not in ev: err(f'{ev["id"]}: event missing {key}')
        if not isinstance(ev.get('sequence'),int) or ev['sequence']<1: err(f'{ev["id"]}: invalid sequence')
        if not ev.get('details'): err(f'{ev["id"]}: empty narrative record')
        if idx['witnesses'].get(ev.get('witness_id'),{}).get('source_id')!=ev.get('source_id'): err(f'{ev["id"]}: primary witness/source mismatch')
        refs(ev,'supporting_witness_ids','witnesses')
        for pid in ev.get('passage_ids',[]):
            p=idx['passages'].get(pid,{})
            if p.get('source_id')!=ev.get('source_id'): err(f'{ev["id"]}: event/passage source mismatch')
            if p.get('witness_id') not in ev.get('supporting_witness_ids',[]): err(f'{ev["id"]}: passage witness absent from supporting witnesses')
        by_story[ev.get('story_id')].append(ev)
    for story in d['story_spines']:
        ref(story,'source_id','sources');ref(story,'witness_id','witnesses');refs(story,'event_ids','narrative_events',True)
        events=[idx['narrative_events'][eid] for eid in story.get('event_ids',[]) if eid in idx['narrative_events']]
        sequence=[ev['sequence'] for ev in events]
        if sequence!=sorted(set(sequence)): err(f'{story["id"]}: spine event order must be strictly increasing source narration order')
        if len(story.get('event_ids',[]))!=len(set(story.get('event_ids',[]))): err(f'{story["id"]}: duplicate event in spine')
        if any(ev.get('source_id')!=story.get('source_id') for ev in events): err(f'{story["id"]}: contains event from another source')
        if {ev['id'] for ev in by_story.get(story['id'],[])}!=set(story.get('event_ids',[])): err(f'{story["id"]}: spine/event membership mismatch')
        if any(ev.get('story_id')!=story['id'] for ev in events): err(f'{story["id"]}: contains event from another story')
        if not story.get('scope') or not story.get('completeness_basis'): err(f'{story["id"]}: missing scope/completeness basis')
        if story.get('status')=='COMPLETE' and story.get('missing_sections'): warnings.append(f'{story["id"]}: declared spine complete but other extraction gaps remain; inspect separate completeness axes')
    for c in d.get('coverage',[]):
        ref(c,'source_id','sources');ref(c,'witness_id','witnesses')
        for key in ['read_passage_ids','completely_extracted_passage_ids','partially_extracted_passage_ids']: refs(c,key,'passages')
        if set(c.get('completely_extracted_passage_ids',[])) & set(c.get('partially_extracted_passage_ids',[])): err(f'{c["source_id"]}: complete and partial coverage overlap')
        for pid in c.get('completely_extracted_passage_ids',[]):
            if idx['passages'].get(pid,{}).get('extraction_status')!='COMPLETE':err(f'{c["source_id"]}: coverage overclaims COMPLETE passage {pid}')
    chapter_keys=set()
    for c in d.get('chapter_coverage',[]):
        ref(c,'source_id','sources');ref(c,'witness_id','witnesses')
        refs(c,'passage_ids','passages');refs(c,'evidence_ids','evidence')
        key=(c.get('source_id'),c.get('witness_id'),c.get('book'),str(c.get('chapter')))
        if key in chapter_keys: err(f'chapter coverage: duplicate {key}')
        chapter_keys.add(key)
        if c.get('state') not in {'NOT_STARTED','IN_PROGRESS','PARTIAL','COMPLETE','BLOCKED'}:
            err(f'chapter coverage: invalid state {key}')
        if c.get('state')=='COMPLETE':
            for field in ['read_entire_chapter','narrative_extracted','characters_extracted','relationships_extracted','boons_powers_extracted','checked']:
                if c.get(field) is not True: err(f'chapter coverage COMPLETE without {field}: {key}')
            if not c.get('passage_ids') or not c.get('evidence_ids'): err(f'chapter coverage COMPLETE lacks passage/evidence: {key}')
        if c.get('state')=='BLOCKED' and not c.get('blocking_reason'): err(f'chapter coverage BLOCKED without reason: {key}')
        for pid in c.get('passage_ids',[]):
            p=idx['passages'].get(pid,{})
            if p.get('source_id')!=c.get('source_id') or p.get('witness_id')!=c.get('witness_id'):
                err(f'chapter coverage passage source/witness mismatch: {pid}')
    for v in d['variants_and_conflicts']:
        refs(v,'source_ids','sources');refs(v,'evidence_ids','evidence')
    return {'passed':not errors,'errors':errors,'warnings':warnings,'scope':'Structural validation; does not establish textual truth or exhaustive extraction.'}

def stats(d):
    verified=lambda rows: sum(r.get('verification_status')=='VERIFIED' for r in rows)
    evidence_index={e['id']:e for e in d['evidence']}
    counts={'sources_registered':len(d['sources']),'witnesses_registered':len(d['witnesses']),'sources_with_passage_reading':len({p['source_id'] for p in d['passages'] if p.get('reading_status') in {'READ','PARTIALLY_READ'}}),'passages_registered':len(d['passages']),'passages_fully_extracted':sum(p.get('extraction_status')=='COMPLETE' for p in d['passages']),'passages_partially_extracted':sum(p.get('extraction_status')=='PARTIAL' for p in d['passages']),'entities':len(d['entities']),'entities_with_verified_evidence':sum(bool(n.get('evidence_ids')) and all(evidence_index.get(i,{}).get('verification_status')=='VERIFIED' for i in n['evidence_ids']) for n in d['entities']),'assertions_verified_against_witness':verified(d['assertions']),'relationships_verified_against_witness':verified(d['relationships']),'kinship_relationships_verified':verified([r for r in d['relationships'] if r['predicate'] in {'parent_of','child_of','spouse_of','sibling_of','elder_sibling_of','parent','spouse','sibling','child'}]),'boons_verified':verified([b for b in d['boons_and_powers'] if b['type']=='BOON']),'powers_verified':verified([b for b in d['boons_and_powers'] if b['type']=='POWER']),'events_with_records':len(d['narrative_events']),'events_verified_against_witness':verified(d['narrative_events']),'story_spines':len(d['story_spines']),'story_spine_statuses':dict(Counter(s.get('status') for s in d['story_spines'])),'variant_records':len(d['variants_and_conflicts'])}

    counts.update(content_entities=sum(not n.get('documentary_node') for n in d['entities']),documentary_entities=sum(bool(n.get('documentary_node')) for n in d['entities']),content_assertions_verified_against_witness=verified([r for r in d['assertions'] if r.get('claim_kind')!='DOCUMENTARY_GRAPH_LINK']),content_relationships_verified_against_witness=verified([r for r in d['relationships'] if r.get('claim_kind')!='DOCUMENTARY_GRAPH_LINK']),source_examination_statuses=dict(Counter(s.get('examination_status') for s in d['sources'])))
    return counts

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    graph=load_graph(args.root);report=validate(graph);report['counts']=stats(graph)
    print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)
