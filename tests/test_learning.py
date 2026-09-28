import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from immune.learning import Policy, Store, cycle, evaluate, promotion_gate, signature, respond
from immune.verifier_feedback import verified_feedback


def suite():
    return [{'id': f'{kind}-{i}', 'group': f'eval-{kind}-{i}', 'suite': kind,
             'input': f'Unseen {kind} scenario {i}', 'expected': {'action': 'draft', 'text': 'A useful reply'}}
            for kind in ('target', 'retention', 'safety') for i in range(4)]


def feedback(i):
    return {'id': f'correction-{i}', 'group': f'work-{i}', 'input': f'Actual task {i}',
            'observed_output': '{"action":"send","text":"Unsupported commitment"}',
            'corrected_output': '{"action":"draft","text":"A useful reply"}'}


class FakeProvider:
    """Control-flow fixture ONLY. No model, weights, or provider claims."""
    identity = 'fixture:not-a-model'

    def __init__(self):
        self.parents = []
        self.batches = []
        self.fail = False
        self.regress = False
        self.on_train = None

    def evaluate(self, checkpoint, prompts, policy):
        if self.fail:
            raise RuntimeError('secret-must-never-be-persisted')
        # No expected fields may be sent into sampling.
        assert all(set(p) == {'id', 'input'} for p in prompts)
        outputs = {p['id']: '{"action":"draft","text":"A useful reply"}' for p in prompts}
        if not checkpoint.get('inference_checkpoint'):
            outputs['target-0'] = '{"action":"send"}'
        if self.regress and checkpoint.get('inference_checkpoint'):
            outputs['retention-0'] = '{"action":"send"}'
        return outputs

    def train(self, parent, examples, policy, attempt_id):
        self.parents.append(copy.deepcopy(parent)); self.batches.append(copy.deepcopy(examples))
        if self.on_train:
            self.on_train()
        return {'training_checkpoint': 'fixture://train/' + attempt_id,
                'inference_checkpoint': 'fixture://inference/' + attempt_id}

    def respond(self, active, prompt, policy):
        return 'Used ' + active['version'] + ' for ' + prompt


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.policy = Policy(trusted_verifiers=('test_runner',))
        self.provider = FakeProvider()
        self.store = Store(self.tmp.name + '/loop.sqlite', self.policy, suite(), self.provider.identity)

    def add(self, start=0):
        for i in (start, start + 1):
            self.store.ingest(feedback(i), human=True)

    def run_cycle(self):
        return cycle(self.store, self.provider, enabled=True)

    def test_disabled_and_insufficient_data_never_call_provider(self):
        self.add()
        self.assertEqual(cycle(self.store, self.provider)['status'], 'disabled')
        self.assertFalse(self.provider.parents)

    def test_waits_for_minimum_batch(self):
        self.store.ingest(feedback(0), human=True)
        self.assertEqual(self.run_cycle()['status'], 'waiting')

    def test_promotes_without_manual_candidate_approval(self):
        self.add()
        result = self.run_cycle()
        self.assertEqual(result['status'], 'promoted')
        self.assertNotEqual(self.store.active()['version'], 'base')
        self.assertEqual(self.store.status()['feedback']['accepted'], 2)

    def test_regression_rejects_even_if_target_improves(self):
        self.add(); self.provider.regress = True
        self.assertEqual(self.run_cycle()['status'], 'rejected')
        self.assertEqual(self.store.active()['version'], 'base')

    def test_next_task_uses_promoted_checkpoint(self):
        self.add(); self.run_cycle()
        result = respond(self.store, self.provider, 'my next task')
        self.assertEqual(result['checkpoint'], self.store.active()['inference_checkpoint'])
        self.assertIn(self.store.active()['version'], result['output'])

    def test_rejected_candidate_never_serves_next_task(self):
        self.add(); self.provider.regress = True; self.run_cycle()
        result = respond(self.store, self.provider, 'my next task')
        self.assertEqual(result['version'], 'base')
        self.assertIsNone(result['checkpoint'])

    def test_safety_failure_rejects(self):
        outputs = self.provider.evaluate({}, [{'id': c['id'], 'input': c['input']} for c in suite()], self.policy)
        before = evaluate(suite(), outputs)
        outputs['target-0'] = '{"action":"draft","text":"A useful reply"}'
        outputs['safety-0'] = 'unsafe'
        self.assertFalse(promotion_gate(before, evaluate(suite(), outputs), self.policy)['promote'])

    def test_no_gain_rejects(self):
        self.add(); self.run_cycle(); self.add(2)
        self.assertEqual(self.run_cycle()['status'], 'rejected')

    def test_restart_resumes_parent_and_replays_accepted_lessons(self):
        self.add(); self.run_cycle()
        parent = self.store.active()
        self.store = Store(self.store.path, self.policy, suite(), self.provider.identity)
        self.add(2); self.run_cycle()
        self.assertEqual(self.provider.parents[-1], parent)
        self.assertEqual(len(self.provider.batches[-1]), 4)
        self.assertEqual(self.provider.batches[-1][0]['corrected_output'], feedback(2)['corrected_output'])

    def test_rejected_lessons_do_not_enter_replay(self):
        self.add(); self.provider.regress = True; self.run_cycle()
        self.add(2); self.provider.regress = False; self.run_cycle()
        self.assertEqual(len(self.provider.batches[-1]), 2)

    def test_rolling_budget_counts_all_attempts(self):
        self.add(); self.run_cycle(); self.add(2); self.run_cycle(); self.add(4)
        self.assertEqual(self.run_cycle()['status'], 'budget_exhausted')

    def test_untrusted_and_self_asserted_verification_quarantined(self):
        record = {**feedback(0), 'source': 'human', 'verified_success': True}
        self.assertEqual(self.store.ingest(record)['status'], 'quarantined')
        self.assertEqual(self.store.ingest(feedback(1), verifier='test_runner', signed='fake')['status'], 'quarantined')
        self.assertEqual(self.run_cycle()['status'], 'waiting')

    def test_signed_feedback_and_tampering(self):
        key = 'fixture-key-never-use-in-production-12345'
        envelope = verified_feedback(feedback(0), lambda text: json.loads(text).get('action') == 'draft', key)
        with patch.dict(os.environ, {'IMMUNE_VERIFIER_KEY_TEST_RUNNER': key}):
            self.assertEqual(self.store.ingest(envelope['record'], verifier='test_runner', signed=envelope['signature'])['status'], 'new')
            changed = {**envelope['record'], 'id': 'tampered', 'corrected_output': 'unsafe'}
            self.assertEqual(self.store.ingest(changed, verifier='test_runner', signed=envelope['signature'])['status'], 'quarantined')

    def test_verifier_requires_successful_postcondition(self):
        with self.assertRaises(ValueError):
            verified_feedback(feedback(0), lambda text: False, 'a' * 32)
        with self.assertRaises(ValueError):
            verified_feedback(feedback(0), lambda text: True, 'a' * 32)

    def test_verifier_does_not_sign_agent_control_flags(self):
        raw = {**feedback(0), 'critical_regression': True, 'checkpoint': 'forged', 'source': 'human'}
        envelope = verified_feedback(raw, lambda text: json.loads(text).get('action') == 'draft', 'a' * 32)
        self.assertNotIn('critical_regression', envelope['record'])
        self.assertNotIn('source', envelope['record'])

    def test_json_oracle_distinguishes_boolean_and_number(self):
        cases = [{'id': 'one', 'suite': 'safety', 'expected': {'approved': True}}]
        self.assertFalse(evaluate(cases, {'one': '{"approved":1}'})[0]['passed'])

    def test_protected_scenario_and_exact_input_never_train(self):
        self.assertEqual(self.store.ingest({**feedback(0), 'input': suite()[0]['input']}, human=True)['status'], 'quarantined')
        self.assertEqual(self.store.ingest({**feedback(1), 'group': suite()[0]['group']}, human=True)['status'], 'quarantined')

    def test_conflicts_are_quarantined(self):
        self.store.ingest(feedback(0), human=True)
        conflict = {**feedback(0), 'id': 'conflict', 'corrected_output': 'Different decision'}
        self.assertEqual(self.store.ingest(conflict, human=True)['status'], 'quarantined')

    def test_duplicate_correction_is_idempotent(self):
        self.store.ingest(feedback(0), human=True)
        self.store.ingest(feedback(0), human=True)
        self.assertEqual(self.store.status()['feedback']['new'], 1)
        with self.assertRaises(ValueError):
            self.store.ingest({**feedback(0), 'corrected_output': 'changed'}, human=True)

    def test_operator_can_attest_previously_quarantined_feedback(self):
        self.store.ingest(feedback(0))
        self.assertEqual(self.store.ingest(feedback(0), human=True)['status'], 'new')

    def test_provider_failure_pauses_and_does_not_leak_or_retry(self):
        self.add(); self.provider.fail = True
        self.assertEqual(self.run_cycle()['status'], 'failed')
        self.assertEqual(self.store.active()['version'], 'base')
        self.assertNotIn('secret-must-never', json.dumps(self.store.status()))
        self.assertEqual(self.run_cycle()['status'], 'paused')

    def test_second_worker_cannot_train_concurrently(self):
        self.add()
        other = Store(self.store.path, self.policy, suite(), self.provider.identity)
        self.provider.on_train = lambda: self.assertEqual(cycle(other, self.provider, enabled=True)['status'], 'busy')
        self.assertEqual(self.run_cycle()['status'], 'promoted')

    def test_interrupted_attempt_is_not_automatically_retried(self):
        self.add()
        class Crash(BaseException): pass
        self.provider.on_train = lambda: (_ for _ in ()).throw(Crash())
        with self.assertRaises(Crash):
            self.run_cycle()
        self.assertEqual(self.run_cycle()['status'], 'busy')
        self.assertEqual(self.store.recover()['recovered'], 1)
        self.assertEqual(self.store.status()['feedback']['failed'], 2)

    def test_verified_critical_regression_rolls_back_and_pauses(self):
        self.add(); self.run_cycle()
        active = self.store.active()
        key = 'trusted-verifier-key-for-test-only-123'
        record = {**feedback(10), 'critical_regression': True,
                  'checkpoint': active['inference_checkpoint'], 'verified_success': True}
        with patch.dict(os.environ, {'IMMUNE_VERIFIER_KEY_TEST_RUNNER': key}):
            self.store.ingest(record, verifier='test_runner', signed=signature(record, key))
        self.assertEqual(self.store.active()['version'], 'base')
        self.assertTrue(self.store.status()['paused'])

    def test_untrusted_rollback_request_is_ignored(self):
        self.add(); self.run_cycle()
        active = self.store.active()
        self.store.ingest({**feedback(10), 'critical_regression': True, 'checkpoint': active['inference_checkpoint']})
        self.assertEqual(self.store.active(), active)

    def test_stale_candidate_cannot_replace_rollback(self):
        self.add(); self.run_cycle(); self.add(2)
        self.provider.on_train = self.store.rollback
        self.assertEqual(self.run_cycle()['status'], 'stale')
        self.assertEqual(self.store.active()['version'], 'base')

    def test_incomplete_evaluation_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate(suite(), {})

    def test_pinned_policy_and_evaluation_cannot_change_silently(self):
        changed = copy.deepcopy(suite()); changed[0]['expected'] = 'easier answer'
        with self.assertRaises(ValueError):
            Store(self.store.path, self.policy, changed, self.provider.identity)
        with self.assertRaises(ValueError):
            Store(self.store.path, Policy(steps=5), suite(), self.provider.identity)

    def test_config_bounds(self):
        with self.assertRaises(ValueError): Policy(max_updates_per_day=0)
        with self.assertRaises(ValueError): Policy(steps=1000)
        with self.assertRaises(ValueError): Policy(trusted_verifiers='bad')
        with self.assertRaises(ValueError): Store(self.tmp.name+'/invalid.sqlite', self.policy, [], self.provider.identity)


if __name__ == '__main__':
    unittest.main()
