"""Exercise integrity guards using deliberately corrupted copies of the actual graph."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from validate_graph import load_graph, validate

ROOT=Path(__file__).resolve().parent
class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.graph=load_graph(ROOT)
    def rejects(self,mutate,fragment):
        d=copy.deepcopy(self.graph);mutate(d)
        result=validate(d)
        self.assertFalse(result['passed'])
        self.assertTrue(any(fragment in e for e in result['errors']),result['errors'])
    def test_issued_graph_valid(self): self.assertTrue(validate(self.graph)['passed'])
    def test_missing_evidence(self): self.rejects(lambda d:d['relationships'][0].update(evidence_ids=['absent-evidence']),'absent evidence')
    def test_dangling_endpoint(self): self.rejects(lambda d:d['relationships'][0].update(object_id='absent-entity'),'missing from entities')
    def test_wrong_evidence_witness(self): self.rejects(lambda d:d['evidence'][0].update(witness_id=d['witnesses'][-1]['id']),'evidence/passage mismatch')
    def test_reversed_story_order(self): self.rejects(lambda d:d['story_spines'][0]['event_ids'].reverse(),'strictly increasing')
    def test_missing_power_field(self): self.rejects(lambda d:d['boons_and_powers'][0].pop('restrictions'),'missing boon/power field restrictions')
    def test_incomplete_passage_overclaim(self):
        def mutate(d):
            p=next(p for p in d['passages'] if p['extraction_status']=='PARTIAL')
            d['coverage'].append(dict(source_id=p['source_id'],witness_id=p['witness_id'],completely_extracted_passage_ids=[p['id']]))
        self.rejects(mutate,'coverage overclaims COMPLETE')
    def test_duplicate_id(self): self.rejects(lambda d:d['entities'].append(copy.deepcopy(d['entities'][0])),'duplicate')
    def test_unread_chapter_cannot_be_complete(self):
        def mutate(d):
            r=next(r for r in d['chapter_coverage'] if r['state']=='COMPLETE')
            r['read_entire_chapter']=False
        self.rejects(mutate,'COMPLETE without read_entire_chapter')
    def test_unchecked_chapter_cannot_be_complete(self):
        def mutate(d):
            r=next(r for r in d['chapter_coverage'] if r['state']=='COMPLETE')
            r['boons_powers_extracted']=False
        self.rejects(mutate,'COMPLETE without boons_powers_extracted')
    def test_chapter_coverage_no_duplicate_units(self):
        self.rejects(lambda d:d['chapter_coverage'].append(copy.deepcopy(d['chapter_coverage'][0])),'chapter coverage: duplicate')
    def test_unverified_cannot_support_verified(self): self.rejects(lambda d:d['evidence'][0].update(verification_status='NEEDS_REVIEW'),'VERIFIED without verified supporting evidence')
    def query(self,*args):
        return json.loads(subprocess.check_output([sys.executable,str(ROOT/'query_graph.py'),*args],text=True))
    def test_bhanda_power_query_has_evidence(self):
        records=self.query('powers','Bhanda')
        self.assertTrue(records)
        self.assertTrue(all(r['support'] for r in records))
        self.assertTrue(any('half' in json.dumps(r,ensure_ascii=False).lower() for r in records))
    def test_frame_query_preserves_source_order(self):
        records=self.query('story','dm-story-frame')
        self.assertEqual(len(records),1)
        events=records[0]['events']
        self.assertEqual([e['sequence'] for e in events],[1,2,3,62,63,64])
        self.assertTrue(all(e['support'] for e in events))
    def test_mudgala_gaps_remain_visible(self):
        records=self.query('gaps','--source','gp-src-mudgala')
        self.assertTrue(records)
        self.assertTrue(any(not r.get('narrative_extraction_complete') for r in records))

if __name__=='__main__': unittest.main(verbosity=2)
