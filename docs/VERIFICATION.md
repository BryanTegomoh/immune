# Verification record

Built during the September 27, 2026 hackathon session.

## Functional checks completed

- Production frontend build passed with React 19.3.0 and Vite 7.3.6.
- Eight automated integrity tests passed: split validation, no reference labels/rationales in prompts, held-out correction rejection, completion-only token alignment, always-escalate baseline, strict output parsing, credential gating, correction-revision invalidation, and invalid-label rejection (some tests cover multiple assertions).
- River client 0.12.0 installed (Python 3.12+ required for live integrations). Adapter calls checked against installed signatures for sampling, model creation, forward/backward, optimizer step, and checkpoint save.
- MCP 1.30.0 installed. Local stdio initialization and discovery of all three IMMUNE tools passed. This is not proof of registration in QM.
- GBrain tool schema discovery, argument construction, write, and exact diagnostic recall verified against the live workspace; see the recorded run below.
- HTTP checks rejected held-out corrections, training without a key, and a mutation with an untrusted Origin.
- Browser interaction checks passed: review and save a correction; reload and verify persistence; next-case navigation; open connection instructions; export JSON.
- No browser page errors. No horizontal page overflow at 390 x 844; the results table intentionally scrolls within its container.
- All QA corrections were saved in isolated temporary state. The delivered app begins with zero human approvals and no evaluation scores.

## Interface verification

Desktop and mobile browser checks covered case review, correction persistence, navigation, connection instructions, and JSON export. Tested viewports included 1440 × 1000 and 390 × 844. The mobile layout stacks the review and ledger columns; the result table scrolls internally without page overflow.

The interface uses real decision controls and provider-dependent actions. Reference labels are identified as synthetic and unreviewed. No simulated performance is presented as a live result.

## Live verification update

- River baseline completed: 11/12 correct, zero invalid outputs, zero missed required escalations; one REVISE reference was predicted ESCALATE. Source: https://github.com/BryanTegomoh/immune/actions/runs/36358066104
- GBrain authentication, write, and exact diagnostic-fact recall passed. Memorable extraction ran on a real completed task trace; its draft was stored and retrieved through GBrain. Source: https://github.com/BryanTegomoh/immune/actions/runs/36359383279
- Memorable returned admitted=true and reason=judge_unparseable on the second run. Do not describe this as validated procedure quality. The original draft had been rejected for no_postcondition.
- Superset launch configuration and self-contained evidence page are prepared but have not been used/published in Superset.

## Remaining limitations

- Live River health and model-capability calls passed at 16:14 PDT on September 27, 2026. Qwen/Qwen3.5-9B is listed. No weight update or checkpoint creation has completed yet.
- Connection-check evidence: https://github.com/BryanTegomoh/immune/actions/runs/36357991859. All eight integrity tests also passed on the GitHub runner. The overall check failed because GBRAIN_TOKEN was absent; this does not invalidate the successful River check.
- Expert-reviewed correction sync and paired River training remain pending label review. The verified memory round-trip used a diagnostic record, not an expert correction.
- No QM deployment was configured, no Superset page created, and no UFO extension installed.
- No measured accuracy gain is claimed.
- The application is a loopback-only hackathon prototype, not a production service or medical product.
- The small, synthetic evaluation supports a demo of the mechanism. It does not establish clinical safety or generalization to other domains.
