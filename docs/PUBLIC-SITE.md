# Public IMMUNE site

The Vercel presentation was built after the hackathon submission. The original Python workbench remains available with `python -m immune.server`.

Run `npm ci` and `npm run dev:site` to develop the public site; `npm run build:site` produces `site-dist`. Vercel uses `npm run build:public` to assemble the public homepage and the full workbench at `/workbench/`. Existing owner authorization and API routing are preserved.

The site is static. It exposes synthetic cases and the completed experiment from run 36359516068. It does not accept provider credentials, call paid providers, or modify the original experiment. Review exercises use browser local storage and can be exported as JSON.

## Design specification

Reference: `exec-e695631b-b14d-4bd7-a0a8-18ccca94c269.png`, generated for this public-site revision. White background, charcoal text, lime accents, quiet gray evidence surfaces. A neutral sans-serif body and headings, with system monospace for evidence and metadata; system fonts avoid third-party font requests under the existing security policy. Open metric rail, split case navigator and detail panel, small pill labels for outcomes, restrained borders, no decorative imagery.

Primary navigation: Experiment, Try a review, About. The header action is Open workbench so the existing hosted application stays accessible; source links are available through the evidence and documentation. Hero: Expert judgment. Measurable learning. Main views: case explorer and training trace. The review and about views extend the same component system to support the requested public demonstration.

Intentional evidence corrections to the visual concept: generated medical case text and invented subcategories are replaced by the exact synthetic dataset. Model outputs contain only the recorded decision, with no invented reasoning. The result note and provenance are retained.

The experiment JSON contains only public synthetic cases, model settings, losses, raw predictions, and provenance. API keys and raw application state are excluded.

## Verification

Production Vite build passed. Local Chromium was used because the cloud browser blocked the loopback preview. Functional checks passed for case filtering, improved/regressed navigation, checkpoint disclosure, review persistence after reload, JSON export, and video playback (87.68 seconds). Desktop was inspected at 1536 × 1200 and mobile at 390 × 844. No page-level JavaScript errors or horizontal page overflow were found.

The concept and final browser screenshots were inspected directly with view_image. Fidelity review covered headline and navigation copy, split layout, typographic hierarchy, white/charcoal/lime palette, evidence surfaces, outcome tags, and responsive flow. The code follows the visual specification, with the factual corrections noted above. Mobile changes the sidebar into a horizontal case selector; no medical imagery or invented result text is used. An early screenshot captured a transition mid-animation; the final review used settled animation states. No material visual overlap remains.
