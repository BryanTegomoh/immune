import os
import tempfile
import unittest
from unittest.mock import patch
os.environ['IMMUNE_RUNS_DIR']=tempfile.mkdtemp(prefix='immune-test-')
from immune.core import cases,validate_dataset,make_datum,score,parse_label,prompt
from immune import engine

class Tokenizer:
    eos_token_id=0
    def encode(self,s,add_special_tokens=False): return [ord(c) for c in s]

class Integrity(unittest.TestCase):
    def test_heldout_cannot_be_corrected(self):
        with self.assertRaises(ValueError): engine.correct('H01','SHIP','tamper')
    def test_splits_and_prompt_have_no_answer(self):
        data=cases(); validate_dataset(data)
        self.assertEqual(len([c for c in data if c['split']=='heldout']),12)
        for c in data:
            self.assertNotIn('rationale',prompt(c)); self.assertNotIn('label',prompt(c))
    def test_completion_alignment(self):
        d=make_datum(Tokenizer(),'abc','SHIP')
        self.assertEqual(len(d['input_ids']),len(d['weights']))
        self.assertEqual(len(d['input_ids']),len(d['target_tokens']))
        trained=[t for t,w in zip(d['target_tokens'],d['weights']) if w]
        self.assertEqual(trained,[ord(c) for c in 'SHIP']+[0])
    def test_all_escalate_does_not_look_perfect(self):
        rows=[{'expected':c['label'],'predicted':'ESCALATE'} for c in cases() if c['split']=='heldout']
        m=score(rows)
        self.assertEqual(m['correct'],4);self.assertEqual(m['unnecessary_escalations'],4)
    def test_invalid_output_never_silently_escalates(self):
        self.assertEqual(parse_label('I say SHIP or REVISE'),'INVALID')
        self.assertEqual(parse_label(' REVISE\n'),'REVISE')
    def test_training_requires_credentials(self):
        with patch.dict(os.environ,{'RIVER_API_KEY':''}):
            with self.assertRaises(ValueError):engine.start('train')
    def test_revision_invalidates_memory_receipt(self):
        engine.correct('T01','REVISE','First review')
        engine.STATE['corrections']['T01']['gbrain_receipt']={'id':'old'}
        engine.correct('T01','REVISE','Corrected review')
        self.assertNotIn('gbrain_receipt',engine.STATE['corrections']['T01'])
    def test_unknown_label_is_rejected(self):
        with self.assertRaises(ValueError):engine.correct('T01','PASS','review')

if __name__=='__main__':unittest.main()
