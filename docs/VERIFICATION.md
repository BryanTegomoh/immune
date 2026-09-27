# Verification record

Built during the September 27, 2026 hackathon session.

## Functional checks completed

- Production frontend build passed with React 19.3.0 and Vite 7.3.6.
- Eight automated integrity tests passed: split validation, no reference labels/rationales in prompts, held-out correction rejection, completion-only token alignment, always-escalate baseline, strict output parsing, credential gating, correction-revision invalidation, and invalid-label rejection (some tests cover multiple assertions).
- River client 0.12.0 installed (Python 3.12+ required for live integrations). Adapter calls checked against installed signatures for sampling, model creation, forward/backward, optimizer step, and checkpoint save.
- MCP 1.30.0 installed. Local stdio initialization and discovery of all three IMMUNE tools passed. This is not proof of registration in QM.
- GBrain argument construction validated against a representative content schema. Actual workspace schema discovery requires a token and remains unverified.
- HTTP checks rejected held-out corrections, training without a key, and a mutation with an untrusted Origin.
- Browser interaction checks passed: review and save a correction; reload and verify persistence; next-case navigation; open connection instructions; export JSON.
- No browser page errors. No horizontal page overflow at 390 x 844; the results table intentionally scrolls within its container.
- All QA corrections were saved in isolated temporary state. The delivered app begins with zero human approvals and no evaluation scores.

## Visual verification

The generated concept was inspected with view_image, along with the actual desktop and mobile browser screenshots. The selected design was faithfully implemented in its typography hierarchy, white-and-lime palette, open two-column layout, evidence blocks, decision controls, and evaluation table, subject to the functional changes below. This is a comparison of the real rendered UI with the concept, not a screenshot used as the UI.

- Concept: `generated_images/exec-3d405aec-6697-4953-ada6-0b43b428889c.png` in the originating conversation workspace, 1505 x 1045.
- Browser method: Playwright using a separately launched local Chromium. The provided cloud browser could not open the loopback URL (ERR_BLOCKED_BY_CLIENT). The standard browser download failed; a Chromium binary from the established @sparticuz/chromium package was used for local testing.
- Viewports: 1440 x 1000 desktop, 390 x 844 mobile, and a final 1505 x 1045 render matching the concept width and viewport height. Full-page screenshot is taller because functional setup controls extend below the main workbench.
- Final screenshot: `IMMUNE-preview.png`, supplied alongside the source archive.

| Comparison | Result |
|---|---|
| Main copy and hierarchy | IMMUNE, title, subtitle, and the four-step rail preserved. |
| Palette | White background, dark type, gray evidence surfaces, lime active choices preserved. |
| Layout | Open review/ledger columns and full-width result table preserved; mobile stacks them. |
| Type | Sans hierarchy with monospace evidence and metadata; system fallback fonts used. |
| Controls | Three decision choices, rationale input, and save action are real controls. |
| Provider rows | Name/description collision found and corrected with wider first column. |
| Disabled controls | Low-contrast opacity treatment replaced by readable unavailable states. |
| Responsive view | Main controls remain usable; result table scrolls internally; no page overflow. |

Intentional changes from the concept: added Train & verify, next-case, connection, memory sync/recall, export, and setup controls; added approval count and honest reference-label note; changed the result column from Expert to Reference because synthetic labels are not yet physician-reviewed; used disabled button styling when keys are absent. Above-the-fold copy review found only these purposeful workflow and provenance additions. No decorative imagery or simulated performance was added. No material visual collision remains after the correction.

## Unverified and out of scope

- Live River health and model-capability calls passed at 16:14 PDT on September 27, 2026. Qwen/Qwen3.5-9B is listed. No weight update or checkpoint creation has completed yet.
- Connection-check evidence: https://github.com/BryanTegomoh/immune/actions/runs/36357991859. All eight integrity tests also passed on the GitHub runner. The overall check failed because GBRAIN_TOKEN was absent; this does not invalidate the successful River check.
- No GBrain write/recall or Memorable extraction was performed here: no tokens supplied.
- No QM deployment was configured, no Superset page created, and no UFO extension installed.
- No measured accuracy gain is claimed.
- The application is a loopback-only hackathon prototype, not a production service or medical product.
- The small, synthetic evaluation supports a demo of the mechanism. It does not establish clinical safety or generalization to other domains.
