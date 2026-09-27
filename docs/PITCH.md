# IMMUNE demo guide

## One sentence

IMMUNE helps experts turn corrections into persistent agent memory and testable training examples.

## Two-minute demonstration

**0:00 — The problem.** “An expert correction should be useful beyond one conversation. I built IMMUNE to preserve that feedback and test whether it changes future decisions.”

**0:15 — Review a case.** Show the evidence, proposed output, and SHIP / REVISE / ESCALATE controls. Explain the decision and save the rationale. Identify the cases as synthetic and draft labels as awaiting expert review.

**0:40 — Show persistent memory.** Open the recorded GBrain write-and-recall evidence. Explain that the verified round-trip used a unique diagnostic record. Show the procedure draft extracted by Memorable and retrieved from GBrain. Its provider quality response was `admitted: true` with `reason: judge_unparseable`; describe it as an unvalidated draft.

**1:05 — Show the evaluation.** Open the evidence report and an individual case. River's recorded baseline scored **11/12**, with zero invalid outputs and zero missed required escalations. Show the remaining error: an escalation where the reference called for revision.

**1:30 — Explain the training experiment.** The implemented pipeline trains only on approved decisions, saves a checkpoint, and repeats the same held-out evaluation. Paired training has not yet completed, so no improvement is claimed.

**1:50 — Close.** “As a physician and epidemiologist, I care about defining failures and checking whether apparent progress is real. IMMUNE makes expert feedback persistent and its effects measurable.”

## If a paired training run completes

Replace the pending-training segment with the recorded before/after scores, approved example count, checkpoint, and raw predictions. Show regressions alongside improvements. Use the paired baseline from that run, not a separate earlier evaluation.

If there is no improvement, say so. If the only gain is output-format compliance, describe that narrower result. Never weaken the baseline prompt to manufacture a gain.

## Evidence and integration status

- [River baseline](https://github.com/BryanTegomoh/immune/actions/runs/36358066104)
- [GBrain and Memorable run](https://github.com/BryanTegomoh/immune/actions/runs/36359383279)
- [Verification record](VERIFICATION.md)
- [Integration guide](SPONSOR-DEMO.md)

QM and Superset assets are prepared but live activation is unverified. UFO is not implemented. Describe only demonstrated integrations as working in the demo.
