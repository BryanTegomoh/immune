# Own Your Intelligence submission draft

This draft reflects verified evidence as of September 27, 2026. Do not submit a demo-video placeholder. Update the training sentence only after a paired training run completes.

## Email

bryan.tegomoh@gmail.com

## Team Name

IMMUNE

## Member Names + Emails

Bryan Tegomoh, bryan.tegomoh@gmail.com

## Project Description

IMMUNE is an expert-feedback workbench for AI agents, built by a physician and epidemiologist. It turns review decisions into persistent incident memory, procedure drafts, and supervised training examples, with a full evaluation record to test whether model behavior changes.

GBrain stores and retrieves incidents. Memorable extracts procedures from completed task traces. River provides the model-training and evaluation pipeline. The interface lets an expert approve, revise, or escalate synthetic agent outputs and inspect every evaluation case.

Verified so far: River inference scored 11/12 on a fixed synthetic held-out set; GBrain wrote and retrieved an exact diagnostic record; Memorable returned a procedure draft that was stored and retrieved through GBrain. Paired model training remains pending expert label review. A QM MCP adapter and Superset presentation assets are included; live activation in those products is pending.

## Github URL

https://github.com/BryanTegomoh/immune

Use this repository URL for judge access.

## Demo Video URL

Not yet available. Insert the actual accessible recording URL before submitting.

## Side Quest

- GBrain: verified memory write and exact recall.
- Memorable: verified extraction API response and GBrain storage/retrieval of its draft. Report the actual quality-gate result.
- River AI: baseline inference verified; select for the trained-model challenge once actual training completes.
- QM: select only after demonstrating the adapter through a real QM instance.
- Superset: select once the project is used in Superset and its Page is published.
- UFO: no integration yet; do not claim completion.

## Anything else you'd like the judges / organizers to know?

Solo builder: physician and epidemiologist working on AI evaluation. Built from scratch during hackathon hours, with no prebuilt project or fork. Uses synthetic cases only. The experiment preserves raw predictions, tracks missed and unnecessary escalations, and excludes held-out cases from training. This is a small engineering demonstration, not clinical validation. The long-term goal is to make domain-expert feedback persist across agent sessions and become testable model improvements.

## Send me a copy of my responses

Yes.

## If training finishes before submission

Replace the pending-training sentence with the actual before/after score, number of approved training cases, and saved checkpoint evidence. Include regressions or no improvement when that is the result. Do not use the earlier separate baseline as the paired baseline unless the recorded training run confirms it.
