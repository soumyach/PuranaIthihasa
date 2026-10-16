import json, collections, shutil, hashlib, datetime, sys
from pathlib import Path
W=Path('work/continuation4');O=Path('outputs/research');B=W/'baseline/research'
sys.path.insert(0,str(O));import validate_graph as V
D=V.load_graph(O);base=V.load_graph(B);report=V.validate(D);assert report['passed'],report
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
core=[r for r in D['chapter_coverage'] if r['source_id'] in ['gp-src-ganesha','gp-src-mudgala']];assert len(core)==675
states=collections.Counter(r['state'] for r in core)
def ck(r):return r['source_id'],r['witness_id'],r.get('book'),str(r['chapter'])
oldch={ck(r):r for r in base['chapter_coverage']}
newch=[r for r in core if r['state']=='COMPLETE' and oldch[ck(r)]['state']!='COMPLETE']
dump('chapter_coverage_updates.json',[dict(identity=dict(source_id=r['source_id'],witness_id=r['witness_id'],book=r.get('book'),chapter=r['chapter']),before=oldch[ck(r)],after=r,evidence_ids=r.get('evidence_ids',[]),reason='Directly read incremental extraction or explicit incomplete read-only reconnaissance; statuses follow author checks and retained semantic omissions.') for r in D['chapter_coverage'] if oldch.get(ck(r))!=r])
finished=[r for r in D['story_spines'] if r['status']=='COMPLETE'];oldsp={r['id']:r for r in base['story_spines']}
newfinished=[r for r in finished if oldsp.get(r['id'],{}).get('status')!='COMPLETE']
corefinished=[r for r in finished if r['source_id'] in ['gp-src-ganesha','gp-src-mudgala']]
E={r['id']:r for r in D['evidence']};P={r['id']:r for r in D['passages']};EV={r['id']:r for r in D['narrative_events']}
pending={t:[r for r in D[t] if r.get('verification_status')=='NEEDS_REVIEW'] for t in ['evidence','assertions','relationships','boons_and_powers','narrative_events']}
reviews=[]
for f in sorted((W/'reviews').glob('*.json')):
    value=json.loads(f.read_text())
    if isinstance(value,dict) and any(k in value for k in ['review_units','findings','checks']):reviews.append(value)
dump('continuation4_independent_review.json',dict(reports=reviews,limits='Targeted sample review of primary witnesses, not independent certification of all assertions, doctrinal interpretation or print recensions. Earlier review files and resolutions remain intact.'))
changes=json.loads((O/'continuation4_change_records.json').read_text())
resolved=[r for r in changes if r['track'] in ['root-review-resolution','root-identity-reconciliation'] or r['track']=='rfix4']
finding_resolutions=[]
for review in reviews:
    for f in review.get('findings',[])+review.get('recommended_corrections',[])+review.get('checks',[]):
        status=f.get('status',f.get('verdict','RECOMMENDATION'))
        if not any(z in status for z in ['CORRECTION','PENDING','UNDETERMINED','REFINEMENT_RECOMMENDED']) and not f.get('suggested'):continue
        ids=[r['id'] for r in f.get('records',[])+f.get('affected_records',[])]+f.get('record_ids',[])+f.get('claim_ids',[])+f.get('checked_record_ids',[])
        matching=[r['id'] for r in resolved if r['record_id'] in ids]
        author_applied=bool(f.get('applied_before_author_freeze'))
        current=[dict(table=t,record=r) for t in V.TABLES+['evidence'] for r in D[t] if r['id'] in ids]
        resolution='RETAINED_PENDING_WITH_DOCUMENTED_ANNOTATION' if status.startswith('PENDING') and matching else ('RETAINED_PENDING' if status.startswith('PENDING') else ('APPLIED_WITH_DOCUMENTED_CHANGE' if matching else ('APPLIED_BEFORE_AUTHOR_FREEZE' if author_applied else 'RETAINED_PENDING')))
        finding_resolutions.append(dict(finding_id=f['id'],author_status=status,current_resolution=resolution,change_record_ids=matching,author_checkpoint=f.get('author_checkpoint') if author_applied else None,current_records=current,notes='The original bounded review and its compared hash remain preserved; this resolution records the current integrated values. Existing and newly flagged unresolved claims retain their exact statuses.'))
dump('continuation4_review_resolution.json',dict(record_update_ids=[r['id'] for r in resolved],finding_resolutions=finding_resolutions,details=resolved,unresolved='Exact remaining chapter omissions, open variants and NEEDS_REVIEW records are retained. All affected whole-scene story spines remain PARTIAL. Selective independent checks do not certify every new row.'))
dump('claims_needing_review.json',dict(explicit_NEEDS_REVIEW=pending,chapter_omissions=[r for r in D['chapter_coverage'] if r['state'] in ['PARTIAL','IN_PROGRESS','BLOCKED']],open_conflicts=[r for r in D['variants_and_conflicts'] if r.get('status') not in ['RESOLVED','CLOSED']],additional_review='All claims outside the bounded independent reports have not been universally second-author checked; textual VERIFIED means checked against their cited witness. Conflicts may have individually verified rival readings. Wider previous review reports remain authoritative for their own scope.'))
documented={(r['table'],r['record_id']) for r in changes};audit={}
for t in ['sources','witnesses','passages','evidence']+V.TABLES+['queue']:
    a={r['id']:r for r in base[t]};z={r['id']:r for r in D[t]};changed=[i for i in a if a[i]!=z.get(i)];missing=set(a)-set(z)
    undoc=[i for i in changed if (t,i) not in documented];assert not missing and not undoc,(t,missing,undoc)
    audit[t]=dict(baseline_ids=len(a),retained_ids=len(set(a)&set(z)),added_ids=len(set(z)-set(a)),changed_old_ids=changed,undocumented_changes=undoc)
dump('stable_id_audit.json',audit)
# Preserve earlier user-facing reports as an immutable checkpoint, including the prior spine export.
hist=O/'checkpoints/continuation4/issued_previous_reports';hist.mkdir(parents=True,exist_ok=True)
for n in ['COVERAGE_REPORT.md','VERIFICATION_REPORT.md','CHANGELOG.md','COMPLETE_STORY_SPINES.md','complete_story_spines.json','checkpoint_summary.json','stable_id_audit.json','verification_report.json']:
    if (B/n).exists():shutil.copyfile(B/n,hist/n)
lines=['# Complete bounded story spines — current checkpoint','',f'{len(newfinished)} newly completed this continuation; {len(finished)} total retained complete spines ({len(corefinished)} Gaṇeśa/Mudgala). Only explicit COMPLETE stories appear here; PARTIAL stories remain in graph.json and story_spines.json.','', 'Source narration order, including recalled events and advance summaries, is preserved. Unstated family, teacher, austerity or boon fields are not guessed. Exact relationships and field-specific boon evidence remain in the linked graph tables.','']
structured=[]
for s in finished:
    lines+=['## '+s['title'],'',f'ID: `{s["id"]}`. Scope: {s["scope"]}. Newly completed this continuation: {s in newfinished}.','',s['completeness_basis'],'']
    if s.get('editorial_notes'):lines+=[s['editorial_notes'],'']
    events=[];eids=set();actors=set()
    for i in s['event_ids']:
        ev=EV[i];support=[E[x] for x in ev['evidence_ids']];eids.update(ev['evidence_ids']);actors.update(ev['participants']);events.append(dict(event=ev,evidence=support))
        links='; '.join(f'[{e["locator"]}]({P[e["passage_id"]]["url"]})' for e in support)
        lines += [f'{ev["sequence"]}. **{ev["id"]}** — {ev["details"]} Outcome: {ev["outcome"]}. {links}','']
    # Associated rows share explicit event evidence; this is a navigation subset, not an invented completeness claim.
    structured.append(dict(story=s,newly_completed_this_continuation=s in newfinished,events=events,participant_entities=[r for r in D['entities'] if r['id'] in actors],event_evidence_relationships=[r for r in D['relationships'] if set(r['evidence_ids'])&eids],event_evidence_boons_and_powers=[r for r in D['boons_and_powers'] if set(r['evidence_ids'])&eids],navigation_note='Related-row subset uses shared event evidence. Graph tables retain narrower iconographic/ritual passages and all other source-local rows.'))
(O/'COMPLETE_STORY_SPINES.md').write_text('\n'.join(lines)+'\n');dump('complete_story_spines.json',structured)
def ranges(nums):
    nums=sorted(set(nums));groups=[]
    for n in nums:
        if groups and n==groups[-1][-1]+1:groups[-1].append(n)
        else:groups.append([n])
    return ', '.join(str(g[0]) if len(g)==1 else f'{g[0]}–{g[-1]}' for g in groups) or 'none'
rows=[]
for wid in ['gp-wit-sd-upasana','gp-wit-sd-krida']+[f'gp-wit-sd-mudgala-{i}' for i in range(1,10)]:
    rr=[r for r in core if r['witness_id']==wid];cc=collections.Counter(r['state'] for r in rr);rows.append((wid,rr,cc))
cl=['# Source coverage — continuation4','',f'**{len(newch)} new whole chapters fully processed this continuation. {states["COMPLETE"]}/675 Gaṇeśa/Mudgala chapters now COMPLETE; {675-states["COMPLETE"]} unfinished.**','',f'**{len(newfinished)} new complete bounded narrative arcs; {len(finished)} total retained complete arcs, including {len(corefinished)} Gaṇeśa/Mudgala arcs.** No complete-source claim.','', 'Whole-chapter COMPLETE requires complete body reading plus narrative, actor, relationship, boon/power extraction and checking. Significant unresolved claims keep chapters and affected story arcs PARTIAL. Unstarted and partly read bodies stay distinct.','', '| Witness | Chapters | COMPLETE | PARTIAL | IN_PROGRESS | NOT_STARTED | BLOCKED |','|---|---:|---:|---:|---:|---:|---:|']
for wid,rr,cc in rows:cl.append('|'+wid+'|'+str(len(rr))+'|'+ '|'.join(str(cc[s]) for s in ['COMPLETE','PARTIAL','IN_PROGRESS','NOT_STARTED','BLOCKED'])+'|')
cl += ['', '## Complete chapter ranges and additions','']
for wid,rr,cc in rows:cl.append(f'- {wid}: COMPLETE {ranges([r["chapter"] for r in rr if r["state"]=="COMPLETE"])}; newly completed {ranges([r["chapter"] for r in newch if r["witness_id"]==wid])}.')
cl += ['', '## Exact unfinished units with recorded work','']
for r in core:
    if r['state'] not in ['NOT_STARTED','COMPLETE']:cl.append(f'- {r["witness_id"]} chapter {r["chapter"]}: **{r["state"]}**; whole body read={r["read_entire_chapter"]}. '+'; '.join(r.get('omissions',[])))
cl += ['', '## Remaining source order','']
for wid,rr,cc in rows:cl.append(f'- {wid}: NOT_STARTED {ranges([r["chapter"] for r in rr if r["state"]=="NOT_STARTED"])}.')
cl += ['', 'Embedded Gaṇeśa Gītā Krīḍā138–148 remains counted once, with137/149 context retained. The standalone Gītā witness remains separately tracked. All nine indexed Mudgala khaṇḍas and428 chapters remain; ninth khaṇḍa41chapters is not discarded.','', 'Earlier Lalitopākhyāna, Devī Māhātmya, targeted Devī Bhāgavata and wider-corpus source registrations are unchanged in scope. Five previously read Devī Bhāgavata chapters remain PARTIAL; no additional corpus work was started this continuation. Exact queues are retained in extraction_queue.json.']
first=[r for r in core if r['witness_id']=='gp-wit-sd-mudgala-1'];fc=collections.Counter(r['state'] for r in first)
cl+=['',f'All 54 first-khaṇḍa Mudgala chapter bodies have now been read across retained checkpoints: {fc["COMPLETE"]} COMPLETE, {fc["PARTIAL"]} PARTIAL. Reading completion is separate from extraction completion.']
(O/'COVERAGE_REPORT.md').write_text('\n'.join(cl)+'\n')
root_units=sum(len(r.get('review_units',[])) for r in reviews)
vl=['# Verification report — continuation4','',f'Structural validation: **PASS** ({len(report["errors"])} errors, {len(report["warnings"])} warnings). All 15 existing integrity tests are rerun in integrity_test_results.txt. Stable-ID preservation and documentation of changed old rows: **PASS**.','',f'{len(reviews)} new independent review reports retained alongside earlier reviews; {root_units} bounded root review units. These are selective scopes, not an exhaustive unique-assertion count.','', 'Independent checks prioritize source-local parentage, initiation, austerity units, request versus grant, conditions, counters, surrender and outcomes. Field-specific corrections and completeness decisions retain before/after records; original review reports are preserved with resolutions.','', '## Explicit claims requiring review','']
for t,rs in pending.items():vl.append(f'- {t}: {len(rs)} — '+(', '.join(r['id'] for r in rs) or 'none'))
vl += ['', 'All current unresolved source claims, chapter omissions and open conflicts are enumerated in claims_needing_review.json. Supported rival readings can both be VERIFIED while their discrepancy remains OPEN. No remembered translation or other-work episode resolves an unread or malformed passage.','', 'Witness-level VERIFIED means checked against its cited passage. Independent review was selective, and alternate print recension/Sanskrit collation remains pending where flagged. Same-named actors in different source contexts are preserved separately; cosmological emanation is not silently biological lineage.','', 'Previous Lalitopākhyāna, Devī Māhātmya, Devī Bhāgavata and standalone Gītā reviews remain intact; this continuation adds no wider-corpus work.']
(O/'VERIFICATION_REPORT.md').write_text('\n'.join(vl)+'\n')
ch=['# Changelog — continuation4','',f'- Continued the issued 145-chapter checkpoint. Added {len(newch)} complete whole chapters and {len(newfinished)} complete bounded story/teaching arcs; totals now {states["COMPLETE"]}/675 chapters and {len(finished)} complete arcs across the retained graph.','- Preserved every issued ID, source/witness reference, prior verified assertion and wider-corpus registration; schema remains 0.1.0. Every changed existing row retains before/after values, reason and evidence.','- Advanced Upāsanā from 61, Krīḍā from 44 and Mudgala from 2.11 in source order, with complete chronology and exact evidence for significant characters, relationships, instructions, boons, powers and outcomes.','- Distinguished observed manifestation from installed image, narrated events from recalled examples, and requested powers from explicit grants. Unstated dialogue or battle strategies were not supplied.','- Kept significant lexical, actor, kinship and boon uncertainties PARTIAL in affected chapters and story scopes; corrections and source-context conflicts are explicit.','- Added append-only arc checkpoints, independent review/resolution records, current coverage and resumable queues. All 15 existing integrity tests were rerun.','- No website, UI, games, visuals, fiction, extra Purāṇas or wider-source extraction introduced.']
(O/'CHANGELOG.md').write_text('\n'.join(ch)+'\n')
(O/'README.md').write_text('# Khatakshetra Śākta Source Graph v0.1 — continuation4\n\nCurrent incremental checkpoint preserves the issued graph and schema.\n\n- graph.json and individual JSON tables: current evidence-backed records.\n- COVERAGE_REPORT.md / chapter_coverage.json: exact chapter counts, states and omissions.\n- COMPLETE_STORY_SPINES.md / complete_story_spines.json: all retained complete bounded arcs, with event evidence and new-arc flags. Partial arcs remain in story_spines.json.\n- VERIFICATION_REPORT.md / continuation4_independent_review.json: selective independent review and limits.\n- CHANGELOG.md / change_records.json / stable_id_audit.json: auditable corrections and preserved IDs.\n- extraction_queue.json / checkpoints/continuation4: precise resumption and frozen author patches.\n\nRun python3 validate_graph.py, then python3 -m unittest discover -s . -p test_integrity.py -v. COMPLETE witnesses, chapters and bounded arcs are distinct; no whole-corpus completion is claimed.\n')
cp=O/'checkpoints/continuation4';cp.mkdir(parents=True,exist_ok=True)
for n in ['checkpoints','patches','reviews']:shutil.copytree(W/n,cp/n,dirs_exist_ok=True)
shutil.copyfile(W/'CONTRACT.md',cp/'CONTRACT.md')
nextrows=[r for r in D['queue'] if r.get('status') not in ['DONE','COMPLETE','CLOSED']]
(cp/'RESUME.md').write_text('# Resume continuation4\n\nLoad current graph.json and chapter_coverage.json, retain IDs, and consult the precise extraction_queue.json tasks. Do not replay earlier continuation scripts against their older baseline. Frozen patches have already been integrated; do not append them twice.\n\nUnresolved chapter fields stay PARTIAL until supported; all NOT_STARTED chapters require actual body reading. Independent reports and resolutions retain their bounded scope.\n')
report.update(counts=V.stats(D),core_chapter_states=dict(states),newly_completed_chapters=len(newch),newly_completed_arcs=len(newfinished),total_complete_arcs=len(finished),baseline_ids_preserved=True);dump('verification_report.json',report)
summary=dict(continuation='continuation4',new_chapters_complete=len(newch),new_complete_arcs=len(newfinished),core_chapters_complete=states['COMPLETE'],core_chapters_remaining=675-states['COMPLETE'],core_chapter_states=dict(states),total_complete_arcs=len(finished),core_complete_arcs=len(corefinished),new_chapter_keys=[dict(witness_id=r['witness_id'],chapter=r['chapter']) for r in newch],new_complete_arc_ids=[r['id'] for r in newfinished],explicit_needs_review={t:len(rs) for t,rs in pending.items()},counts=V.stats(D));dump('checkpoint_summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
