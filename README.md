# IMMUNE

**An immune system for AI agents.**

A local workbench that turns human corrections into incident memory, optional procedure drafts, and supervised updates to a River-hosted open-weight model. Built from scratch during the September 27, 2026 hackathon. No prior project code was imported.

## Start in 30 seconds

Python 3.10+ is enough to open the bundled workbench. The compiled UI is included.

```bash
cd immune
python3 -m immune.server
```

Open **http://127.0.0.1:8765**. On Windows use `python` instead of `python3`.

Without credentials you can review cases, save corrections, inspect connection status, and export the record. There are no simulated model results. The Run baseline and Train & verify buttons are disabled until River is configured.

## Provide credentials securely through GitHub

In this private repository, open **Settings > Secrets and variables > Actions > New repository secret**. Add:

- `RIVER_API_KEY`: your River API key.
- `GBRAIN_TOKEN`: a token connection for your GBrain client with Full memory access.
- `MEMORABLE_API_KEY`: optional, for procedure extraction.

These are Actions secrets, not files, issues, chat messages, or repository variables. GitHub injects them into the manual workflow; they do not need to be read back or copied into this conversation.

Open **Actions > IMMUNE live experiment > Run workflow**. Start with `check-connections`. This checks River health/model access and GBrain tool discovery without training or writing memory. Once the selected training labels have been reviewed, choose `train`, enter their IDs (for example `T01,T02,T03`), and confirm review. The workflow records those approvals, syncs to GBrain, recalls the incidents, and runs the paired River training/evaluation. Its results are downloadable as a private artifact. It does not run automatically on pushes.

The GitHub workflow does not automatically configure your laptop. To run the UI and integrations locally, follow the `.env` setup below. To inspect a completed Actions run locally, place the artifact's `state.json` at `runs/state.json` before starting the server.

## Connect the live learning loop

**Python 3.12 or newer is required by river-client 0.12.0.** Check `python3 --version` before creating the environment.

In the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and copy with `Copy-Item .env.example .env`.

Edit `.env` locally. Do not paste credentials into chat, commit them, or expose this server publicly.

```dotenv
RIVER_API_KEY=your_river_key
RIVER_MODEL=Qwen/Qwen3.5-9B
GBRAIN_TOKEN=your_gbrain_connection_token
MEMORABLE_API_KEY=optional_memorable_key
```

Restart using the activated environment:

```bash
python -m immune.server
```

GBrain setup: open your hackathon workspace, add its Memory application to a client with **Full** access, then create a token connection. The app connects to `https://gbrain.io/mcp`, discovers the current tool schemas, and validates arguments before calling `remember` and `recall`. It stops visibly if your workspace exposes an unsupported schema. The discovered schemas appear in the exported experiment; use the optional JSON argument templates in `.env.example` if needed.

Confirm River model access before training:

```bash
python -m immune.cli models
```

If the default model is unavailable, select an available model from that output and update `RIVER_MODEL`. Tokenizer downloads require access to Hugging Face. River uses its hosted training service; no local GPU or PyTorch model installation is needed.

## Demo sequence

1. Click **Connect GBrain**. Tool discovery must succeed.
2. Click **Run baseline**. Wait for actual predictions on 12 fixed held-out cases.
3. Review training cases. Select SHIP, REVISE, or ESCALATE, edit the rationale, and save. Use **Next case**. Review at least T01 through T12, including acceptable examples. Every prefilled label/rationale is a draft until you approve it.
4. Click **Sync corrections**, then **Recall incidents**. Show the retrieved GBrain record. If Memorable is configured, extraction produces procedure drafts in the same sync operation.
5. Click **Train & verify**. This starts a fresh paired experiment: baseline, 12 LoRA updates on approved cases, checkpoint save, then evaluation on the same held-out inputs. The complete run is asynchronous; the browser shows progress.
6. Inspect **What changed?** and the raw outputs. Show regressions and invalid outputs as well as improvements. Export the experiment.

Keep the paired experiment running before the pitch, so the judges can inspect completed results. Do not imply that a prerecorded run is occurring live. A separate baseline run is optional; Train & verify measures its own baseline to ensure a matched comparison.

## What is implemented, and what still needs verification

| Component | Implementation | Status at handoff |
|---|---|---|
| UI | React/Vite, correction review, persistence, export, responsive layout | Built locally |
| River | Official SDK, LoRA, completion-only loss, fixed before/after prompts, checkpoint, raw predictions | SDK signatures checked; credentials needed for live run |
| GBrain | Streamable HTTP MCP discovery, schema validation, remember/recall | Adapter implemented; credentials and workspace schema need live verification |
| Memorable | Documented `/v1/extract`, actual review trace, locally stored draft | Adapter implemented; optional key needed |
| QM | Local MCP tool server, stdio or HTTP, for running experiments and reading results | Tool surface included; not registered in a QM deployment |
| Superset | This source folder can be opened as the hackathon project | Not used in this environment |
| UFO | No integration | Not implemented |

**The hackathon requires GBrain use. The River prize requires real River training. This package alone does not establish either qualification. Complete and show the live calls.**

## Evaluation contract

- 24 training cases and 12 held-out cases, each split balanced across the three labels.
- Cases authored during this session. No patient records or external dataset used.
- Held-out examples are inaccessible to the correction endpoint and never enter the training batch. Similar failure categories occur in both splits; this is a small transfer demonstration, not an independent clinical validation dataset.
- Only the case context and assistant output enter the prompt. Case IDs, reference labels, rationales, and failure-family tags are excluded.
- Baseline and trained model receive identical token IDs, greedy decoding, seed 27, and a 32-token answer budget. The first and final evaluation share one model instance in each paired run.
- Strict label parsing: extra text is INVALID. Format compliance can improve without deeper reasoning improvement; inspect raw outputs.
- Accuracy, missed required escalations, unnecessary escalation on acceptable outputs, and invalid outputs are reported. An always-ESCALATE policy scores only 4/12 and unnecessarily escalates all four acceptable cases.
- Reference labels are synthetic draft labels. Review them before using these results as expert evaluation. If you edit labels or cases, begin a new experiment and report the change. Do not optimize repeatedly against this tiny held-out set and call it fresh validation.
- Twelve full-batch steps, rank 16, learning rate 1e-4; these are initial hackathon settings, not optimized hyperparameters.
- GBrain recall and Memorable drafts are deliberately excluded from the model's evaluation prompt, so the before/after comparison isolates the weight update. There is no memory-only ablation yet.
- This version starts each training experiment from the base model. It does not implement multi-round continual learning or automatic deployment of a new checkpoint.
- One expert correction is not guaranteed to improve an LLM. Gains, if any, apply only to this small synthetic task. No claim of clinical safety, immunity, or novel research priority follows.

## QM extension

Run the app first. For a local MCP-capable harness:

```bash
python -m immune.mcp_server
```

For a QM deployment on the same machine, an administrator can run the loopback HTTP adapter:

```bash
python -m immune.mcp_server --http
```

Its MCP address is `http://127.0.0.1:8767/mcp`. Register it using QM's documented administrator MCP connector route, with access limited to your hackathon scope. This address is local to the process host. A remote QM deployment cannot reach your laptop's loopback address; run both in the same approved environment or have the QM team help configure authenticated transport. Do not make this unauthenticated demo public.

Tools: `evaluation_status`, `approved_corrections`, `run_immune`. The adapter intentionally cannot approve labels on the expert's behalf. It talks to the running app, avoiding a second state writer. Ask the QM agent: "Read the IMMUNE experiment status. Summarize measured changes and failures. Do not claim improvement unless the recorded results support it."

## Development

```bash
npm ci
npm run build
python -m unittest discover -s tests -v
```

`npm run dev` provides the Vite UI at port 5173 with an API proxy to the Python server. Run only one Python state-writing server per `runs` directory. Do not run the mutation CLI concurrently with the UI server. Credentials are loaded at startup. Runtime state is stored in ignored `runs/state.json`; keep it for the demo. Each run records dataset/prompt/training hashes, model identity, losses, checkpoint path, settings, and raw outputs. Environment keys are not included in exports.

## Source documentation

- River SFT: https://docs.river.ai/guides/sft/
- River SDK: https://docs.river.ai/python-api/
- River account/model access: https://docs.river.ai/quickstart/
- GBrain memory access: https://gbrain.io/docs/workspace/memory-anywhere
- GBrain client tokens: https://gbrain.io/docs/tools/assistants
- Memorable extraction: https://www.memorable.sh/doc
- QM connectors: https://github.com/yc-software/qm/blob/main/docs/mcp-connectors.md

See `docs/PITCH.md` for the presentation and `docs/VERIFICATION.md` for local checks and known gaps.
