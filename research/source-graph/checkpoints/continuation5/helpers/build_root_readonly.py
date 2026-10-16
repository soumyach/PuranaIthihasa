import json,copy
from pathlib import Path
W=Path('work/continuation5');D=json.loads((W/'baseline/research/graph.json').read_text())
x={'passages':[],'chapter_coverage':[],'changes':[],'updates':[],'notes':'Root next-chapter fragments actually read during bounded independent review, but not formally extracted. No narrative claims or COMPLETE states created from reconnaissance.','inspected_urls':[]}
for key,wid,ch,verses,url,om in [
 ('upasana81','gp-wit-sd-upasana',81,'1–14;15a incidentally read','https://sanskritdocuments.org/doc_purana/gaNeshapurANam1.html','81.1–14 and15a read-only; formal whole-chapter extraction must resume81.1.15b onward unread.'),
 ('krida64','gp-wit-sd-krida',64,'1–9','https://sanskritdocuments.org/doc_purana/gaNeshapurANam2.html','64.1–9 read-only; formal whole-chapter extraction must resume64.1.10 onward unread.'),
 ('mudgala2-27','gp-wit-sd-mudgala-2',27,'1–11','https://sanskritdocuments.org/doc_purana/mudgalapurANam2.html','2.27.1–11 read-only; formal whole-chapter extraction must resume2.27.1.12 onward unread.')]:
 author_rows=[r for n in ['gup6','gkr6','mud6'] for r in json.loads((W/'patches'/f'{n}.json').read_text()).get('chapter_coverage',[]) if r.get('witness_id')==wid and r.get('chapter')==ch]
 if author_rows and (author_rows[-1]['read_entire_chapter'] or author_rows[-1]['state'] in ['COMPLETE','PARTIAL']):
  continue # Stronger whole-body record takes precedence, without downgrade.
 c=copy.deepcopy(author_rows[-1] if author_rows else next(r for r in D['chapter_coverage'] if r['witness_id']==wid and r['chapter']==ch));pid='rfix5-p-readonly-'+key
 label=('Upāsanā' if key.startswith('upasana') else 'Krīḍā' if key.startswith('krida') else 'Mudgala2.')+str(ch)+'.'+verses
 x['passages'].append(dict(id=pid,source_id=c['source_id'],witness_id=wid,book=c['book'],khanda=c['khanda'],chapter=ch,verses=verses,url=url,locator=label,reading_status='PARTIALLY_READ',extraction_status='UNEXAMINED',limitations='Root actually read only the bounded fragment. '+om))
 c.update(state='IN_PROGRESS',passage_ids=list(dict.fromkeys(c.get('passage_ids',[])+[pid])),omissions=[om,'Narrative events, character relations, boons and powers have not been formally extracted from this read-only span.']);c['independent_review_notes']='Root bounded reconnaissance extends the author fragment where recorded; formal extraction remains unperformed.';x['chapter_coverage'].append(c);x['changes'].append('Registered read-only '+label+'; no completeness or extracted-claim inference.');x['inspected_urls'].append(url)
c=copy.deepcopy(next(r for r in D['chapter_coverage'] if r['witness_id']=='gp-wit-sd-upasana' and r['chapter']==71))
c['omissions']=['71.19 Kārtavīrya performer naming and exact named royal outcome recipients require collation. Local72 father/child naming and73 actual bodily remedy/reunion are now extracted; they do not settle the earlier71 named-performer/outcome conflict.']
x['chapter_coverage'].append(c)
x['changes'].append('Corrected stale chapter71 claim that72 is unextracted; retained PARTIAL performer/recipient uncertainty and exact earlier evidence.')
(W/'patches/rfix5.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print('Registered',len(x['passages']),'root bounded read-only fragments; author-owned frontier retained.')
