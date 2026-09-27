# IMMUNE sponsor demo

## Verified live

- River: 11/12 baseline decisions correct on the fixed synthetic held-out set. Zero invalid outputs. Training has not yet run.
- GBrain: a unique diagnostic fact was written and the exact fact retrieved. A Memorable draft was also written and retrieved under entity immune-hackathon.
- Memorable: the extraction API returned a procedure draft from a real completed GBrain task. The first draft was rejected (no_postcondition). A second trace included a real successful repository test run; the API returned admitted=true with reason=judge_unparseable. Preserve that caveat: admission is not evidence of a successful quality assessment, and the draft is not automatically executable.

Evidence:
- https://github.com/BryanTegomoh/immune/actions/runs/36358066104
- https://github.com/BryanTegomoh/immune/actions/runs/36359383279

## Superset: launch and present

The repository includes .superset/config.json and setup.sh. Import this repository into your authenticated Superset workspace. Setup installs the Python clients and checks experiment integrity; Run starts the workbench at http://127.0.0.1:8765.

Publish the prepared presentation from a Superset terminal:

```bash
superset pages publish docs/demo.html --title "IMMUNE: expert feedback to agent memory" --label "Hackathon evidence" --visibility just_me
```

Inspect it first. To share with judges, use the Page's Share control and choose the intended audience. A source file or config alone does not prove Superset use. Capture the running workspace and published Page in the demo.

Superset documentation: https://docs.superset.sh/pages and https://docs.superset.sh/setup-teardown-scripts

## QM: inspect measured results

The local MCP adapter is implemented. It is not registered in a live QM instance.

Run IMMUNE and its HTTP adapter on the same host reachable by your QM deployment:

```bash
.venv/bin/python -m immune.server
# In a second terminal:
.venv/bin/python -m immune.mcp_server --http
```

An authorized QM administrator registers the service using PUT /v1/admin/mcp-servers/immune. For a QM core on the same host, the registration fields are:

```json
{"name":"IMMUNE","url":"http://127.0.0.1:8767/mcp","auth":"none","credentialScope":"shared","readOnly":false,"enabled":true}
```

The loopback address works only when both services share a host/network namespace. Do not point a remote QM service at your laptop's loopback address, expose this unauthenticated adapter publicly, or disable QM's access controls. Ask the QM team to help register it in the hackathon instance.

Ask QM: "Use IMMUNE to read the latest experiment and approved corrections. Explain the baseline, trained results if present, regressions, and whether the evidence supports improvement. Do not approve training cases or invent results."

Available tools: evaluation_status, approved_corrections, run_immune. Model training uses River credits and requires actual human-reviewed corrections.

Documentation: https://github.com/yc-software/qm/blob/main/docs/mcp-connectors.md

## UFO: integration not yet built

Proposed automation: review the IMMUNE run artifact, generate a submission summary with evidence links, and flag unverified claims. No usable sponsor extension API documentation or authenticated UFO workspace was available in this session. Obtain the extension quickstart from the UFO team before implementing or claiming this integration.

## Recording: 90 seconds

1. Explain the problem: an expert correction should remain available across agent sessions.
2. Show a synthetic case and the human review controls. Drafts remain drafts until reviewed.
3. Show the GBrain diagnostic record and its exact retrieval.
4. Show the Memorable procedure and its quality-gate status.
5. Show River's full 12-case baseline: 11 correct, one over-escalation. If training completes, show both columns and the saved checkpoint; otherwise explicitly label it pending.
6. If activated, ask QM for the measured experiment status and open the Superset Page.
7. Close: "IMMUNE makes expert feedback persistent, inspectable, and testable." No claim of clinical validation.
