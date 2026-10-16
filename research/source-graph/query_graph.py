"""Inspect source-scoped research records with their evidence, offline."""
import argparse
import json
import unicodedata
from pathlib import Path
from validate_graph import load_graph, stats

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value)).casefold() if not unicodedata.combining(c))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['stats','sources','entities','relations','powers','story','evidence','gaps'])
    parser.add_argument('search',nargs='?',default='')
    parser.add_argument('--source',help='Exact source ID to restrict scope')
    parser.add_argument('--include-review',action='store_true',help='Include NEEDS_REVIEW and REJECTED claims')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();d=load_graph(args.root)
    idx={k:{r['id']:r for r in d[k]} for k in ['sources','witnesses','passages','evidence','entities','narrative_events','story_spines']}
    needle=normalize(args.search)
    def match(r): return not needle or needle in normalize(json.dumps(r,ensure_ascii=False))
    def scope(r):
        sid=r.get('source_id') or r.get('source_scope') or idx['entities'].get(r.get('subject_id') or r.get('recipient_id'),{}).get('source_scope')
        return not args.source or sid==args.source
    def status(r): return args.include_review or r.get('verification_status','VERIFIED')=='VERIFIED'
    def evidence(r):
        return [dict(**idx['evidence'][eid],passage=idx['passages'][idx['evidence'][eid]['passage_id']],witness=idx['witnesses'][idx['evidence'][eid]['witness_id']]) for eid in r.get('evidence_ids',[])]
    if args.command=='stats': out=stats(d)
    elif args.command=='sources': out=[dict(**s,witnesses=[w for w in d['witnesses'] if w['source_id']==s['id']]) for s in d['sources'] if match(s) and (not args.source or args.source==s['id'])]
    elif args.command=='entities': out=[dict(**n,support=evidence(n),relationships=[r for r in d['relationships'] if n['id'] in [r['subject_id'],r['object_id']] and status(r)]) for n in d['entities'] if match(n) and scope(n)]
    elif args.command in ['relations','powers']:
        table='relationships' if args.command=='relations' else 'boons_and_powers'
        out=[]
        for r in d[table]:
            related=[idx['entities'].get(r.get(k),{}) for k in ['subject_id','object_id','recipient_id','grantor_id','worshipped_id']]
            if scope(r) and status(r) and (match(r) or any(match(n) for n in related if n)):out.append(dict(**r,participants=related,support=evidence(r)))
    elif args.command=='story':
        out=[]
        for s in d['story_spines']:
            if match(s) and scope(s):out.append(dict(**s,events=[dict(**idx['narrative_events'][eid],support=evidence(idx['narrative_events'][eid])) for eid in s['event_ids']]))
    elif args.command=='evidence': out=[dict(**e,passage=idx['passages'][e['passage_id']]) for e in d['evidence'] if match(e) and scope(e) and status(e)]
    else:out=[c for c in d['coverage'] if scope(c) and match(c)]
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
