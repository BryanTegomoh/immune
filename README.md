# IMMUNE

### Expert feedback that agents can remember, reuse, and test.

IMMUNE is a workbench for reviewing AI agent decisions and carrying those corrections into persistent memory and model evaluation. An expert reviews an output against its evidence, chooses **SHIP**, **REVISE**, or **ESCALATE**, and records the reason. The system connects that feedback to GBrain incident memory, Memorable procedure extraction, and a River training pipeline.

Built by [Bryan Tegomoh, MD, MPH](https://github.com/BryanTegomoh) for the **Own Your Intelligence Hackathon**, September 27, 2026. Created from scratch during the event.

[Open IMMUNE](https://immune-ai.vercel.app) · [Watch the recorded demo](https://www.perplexity.ai/computer/a/bc4bfb35-2912-4f87-92c4-57fe88b345f4) · [Run locally](#quick-start) · [Measured results](#measured-results) · [Review the cases](docs/TRAINING-REVIEW.md) · [Technical verification](docs/VERIFICATION.md)

## Why IMMUNE

An expert correction should be useful beyond the conversation in which it was made. IMMUNE makes the feedback inspectable, preserves its provenance, and provides a controlled experiment for checking whether supervised training changes future decisions.

The current prototype focuses on synthetic evidence-review and authorization scenarios: unsupported claims, invented citations, uncertainty, untrusted instructions, and actions requiring human approval.

## How it works

1. **Review:** inspect the supplied evidence and the agent's proposed output.
2. **Correct:** choose a decision and explain it. Draft labels become approved examples only after human review.
3. **Remember:** store the correction and its provenance in GBrain, then retrieve it.
4. **Extract:** use Memorable to produce a procedure draft from the completed task trace.
5. **Train and evaluate:** use River to run a matched baseline, train on approved decisions, save a checkpoint, and evaluate the same held-out inputs again.

Training uses the approved **decision labels**. Written rationales remain in the incident record; this version does not train the model to reproduce those rationales. Retrieved memory is excluded from evaluation prompts so that the paired experiment measures the weight update separately.

## Measured results

The following are recorded API results, not simulated scores.

| Component | Verified result | Evidence |
|---|---|---|
| River | Completed paired Qwen3.5-9B experiment: **11/12 correct before and after**, 12 approved examples, 12 training steps, and a saved checkpoint; zero invalid outputs and zero missed required escalations in both evaluations | [Completed paired run](https://github.com/BryanTegomoh/immune/actions/runs/36359516068) |
| GBrain | Wrote a unique diagnostic fact and retrieved that exact fact; also stored and retrieved a procedure draft | [Memory run](https://github.com/BryanTegomoh/immune/actions/runs/36359383279) |
| Memorable | Extracted a procedure from a completed GBrain task and a successful repository test run | [Procedure run](https://github.com/BryanTegomoh/immune/actions/runs/36359383279) |
| Integrity checks | Eight automated tests pass locally and in GitHub Actions | [Tests](tests/test_integrity.py) |

**Paired training completed. No net accuracy improvement is claimed.** On the same 12 held-out cases, H12 improved from ESCALATE to the reference REVISE decision, while H07 regressed from the correct SHIP decision to REVISE. One correction and one regression left accuracy unchanged at 11/12. The run used 12 human-approved synthetic training examples and completed 12 training steps. The saved checkpoint is `river://dea3a115-3a68-4d59-8f5a-44994f435ee6/sampler_weights/immune-6006e7b3ab`. Inspect the [paired run artifact](https://github.com/BryanTegomoh/immune/actions/runs/36359516068) for raw predictions, losses, and provenance.

Memorable produced procedure drafts. A [separate memory demonstration](https://github.com/BryanTegomoh/immune/actions/runs/36359383279) returned `admitted=true` with `reason=judge_unparseable`; all 12 procedure drafts from the [training run](https://github.com/BryanTegomoh/immune/actions/runs/36359516068) were rejected with `reason=no_postcondition`. We retain these outcomes transparently and do not claim validated procedure quality. The separate memory demonstration used a diagnostic record; the paired training run also synced and recalled the approved correction records.

The [recorded demo video](https://www.perplexity.ai/computer/a/bc4bfb35-2912-4f87-92c4-57fe88b345f4) shows the actual workbench and completed paired results. A [direct MP4 download](https://raw.githubusercontent.com/BryanTegomoh/immune/main/docs/IMMUNE-demo.mp4) is also available without the Perplexity player. The earlier self-contained [evidence report](docs/demo.html) and portions of the [verification notes](docs/VERIFICATION.md) may still describe the baseline-only snapshot; the completed paired run linked above is authoritative for the final result.

## Public presentation

The public homepage presents the completed experiment, an interactive case explorer, training trace, video, and a browser-only review exercise. Use **Open workbench** to enter the full owner-authorized application. This presentation was polished after the hackathon. See [public-site setup and verification](docs/PUBLIC-SITE.md).

## Quick start

### Hosted workbench

The full application can now run with a Vercel frontend/API and a GitHub Actions background runner. Public visitors inspect the recorded evidence; owner authorization unlocks correction saves, baseline inference, training, memory sync, and recall. Provider keys remain in Actions secrets, and training requires explicit confirmation. See [hosting and access instructions](docs/HOSTING.md). This hosting adaptation was added after the hackathon submission.

Python 3.10+ can run the bundled interface without provider credentials:

```bash
git clone https://github.com/BryanTegomoh/immune.git
cd immune
python3 -m immune.server
```

Open **http://127.0.0.1:8765**. On Windows, use `python` if that is your Python command.

The compiled interface is included. Without API keys, you can review synthetic cases, save corrections, and export records. Provider actions require configuration; evaluation scores are not prefilled.

### Connect the providers

Live integrations require **Python 3.12+**. No local GPU is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and copy with `Copy-Item .env.example .env`.

Set the following in your local, ignored `.env` file:

| Variable | Purpose |
|---|---|
| `RIVER_API_KEY` | River training and inference |
| `RIVER_MODEL` | Defaults to `Qwen/Qwen3.5-9B`; use a model available to your account |
| `GBRAIN_TOKEN` | GBrain token for the intended workspace, with memory read/write access |
| `MEMORABLE_API_KEY` | Optional procedure extraction |

Restart with `python -m immune.server`. GBrain connects through `https://gbrain.io/mcp` and discovers and validates the available tool schemas. River downloads the tokenizer from Hugging Face and runs model operations on its hosted service.

Keep credentials out of source files and exported reports. The application and MCP adapter bind to loopback and are intended for local use.

### Run through GitHub Actions

On a repository you administer, configure the same keys under **Settings → Secrets and variables → Actions**. Then open **Actions → IMMUNE live experiment → Run workflow**.

| Operation | Behavior |
|---|---|
| `check-connections` | Checks River health/model availability and GBrain tool discovery |
| `memory-check` | Writes and recalls a diagnostic fact; when configured, extracts a Memorable procedure and stores its draft in GBrain |
| `baseline` | Runs the fixed held-out evaluation without training |
| `train` | Records explicitly reviewed training IDs, syncs and recalls their corrections, then runs paired training and evaluation |

For `train`, provide the reviewed case IDs and confirm that you approve their labels and rationales. The workflow does not run automatically on pushes. Results are uploaded as run artifacts with seven-day retention. Treat logs and artifacts in a public repository as public project material; use synthetic data only.

To view a recorded experiment in the local interface, place its artifact's `state.json` at `runs/state.json` before starting the server.

## Integrations

- **GBrain:** incident memory with provenance and scoped recall.
- **River:** official SDK, rank-16 LoRA, completion-only loss, checkpoint saving, and matched evaluation.
- **Memorable:** extraction API with the complete provider response retained alongside each draft.
- **QM:** MCP adapter exposing `evaluation_status`, `approved_corrections`, and `run_immune`. Implemented and locally tested; not yet registered in a live QM deployment.
- **Superset:** repository setup/run configuration and an HTML presentation for Pages. Prepared; live use and publication are not yet verified.

See [integration and demo instructions](docs/SPONSOR-DEMO.md). UFO integration is not implemented.

## Evaluation design

- **24 training cases and 12 held-out cases**, balanced across SHIP, REVISE, and ESCALATE.
- Held-out cases cannot be approved through the correction endpoint or included in the training batch.
- Model inputs contain only supplied context and agent output, excluding reference answers, rationales, IDs, and category tags.
- The paired run uses identical prompt tokens and sampling settings before and after training: greedy decoding, seed 27, and a 32-token output limit.
- Training is configured for 12 full-batch updates at learning rate `1e-4`. Each experiment starts from the base model.
- Metrics include correctness, invalid output format, missed required escalations, and unnecessary escalation of acceptable outputs. Raw predictions remain available for inspection.

This small synthetic benchmark demonstrates the engineering workflow. It is not independent clinical validation. The prototype does not implement continual learning, automatic model deployment, or a guarantee that any correction improves performance.

## Development

```bash
npm ci
npm run build
python -m unittest discover -s tests -v
```

Use `npm run dev` for the Vite development server while the Python API is running. Runtime state is stored in the ignored `runs/` directory. Run only one state-writing Python process per directory.

To regenerate the presentation from recorded results:

```bash
python scripts/build_demo_report.py runs/state.json --memory runs/memory-check.json
```

## Documentation

- [Training-case review](docs/TRAINING-REVIEW.md)
- [Verification and limitations](docs/VERIFICATION.md)
- [Sponsor integration guide](docs/SPONSOR-DEMO.md)
- [River SDK](https://docs.river.ai/python-api/) and [SFT guide](https://docs.river.ai/guides/sft/)
- [GBrain memory access](https://gbrain.io/docs/workspace/memory-anywhere)
- [Memorable API](https://www.memorable.sh/doc)
- [QM MCP connectors](https://github.com/yc-software/qm/blob/main/docs/mcp-connectors.md)
- [Superset Pages](https://docs.superset.sh/pages)
