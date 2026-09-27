# The pitch

## One sentence

IMMUNE turns an expert's correction into a memory, a reusable procedure draft, and a model training example, then tests whether the model handles unseen failures better.

## Two minutes

**0:00** "An agent can remember a mistake and still repeat it. I built IMMUNE to test whether expert feedback can change its behavior."

**0:15** Show a case. "This assistant has overstated its evidence. I can ship the output, revise it, or escalate an action that requires human approval. These are synthetic cases, and I review the training labels."

**0:35** Save a correction and sync it. Show a real GBrain recall. "GBrain records the incident. If configured, Memorable extracts a procedure draft from the review trace."

**0:55** Open the completed River experiment. "River trained this adapter on the corrections I approved. These are 12 different cases that were excluded from training. Both evaluations used the same prompt and sampling settings."

**1:15** Report the actual numbers on screen. "Before: [actual] of 12. After: [actual] of 12. Here are the missed escalations and unnecessary escalations, so saying 'escalate' to everything cannot win."

**1:35** "This is a small learning experiment, not proof of clinical safety. My contribution as a physician and epidemiologist is defining failure, designing the feedback, and checking whether apparent progress is real."

**1:50** "The same loop can serve an engineer or a scientist. Personal AI should learn from your judgment."

## If there is no improvement

Say: "The loop works, but this run did not improve held-out performance. Here is the checkpoint and the complete evaluation. I can distinguish remembering a correction, performing a weight update, and demonstrating an actual gain."

A high baseline is a result. Never weaken the baseline prompt to manufacture a gain. If output-format compliance improves, describe that narrower result.

## If a provider remains disconnected

Do not narrate an unverified provider operation as completed. GBrain is mandatory under the provided rules. Prioritize proving a real write and recall over adding more sponsor integrations. Do not submit for the River training challenge based only on the UI or a mocked result.

## Conversation with River staff

"I built the expert feedback and evaluation side of a learning loop: a review interface, approved examples, completion-only SFT, fixed held-out evaluation, and an audit of errors and regressions. I'd like your critique of the data campaign and how you would turn this into a repeated personalization evaluation. That is the kind of work I want to do with River."

## Immediate order of work

1. Verify River model access and a GBrain write/recall.
2. Review a balanced set of at least 12 training examples.
3. Run the paired training experiment and inspect raw outputs.
4. Add Memorable only after the required integrations work.
5. Register the QM tool surface if a ready deployment is available.
6. Export results, record a short demo, and submit before 5 p.m. Pacific.
