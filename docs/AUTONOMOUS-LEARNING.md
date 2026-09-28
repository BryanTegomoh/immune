# Autonomous learning for persistent agents

IMMUNE's next direction is a learning layer for persistent agents: verified feedback enters a queue; a background worker trains a candidate; automated checks decide whether it becomes the active checkpoint. A person does not need to approve every candidate update.

This is bounded autonomous continual learning, not demonstrated open-ended recursive self-improvement. The implementation updates model adapters; it does not rewrite its own learning algorithm, grant itself new tools, or establish that an agent can reliably judge all its own mistakes.

## What is implemented

- **Durable feedback and version state:** SQLite records corrections, their source, candidate attempts, evaluation outputs, active checkpoint and checkpoint ancestry. Restarting a worker does not reset its learned version to the base model.
- **Trusted automatic intake:** A host-owned test harness can sign feedback only after a failed output has been replaced with one that passes an independent postcondition. The worker verifies the signature and source allowlist. A correction from a person is also accepted; that person need not supervise subsequent updates.
- **Candidate updates:** River training uses the full corrected output, rather than only the historical SHIP/REVISE/ESCALATE labels. It resumes from the active training checkpoint, including optimizer state, and saves separate training and inference checkpoints.
- **Replay:** Previously accepted lessons are included within a configured replay limit. Rejected candidates' lessons are not silently added to replay.
- **Automated promotion:** The candidate must improve target-case results, introduce no previously passing case failures, and pass every configured safety case. Promotion is transactional; stale candidates cannot overwrite a rollback.
- **Prospective use:** The `respond` interface reads the active version for each new task and uses its inference checkpoint. Rejected candidates are never selected through that interface.
- **Rollback:** A trusted critical-regression report naming the active inference checkpoint rolls back to its parent and pauses learning. An operator can also request rollback.
- **Runaway controls:** Bounded batches, steps, input/output lengths, rolling daily update count, concurrency exclusion and no automatic retry of failed or interrupted attempts.

These capabilities have local control-flow and mocked adapter tests. They have **not yet been validated by a new end-to-end paid River continual-learning experiment**. Test fixtures use `fixture://` checkpoint identifiers and are not evidence that any weights changed or any model improved.

## Architecture

```text
Persistent agent / task runner
    |
    +--> current active checkpoint --> actual reply or structured output
    |
    +--> trusted postcondition checker
              |
              +--> failed original + verified corrected output
                            |
                       signed feedback
                            |
                       durable queue
                            |
             bounded background learning worker
                            |
          active checkpoint + new corrections + replay
                            |
                    candidate checkpoints
                            |
          target + retention + safety evaluation
                            |
                  promote OR reject
                            |
             next task uses active checkpoint
```

The evaluator runs automatically. Removing a person from the update loop does not remove the need for a reliable success signal.

## Start without paid calls

From the repository root:

```bash
python -m unittest discover -s tests -v

python -m immune.autonomy \
  --policy examples/autonomy/policy.json \
  --evaluation examples/autonomy/evaluation.json \
  status
```

No River key is needed for these commands. A plain `run-once` returns `disabled`; it does not call River.

The example policy permits at most two candidate attempts in a rolling 24-hour period, with four optimizer steps per candidate. These are operation limits, **not a currency-denominated spending cap**. Sampling and training both consume provider resources; configure provider-side spending controls separately.

## Configure a real task before enabling training

The supplied evaluation file is a small **contract-test template**, not a validated personal-assistant benchmark. It uses exact text or whole-JSON equality. This makes the oracle reproducible but can reject harmless wording differences; the examples largely test narrow instruction-following and output contracts, not broad task quality.

Replace it with a versioned suite for the actual task:

- `target`: new scenarios where the correction should generalize.
- `retention`: work the existing assistant already performs correctly.
- `safety`: explicit invariants that must remain true.

Each case needs `id`, `group`, `suite`, `input`, and `expected`. The default policy requires at least four cases in each partition. Expected answers are not supplied to the model at evaluation time.

Evaluation inputs and scenario groups cannot enter the training queue. This protects exact inputs and declared groups, not semantic leakage: the operator must also prevent near-duplicate training/test scenarios. Because this suite is repeatedly used for promotion, it is a validation suite. Maintain a separate untouched audit set for eventual performance claims.

Policy, evaluation and provider identity are pinned to the state database. Changing them requires a new database and an intentional migration of trusted state; an automatic migration tool is not yet implemented.

## Add a human correction once

Review the synthetic example before asserting approval:

```bash
python -m immune.autonomy \
  --policy examples/autonomy/policy.json \
  --evaluation examples/autonomy/evaluation.json \
  ingest examples/autonomy/feedback.json --human-approved
```

This approves a training example, not each future candidate. Unattended sources use the verifier path instead. Never give an untrusted agent permission to call the human-attestation path.

The default batch requires two new examples, so a single example waits. Do not duplicate an example to satisfy the threshold; repeated input/target pairs are deduplicated.

## Connect an unattended verifier

The module `immune.verifier_feedback.verified_feedback(record, check, key)`:

1. Runs host-owned `check` on the original output and requires failure.
2. Runs the same independent postcondition on the corrected output and requires success.
3. Signs the complete feedback record, including its identity, with HMAC-SHA256.

The producer's `check` must not come from agent-generated code or expected answers. A unit-test harness, schema validator, or an authoritative task outcome can supply this signal. A model declaring “I fixed it” is not a sufficient oracle.

Example integration in trusted host code:

```python
import json
import os
from immune.verifier_feedback import verified_feedback

# record contains id, group, input, observed_output and corrected_output.
# task_oracle is your independently maintained successful-outcome check.
envelope = verified_feedback(
    record,
    task_oracle,
    os.environ["IMMUNE_VERIFIER_KEY_TASK_TESTS"],
)
# Transport the JSON envelope to the learning worker; do not expose the key.
```

Configure `task_tests` in `trusted_verifiers`, provision its signing key separately in the trusted verifier and worker environments, and keep it out of the agent's tool environment. Use a randomly generated key of at least 32 characters.

Worker intake:

```bash
python -m immune.autonomy \
  --policy examples/autonomy/policy.json \
  --evaluation examples/autonomy/evaluation.json \
  ingest signed-feedback.json --verifier task_tests
```

Corrections are quarantined when trust checks fail, when they conflict with an admitted correction, or when they overlap a protected evaluation scenario. Quarantine is visible in `status`; it is not a successful learning event.

## Enable bounded unattended updates

Install the documented provider dependencies on Python 3.12+, and configure `RIVER_API_KEY` in the worker environment. Then authorize the worker once:

```bash
python -m immune.autonomy \
  --policy examples/autonomy/policy.json \
  --evaluation examples/autonomy/evaluation.json \
  watch --allow-training --interval 60
```

It waits for sufficient trusted feedback, trains, evaluates, and promotes or rejects without per-update user input. It uses the existing River key only when a live call is necessary; missing credentials do not fall back to a fake model.

For one iteration, use `run-once --allow-training`. The default model is `Qwen/Qwen3.5-9B`; use the global `--model` option for a model your River account supports.

This worker requires a durable host and volume. It is **not running continuously in Vercel serverless functions**, and this change does not start a daemon or a scheduled billable job. The historical hosted workbench keeps its existing explicit approval flow.

## Use the learned model

For a new task saved in `task.txt`:

```bash
python -m immune.autonomy \
  --policy examples/autonomy/policy.json \
  --evaluation examples/autonomy/evaluation.json \
  respond task.txt --allow-inference
```

The result includes the active version, inference checkpoint, and generated output. This performs inference, not external actions. Sending email, purchasing, deleting, sharing private information, and other consequential actions still require separate application-enforced authorization.

Host applications can use `immune.learning.respond(store, provider, prompt)` directly. A task pins its starting checkpoint; promotion or rollback affects subsequent tasks, not work already in flight.

## Failures, rollback and recovery

A signed feedback record may include `critical_regression: true` and `checkpoint: "river://..."`. The trusted producer supplies these through `verified_feedback(..., critical=True, checkpoint=evaluated_checkpoint)`; agent-supplied control flags are stripped. If its trusted source reports a critical regression against the active checkpoint, IMMUNE restores the parent and pauses further learning. Untrusted reports and reports about stale checkpoints cannot roll back the active version.

`rollback` requests the same action manually. `recover` clears a pause and marks any abandoned running attempt as interrupted, without retrying its training. Inspect the provider state and underlying failure before invoking it. Failed/interrupted attempts still count toward the rolling update limit.

If a process crashes during a provider call, the attempt stays reserved. Another process cannot silently repeat that possibly paid call. This favors stopping over pretending exactly-once external execution is guaranteed.

## Boundaries and remaining work

- This is a single-owner reference runtime, not a hardened multi-tenant service.
- SQLite and verifier secrets must be outside an untrusted agent's writable/readable workspace. A signature cannot protect a database or key the agent can directly modify.
- A valid signature proves which trusted producer reported a result, not that the producer's oracle is correct.
- The default exact-output evaluator is narrow; richer task-specific validators, semantic-leakage checks, memory-only comparisons and independent audits remain necessary.
- There is no automatic discovery of a trustworthy correction for every arbitrary task. The harness must produce corrected outputs backed by a trusted check.
- Two daily attempts and token/step limits are not a monetary budget or a guarantee against all provider-side work after a timeout.
- Continual evaluation can overfit its promotion suite. Passing it is not a guarantee of global safety, zero errors, or immunity.
- Automatic critical-regression rollback depends on receiving a trustworthy report. It does not detect every regression itself.
- Feedback is local to this runtime. GBrain/Memorable are not yet wired into the new worker; their historical workbench integrations remain separate.
- The old 12-case hackathon result is unchanged and is not evidence for this new loop.

## River contract

The adapter uses River's documented training/inference checkpoint distinction, `load_weights(..., load_optimizer=True)`, and `session.sample(..., checkpoint=...)`. Signatures were checked against the repository-pinned `river-client==0.12.0`; the implementation has mocked adapter tests, not a new live-provider verification. See the [River Python API](https://docs.river.ai/python-api/) and [SFT guide](https://docs.river.ai/guides/sft/).
