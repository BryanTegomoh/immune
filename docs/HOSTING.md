# Hosted IMMUNE

The Vercel deployment serves the React workbench and a stateless Node API. Long-running operations execute in the owner-authorized `hosted.yml` GitHub Actions workflow. The original loopback Python server remains available.

Production: https://immune-chi.vercel.app. The project is named `immune`; `immune.vercel.app` was already in use. GitHub `main` is connected to Vercel for subsequent deployments.

## Access and secrets

- Public visitors can inspect a sanitized, recorded synthetic experiment, case decisions, per-case results, and the demo video. Public pages never claim fresh inference or new training.
- Only GitHub user `BryanTegomoh`, with write permission on `BryanTegomoh/immune`, can dispatch hosted work. Owner access accepts a fine-grained token restricted to this repository with Actions read/write and Contents read.
- The owner token is held in browser memory, transmitted over HTTPS to the Vercel API and GitHub, and never intentionally persisted or logged. Reloading locks owner access.
- River, GBrain and Memorable credentials remain in the existing repository Actions secrets. They are not copied into Vercel or the browser.
- All owner operations use the fixed synthetic dataset. Do not enter patient data, credentials, or private information in rationales. Workflow metadata and logs may be visible to repository readers.

## Real operations

Saving a correction dispatches a lightweight job that validates the training case, label and rationale and saves state. Baseline, training, GBrain discovery, sync and recall dispatch provider-backed jobs. Training requires a separate confirmation and may consume credits. Do not submit a second operation until the current one completes.

Jobs share the repository's existing serial concurrency group. Each runner restores the most recent hosted state and uploads the updated state, including failed operations, as an artifact. The web app polls for status every 15 seconds. Refreshing or closing the page does not stop a dispatched job.

Artifacts expire after 90 days. Export important experiments; this is not a permanent database. When no saved artifact remains, the workbench falls back to the clearly identified recorded synthetic seed. GitHub concurrency allows only one pending job; multiple simultaneous owner tabs are not supported.

## Evidence boundaries

The public seed is the completed hackathon experiment: 12 approved examples, 12 training steps, 11/12 correct before and after; H12 improved while H07 regressed. There was no net accuracy improvement and no clinical validation.

Raw workspace recall and GBrain receipts are removed from the public seed. Training-run Memorable drafts failed the `no_postcondition` gate. A separate memory demonstration returned `admitted=true` with `judge_unparseable`; neither outcome establishes validated procedure quality.

## Deployment and checks

Run `npm ci && npm run build`, `node --test tests/hosted-api.test.js`, and `python -m unittest discover -s tests -v`. Deploy the repository root with the included `vercel.json`. The frontend output alone is not the full application.

The hosted API requires no provider environment variables. Owner authorization must be supplied in the app before mutations work. The `immune/hosted.py` runner uses Python 3.12 in Actions. Existing local/MCP functionality is not served as a public MCP endpoint.
