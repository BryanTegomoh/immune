"""Adapter contract tests. No network, tokenizer download or River credits."""
import sys
import types
import unittest
from unittest.mock import patch
from immune.learning import Policy
from immune.river_learning import RiverLearning


class Tokenizer:
    eos_token_id = 0
    def encode(self, value, add_special_tokens=False):
        return [ord(c) for c in value]
    def apply_chat_template(self, messages, **kwargs):
        return 'TASK:' + messages[-1]['content']


class Session:
    def __init__(self):
        self.loaded = None; self.saved = []; self.batches = []; self.optimizers = []; self.sampling = None
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def create_model(self, **kwargs): self.created = kwargs; return self
    def load_weights(self, checkpoint, **kwargs): self.loaded = (checkpoint, kwargs)
    def forward_backward(self, batch, **kwargs): self.batches.append(batch)
    def optim_step(self, **kwargs): self.optimizers.append(kwargs)
    def save_weights(self, name, **kwargs):
        self.saved.append(kwargs['mode'])
        return types.SimpleNamespace(path='river://fixture/' + kwargs['mode'])
    def sample(self, **kwargs):
        self.sampling = kwargs
        return [[types.SimpleNamespace(text='{"reply":"A corrected draft"}')] for _ in kwargs['prompt_token_ids']]


class Client:
    def __init__(self, session): self.current = session
    def session(self, **kwargs): return self.current
    def close(self): pass


class RiverAdapterTests(unittest.TestCase):
    def setUp(self):
        self.provider = RiverLearning('test-base')
        self.provider._tokenizer = Tokenizer()
        self.session = Session()
        self.fake_module = types.SimpleNamespace(LoraConfig=lambda **kwargs: kwargs)

    def test_resumes_optimizer_and_trains_full_corrected_output(self):
        target = '{"action":"draft_reply","reply":"A corrected draft"}'
        with patch.dict(sys.modules, {'river_client': self.fake_module}), patch.object(self.provider, 'client', return_value=Client(self.session)):
            result = self.provider.train({'training_checkpoint': 'river://prior/training'},
                [{'input': 'A real task', 'corrected_output': target}], Policy(), 'attempt')
        self.assertEqual(self.session.loaded[0], 'river://prior/training')
        self.assertTrue(self.session.loaded[1]['load_optimizer'])
        self.assertEqual(self.session.saved, ['training', 'inference'])
        self.assertEqual(len(self.session.optimizers), 4)
        datum = self.session.batches[0][0]
        supervised = [token for token, weight in zip(datum['target_tokens'], datum['weights']) if weight]
        self.assertEqual(supervised, [ord(c) for c in target] + [0])
        self.assertEqual(result['inference_checkpoint'], 'river://fixture/inference')

    def test_sampling_uses_requested_checkpoint_and_fixed_settings(self):
        with patch.object(self.provider, 'client', return_value=Client(self.session)):
            result = self.provider.respond({'inference_checkpoint': 'river://active'}, 'Next task', Policy())
        self.assertEqual(self.session.sampling['checkpoint'], 'river://active')
        self.assertEqual(self.session.sampling['temperature'], 0.0)
        self.assertEqual(self.session.sampling['seed'], 27)
        self.assertIn('corrected draft', result)

    def test_token_budget_rejects_without_truncation(self):
        with self.assertRaises(ValueError):
            self.provider.tokens('x' * 3000, Policy())


if __name__ == '__main__':
    unittest.main()
