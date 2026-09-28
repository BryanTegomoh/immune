"""Bounded autonomous continual learning. No provider calls at import time.

The local operator and signed verifier adapters are the trust boundary.
Feedback text is data, never code. Candidate evaluation and promotion are automatic.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def signature(record, key):
    """Verifier adapters sign the entire record, including identity and outcome."""
    return hmac.new(key.encode(), canonical(record).encode(), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class Policy:
    min_new_examples: int = 2
    max_new_examples: int = 8
    replay_examples: int = 16
    max_updates_per_day: int = 2
    steps: int = 4
    max_input_tokens: int = 2048
    max_output_tokens: int = 512
    min_cases_per_suite: int = 4
    min_target_gain: int = 1
    trusted_verifiers: tuple = ()

    def __post_init__(self):
        limits = {
            'min_new_examples': (1, 64), 'max_new_examples': (1, 64),
            'replay_examples': (0, 128), 'max_updates_per_day': (1, 24),
            'steps': (1, 32), 'max_input_tokens': (32, 8192),
            'max_output_tokens': (8, 2048), 'min_cases_per_suite': (1, 1000),
            'min_target_gain': (1, 1000),
        }
        for name, (low, high) in limits.items():
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError('Invalid learning policy: ' + name)
        if self.min_new_examples > self.max_new_examples:
            raise ValueError('Minimum batch exceeds maximum batch.')
        if not isinstance(self.trusted_verifiers, (list, tuple)):
            raise ValueError('Trusted verifiers must be a list.')
        if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}', v) for v in self.trusted_verifiers):
            raise ValueError('Invalid verifier name.')


def validate_suite(cases, policy):
    if not isinstance(cases, list) or not cases:
        raise ValueError('A versioned evaluation suite is required.')
    ids, prompts = set(), set()
    counts = dict(target=0, retention=0, safety=0)
    for case in cases:
        if set(case) != {'id', 'group', 'suite', 'input', 'expected'}:
            raise ValueError('Each evaluation case needs id, group, suite, input, expected.')
        for key in ('id', 'group', 'input'):
            if not isinstance(case[key], str) or not case[key].strip():
                raise ValueError('Invalid evaluation ' + key)
        if case['id'] in ids or case['input'].strip() in prompts or case['suite'] not in counts:
            raise ValueError('Duplicate or invalid evaluation case.')
        if not isinstance(case['expected'], (str, dict)) or not case['expected']:
            raise ValueError('Expected output must be nonempty text or a JSON object.')
        ids.add(case['id']); prompts.add(case['input'].strip())
        counts[case['suite']] += 1
    if any(n < policy.min_cases_per_suite for n in counts.values()):
        raise ValueError('Each target, retention and safety suite needs enough cases.')


def evaluate(cases, outputs):
    """Strict text/JSON oracle, not a universal natural-language quality judge."""
    if not isinstance(outputs, dict) or set(outputs) != {c['id'] for c in cases}:
        raise ValueError('Missing, duplicate or extra evaluation outputs.')
    rows = []
    for case in cases:
        raw = outputs[case['id']]
        if not isinstance(raw, str):
            raise ValueError('Evaluation output must be text.')
        try:
            actual = json.loads(raw) if isinstance(case['expected'], dict) else raw.strip()
        except (ValueError, TypeError):
            actual = None
        passed = canonical(actual) == canonical(case['expected']) if isinstance(case['expected'], dict) else actual == case['expected']
        rows.append({'id': case['id'], 'suite': case['suite'], 'passed': passed, 'raw': raw})
    return rows


def promotion_gate(before, after, policy):
    if [r['id'] for r in before] != [r['id'] for r in after]:
        raise ValueError('Paired cases do not match.')
    regressions = [b['id'] for b, a in zip(before, after) if b['passed'] and not a['passed']]
    safety_failures = [a['id'] for a in after if a['suite'] == 'safety' and not a['passed']]
    gain = sum(int(a['passed']) - int(b['passed']) for b, a in zip(before, after) if a['suite'] == 'target')
    return {'promote': not regressions and not safety_failures and gain >= policy.min_target_gain,
            'target_gain': gain, 'regressions': regressions, 'safety_failures': safety_failures}


class Store:
    def __init__(self, path, policy, evaluation, provider_identity):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(mode=0o600, exist_ok=True)
        os.chmod(self.path, 0o600)
        self.policy, self.evaluation = policy, evaluation
        self.identity = provider_identity
        validate_suite(evaluation, policy)
        config_hash = fingerprint({'policy': policy.__dict__, 'evaluation': evaluation, 'provider': provider_identity})
        with self.tx() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS feedback (
              id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL, prompt_hash TEXT NOT NULL,
              record TEXT NOT NULL, source TEXT NOT NULL, status TEXT NOT NULL,
              reason TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts (
              id TEXT PRIMARY KEY, parent TEXT NOT NULL, status TEXT NOT NULL,
              event_ids TEXT NOT NULL, created REAL NOT NULL, report TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS versions (
              id TEXT PRIMARY KEY, parent TEXT, data TEXT NOT NULL);
            """)
            # executescript commits; begin explicitly for the identity pin.
            db.execute('BEGIN IMMEDIATE')
            old = self.get(db, 'config_hash')
            if old and old != config_hash:
                raise ValueError('Policy, provider or evaluation changed. Use a new state database; do not silently change the gate.')
            self.put(db, 'config_hash', config_hash)
            if not self.get(db, 'active'):
                base = {'version': 'base', 'training_checkpoint': None, 'inference_checkpoint': None}
                self.put(db, 'active', base)
                db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?)', ('base', None, canonical(base)))
        os.chmod(self.path, 0o600)

    @contextmanager
    def tx(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('BEGIN IMMEDIATE')
        try:
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def get(db, key, default=None):
        row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else default

    @staticmethod
    def put(db, key, value):
        db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (key, canonical(value)))

    def active(self):
        with self.tx() as db:
            return self.get(db, 'active')

    def ingest(self, record, *, human=False, verifier=None, signed=None):
        """Only trusted host code may assert human=True. No public intake endpoint."""
        if not isinstance(record, dict):
            raise ValueError('Feedback must be an object.')
        for key, limit in [('id', 120), ('group', 120), ('input', 16000),
                           ('observed_output', 8000), ('corrected_output', 8000)]:
            if not isinstance(record.get(key), str) or not record[key].strip() or len(record[key]) > limit:
                raise ValueError('Invalid feedback field: ' + key)
        if len(canonical(record)) > 48000:
            raise ValueError('Feedback is too large.')
        trusted = human
        source = 'human' if human else 'untrusted'
        if not human and verifier in self.policy.trusted_verifiers:
            key = os.getenv('IMMUNE_VERIFIER_KEY_' + verifier.upper(), '')
            trusted = bool(len(key) >= 32 and isinstance(signed, str) and hmac.compare_digest(signature(record, key), signed)
                           and record.get('verified_success') is True)
            source = 'verifier:' + verifier if trusted else 'untrusted'
        reason = '' if trusted else 'No trusted correction or signed successful verifier outcome.'
        if record['input'].strip() in {c['input'].strip() for c in self.evaluation} or record['group'] in {c['group'] for c in self.evaluation}:
            reason = 'Evaluation scenario is protected from training.'
        if record['observed_output'].strip() == record['corrected_output'].strip():
            reason = 'No correction was supplied.'
        prompt_hash = fingerprint(record['input'].strip())
        fp = fingerprint([record['input'].strip(), record['corrected_output'].strip()])
        with self.tx() as db:
            duplicate = db.execute('SELECT id,status,reason,record FROM feedback WHERE id=? OR fingerprint=?',
                                   (record['id'], fp)).fetchone()
            if duplicate:
                if duplicate['id'] == record['id'] and json.loads(duplicate['record']) != record:
                    raise ValueError('Feedback ID was reused with different content.')
                active = self.get(db, 'active')
                if trusted and record.get('critical_regression') is True and active['version'] != 'base' and record.get('checkpoint') == active['inference_checkpoint']:
                    self._rollback(db, 'Verified critical regression: ' + record['id'])
                if duplicate['status'] == 'quarantined' and not reason:
                    # A local operator may attest to previously untrusted data.
                    db.execute("UPDATE feedback SET source=?,status='new',reason='' WHERE id=?", (source, duplicate['id']))
                    return {'id': duplicate['id'], 'status': 'new', 'reason': ''}
                return {k: duplicate[k] for k in ('id', 'status', 'reason')}
            conflicts = db.execute("SELECT record FROM feedback WHERE prompt_hash=? AND status!='quarantined'", (prompt_hash,)).fetchall()
            if any(json.loads(r[0])['corrected_output'].strip() != record['corrected_output'].strip() for r in conflicts):
                reason = 'Conflicting correction requires investigation.'
            status = 'quarantined' if reason else 'new'
            db.execute('INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?)',
                       (record['id'], fp, prompt_hash, canonical(record), source, status, reason, time.time()))
            active = self.get(db, 'active')
            if trusted and record.get('critical_regression') is True and active['version'] != 'base' and record.get('checkpoint') == active['inference_checkpoint']:
                self._rollback(db, 'Verified critical regression: ' + record['id'])
            return {'id': record['id'], 'status': status, 'reason': reason}

    def _rollback(self, db, reason):
        active = self.get(db, 'active')
        row = db.execute('SELECT parent FROM versions WHERE id=?', (active['version'],)).fetchone()
        if not row or not row[0]:
            raise ValueError('No prior checkpoint exists.')
        prior = json.loads(db.execute('SELECT data FROM versions WHERE id=?', (row[0],)).fetchone()[0])
        self.put(db, 'active', prior)
        self.put(db, 'paused', reason)
        self.put(db, 'last_rollback', {'from': active['version'], 'to': prior['version'], 'reason': reason, 'at': time.time()})
        return prior

    def rollback(self):
        with self.tx() as db:
            return self._rollback(db, 'Operator rollback')

    def recover(self):
        """A crashed/unknown provider call is NOT automatically retried."""
        with self.tx() as db:
            running = db.execute("SELECT id,event_ids FROM attempts WHERE status='running'").fetchall()
            for row in running:
                db.execute("UPDATE attempts SET status='interrupted',report=? WHERE id=?",
                           (canonical({'reason': 'Operator acknowledged unknown provider outcome; no retry.'}), row['id']))
                for eid in json.loads(row['event_ids']):
                    db.execute("UPDATE feedback SET status='failed' WHERE id=?", (eid,))
            self.put(db, 'paused', None)
        return {'recovered': len(running)}

    def status(self):
        with self.tx() as db:
            counts = {r[0]: r[1] for r in db.execute('SELECT status,count(*) FROM feedback GROUP BY status')}
            attempts = [dict(r) for r in db.execute('SELECT id,parent,status,created,report FROM attempts ORDER BY created DESC LIMIT 20')]
            for row in attempts:
                row['report'] = json.loads(row['report'])
            return {'active': self.get(db, 'active'), 'paused': self.get(db, 'paused'),
                    'provider': self.identity, 'feedback': counts, 'attempts': attempts,
                    'last_rollback': self.get(db, 'last_rollback'), 'config_sha256': self.get(db, 'config_hash')}


def cycle(store, provider, *, enabled=False):
    """One autonomous iteration. Provider implements train/evaluate/respond."""
    if not enabled:
        return {'status': 'disabled', 'reason': 'Operator must authorize a bounded training policy once.'}
    if provider.identity != store.identity:
        raise ValueError('Provider does not match the pinned state.')
    policy = store.policy
    with store.tx() as db:
        if store.get(db, 'paused'):
            return {'status': 'paused'}
        if db.execute("SELECT 1 FROM attempts WHERE status='running'").fetchone():
            return {'status': 'busy', 'reason': 'A running or interrupted attempt requires completion or explicit recovery.'}
        count = db.execute('SELECT count(*) FROM attempts WHERE created>?', (time.time() - 86400,)).fetchone()[0]
        if count >= policy.max_updates_per_day:
            return {'status': 'budget_exhausted'}
        pending = db.execute("SELECT id,record FROM feedback WHERE status='new' ORDER BY created LIMIT ?",
                             (policy.max_new_examples,)).fetchall()
        if len(pending) < policy.min_new_examples:
            return {'status': 'waiting', 'new_examples': len(pending)}
        replay = db.execute("SELECT record FROM feedback WHERE status='accepted' ORDER BY created DESC LIMIT ?",
                            (policy.replay_examples,)).fetchall()
        active = store.get(db, 'active')
        attempt_id = uuid.uuid4().hex
        ids = [r['id'] for r in pending]
        training = [json.loads(r['record']) for r in pending] + [json.loads(r['record']) for r in replay]
        db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?)',
                   (attempt_id, active['version'], 'running', canonical(ids), time.time(), '{}'))
        for eid in ids:
            db.execute("UPDATE feedback SET status='reserved' WHERE id=?", (eid,))
    report = {'mode': provider.identity, 'evaluation_sha256': fingerprint(store.evaluation),
              'training_sha256': fingerprint(training), 'new_examples': len(ids), 'replay_examples': len(replay)}
    try:
        # Expected answers are withheld from the provider during evaluation.
        prompts = [{'id': c['id'], 'input': c['input']} for c in store.evaluation]
        before = evaluate(store.evaluation, provider.evaluate(active, prompts, policy))
        candidate = provider.train(active, training, policy, attempt_id)
        if not isinstance(candidate, dict) or not all(isinstance(candidate.get(k), str) and candidate[k]
                for k in ('training_checkpoint', 'inference_checkpoint')):
            raise ValueError('Both durable training and inference checkpoints are required.')
        after = evaluate(store.evaluation, provider.evaluate(candidate, prompts, policy))
        gate = promotion_gate(before, after, policy)
        report.update(before=before, after=after, gate=gate, candidate=candidate)
        with store.tx() as db:
            stale = store.get(db, 'active')['version'] != active['version'] or bool(store.get(db, 'paused'))
            status = 'promoted' if gate['promote'] and not stale else 'stale' if stale else 'rejected'
            if status == 'promoted':
                candidate = {**candidate, 'version': attempt_id}
                db.execute('INSERT INTO versions VALUES (?,?,?)', (attempt_id, active['version'], canonical(candidate)))
                store.put(db, 'active', candidate)
            db.execute('UPDATE attempts SET status=?,report=? WHERE id=?', (status, canonical(report), attempt_id))
            for eid in ids:
                db.execute('UPDATE feedback SET status=? WHERE id=?', ('accepted' if status == 'promoted' else 'rejected', eid))
        return {'status': status, 'attempt_id': attempt_id, 'gate': gate}
    except Exception as exc:
        # Do not persist provider messages, which may contain credentials or private prompts.
        report['error_type'] = type(exc).__name__
        with store.tx() as db:
            db.execute("UPDATE attempts SET status='failed',report=? WHERE id=?", (canonical(report), attempt_id))
            store.put(db, 'paused', 'Provider/evaluation failure: ' + type(exc).__name__ + '. Inspect before recovery; no automatic retry.')
            for eid in ids:
                db.execute("UPDATE feedback SET status='failed' WHERE id=?", (eid,))
        return {'status': 'failed', 'attempt_id': attempt_id, 'error_type': type(exc).__name__}


def respond(store, provider, prompt):
    """Pin a task to one active checkpoint; never sample an unpromoted candidate."""
    if provider.identity != store.identity:
        raise ValueError('Provider does not match the pinned state.')
    active = store.active()
    return {'version': active['version'], 'checkpoint': active['inference_checkpoint'],
            'output': provider.respond(active, prompt, store.policy)}
