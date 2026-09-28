import { readFileSync } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { unzipSync } from 'fflate';

const REPO = 'BryanTegomoh/immune';
const WORKFLOW = 'hosted.yml';
const seed = JSON.parse(readFileSync(new URL('../data/recorded-state.json', import.meta.url)));
const cases = JSON.parse(readFileSync(new URL('../data/cases.json', import.meta.url)));
const cache = new Map();
const allowed = new Set(['baseline', 'train', 'connect', 'sync', 'recall', 'correct']);
const fail = (message, status = 400) => Object.assign(new Error(message), { status });

async function github(token, path, options = {}) {
  const response = await fetch(`https://api.github.com${path}`, {
    ...options,
    headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', ...options.headers },
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw fail(
    response.status === 401 ? 'GitHub authorization expired or is invalid.' :
    response.status === 403 ? 'GitHub denied access. Use a repository-scoped token with Actions read/write and Contents read.' :
    `GitHub request failed (${response.status}). No successful operation is being claimed.`,
    response.status === 401 || response.status === 403 ? response.status : 502);
  return response;
}

async function authorize(token) {
  if (!token || token.length > 300) throw fail('Owner authorization is required. Open Owner access.', 401);
  const key = 'auth:' + createHash('sha256').update(token).digest('hex');
  if (cache.get(key)?.until > Date.now()) return;
  const user = await (await github(token, '/user')).json();
  if (user.login.toLowerCase() !== 'bryantegomoh') throw fail('Only the repository owner can operate this workbench.', 403);
  const repo = await (await github(token, `/repos/${REPO}`)).json();
  if (!repo.permissions?.push) throw fail('Repository write permission is required.', 403);
  if (cache.size > 30) cache.clear();
  cache.set(key, { until: Date.now() + 60000 });
}

export function validateCorrection(body) {
  if (!body || !cases.some(c => c.id === body.case_id && c.split === 'train'))
    throw fail('Only fixed synthetic training cases accept corrections.');
  if (!['SHIP', 'REVISE', 'ESCALATE'].includes(body.label) ||
      typeof body.rationale !== 'string' || !body.rationale.trim() || body.rationale.length > 4000)
    throw fail('Choose a valid label and a rationale of 1–4000 characters.');
  return { case_id: body.case_id, label: body.label, rationale: body.rationale.trim() };
}

async function hostedState(token) {
  const response = await github(token, `/repos/${REPO}/actions/workflows/${WORKFLOW}/runs?branch=main&per_page=20`);
  const { workflow_runs: runs } = await response.json();
  const active = runs.find(r => ['queued', 'in_progress', 'waiting', 'pending', 'requested'].includes(r.status));
  let state = structuredClone(seed);
  for (const run of runs.filter(r => r.status === 'completed')) {
    const key = `artifact:${run.id}`;
    if (cache.has(key)) { state = structuredClone(cache.get(key)); break; }
    const { artifacts } = await (await github(token, `/repos/${REPO}/actions/runs/${run.id}/artifacts`)).json();
    const artifact = artifacts.find(a => a.name === 'immune-hosted-state' && !a.expired);
    if (!artifact) continue;
    const response = await github(token, `/repos/${REPO}/actions/artifacts/${artifact.id}/zip`);
    const zip = new Uint8Array(await response.arrayBuffer());
    if (zip.length > 5000000) throw fail('Result archive exceeds the safety limit.', 502);
    const files = unzipSync(zip, { filter: f => f.name === 'state.json' && f.originalSize < 5000000 });
    if (!files['state.json']) throw fail('Job artifact did not contain valid state.', 502);
    state = JSON.parse(new TextDecoder().decode(files['state.json']));
    cache.set(key, structuredClone(state));
    break;
  }
  state.busy = Boolean(active);
  if (active) state.job = { status: 'running', stage: active.status === 'queued' ? 'Queued on GitHub Actions' : 'Running on GitHub Actions', url: active.html_url };
  else if (runs[0]?.status === 'completed' && runs[0].conclusion !== 'success')
    state.job = { status: 'error', error: 'Latest hosted job did not succeed. Inspect its GitHub log before retrying.', url: runs[0].html_url };
  state.hosted_run_url = (active || runs[0])?.html_url;
  return state;
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  try {
    const route = req.query.route || 'state';
    const token = (req.headers.authorization || '').replace(/^Bearer /, '');
    if (req.method === 'GET' && ['state', 'export'].includes(route)) {
      if (token) await authorize(token);
      const state = token ? await hostedState(token) : structuredClone(seed);
      return res.status(200).json({ ...state, cases, hosted: true, authenticated: Boolean(token),
        configured: { River: Boolean(token), GBrain: Boolean(token), Memorable: Boolean(token) },
        evidence_note: 'Recorded hackathon run: 11/12 before and after. H12 improved; H07 regressed. No net accuracy improvement. Training-run procedure drafts failed the no_postcondition gate.',
        storage_note: 'Owner changes are saved as GitHub Actions artifacts, retained for 90 days. Export important experiments.' });
    }
    if (req.method !== 'POST' || !['action', 'correct', 'auth'].includes(route))
      throw fail('Not found.', 404);
    if ((req.headers['content-type'] || '').split(';')[0] !== 'application/json') throw fail('JSON required.', 415);
    const origin = req.headers.origin;
    if (origin && new URL(origin).host !== req.headers.host) throw fail('Cross-origin writes are not permitted.', 403);
    await authorize(token);
    if (route === 'auth') return res.status(200).json({ authenticated: true });
    const body = req.body;
    if (!body || typeof body !== 'object' || JSON.stringify(body).length > 20000) throw fail('Invalid request body.');
    const action = route === 'correct' ? 'correct' : body.action;
    if (!allowed.has(action)) throw fail('Unknown action.');
    if (action === 'train' && body.confirm_training !== true) throw fail('Confirm training spend and use of the saved reviewed cases.');
    const correction = action === 'correct' ? validateCorrection(body) : {};
    const state = await hostedState(token);
    if (state.busy) throw fail('A hosted job is already active. Wait for it to finish.', 409);
    if (action === 'train' && !Object.keys(state.corrections || {}).length) throw fail('Save at least one expert correction first.');
    await github(token, `/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
      method: 'POST',
      body: JSON.stringify({ ref: 'main', inputs: { action, correction: JSON.stringify(correction),
        request_id: randomUUID(), confirm_training: String(body.confirm_training === true) } }),
    });
    return res.status(202).json({ status: 'queued', message: 'Job accepted by GitHub. Results appear after the runner finishes.', url: `https://github.com/${REPO}/actions/workflows/${WORKFLOW}` });
  } catch (error) {
    return res.status(error.status || 502).json({ error: error.status ? error.message : 'Hosted request failed. No successful operation is being claimed.' });
  }
}
