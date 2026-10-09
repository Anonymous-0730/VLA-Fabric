# VLA-Fabric Project Page

Anonymous static project page for:

> VLA-Fabric: Communication-Efficient Coordination for Scalable Networks of VLA Agents

## Local Preview

Open `index.html` directly in a browser. The page has no build step, remote
font dependencies, or runtime network requests. Paper and Code are the primary
resource links; Code opens this repository's `code/` directory on GitHub.
For offline access to the tools and downloads, open `code/index.html`.

The homepage focuses on the idea, architecture, a concise task-success comparison,
communication method, and task demonstrations. Detailed ablations and protocol notes live in
[`code/EVALUATION.md`](code/EVALUATION.md).

## Verification

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s code/tests -v
```

Browser checks use an existing Playwright installation and Chromium executable:

```bash
PLAYWRIGHT_MODULE=/path/to/playwright \
CHROMIUM_EXECUTABLE=/path/to/chromium node tests/browser.cjs
```

This command does not install or download a browser. It checks desktop and
mobile layouts, animation pause, reduced motion, figures, charts, and video.

The download bundle contains only the tools documented in `code/README.md`.
The website and code share this repository. Additional implementation components
will be released progressively; see the code README for the current contents.

After changing the result data or utilities, run `python tools/build_release.py`
to refresh the browser data and allowlisted download bundle.

## Publication

The current GitHub Pages deployment is:

<https://anonymous-0730.github.io/VLA-Fabric/>

The site contains only anonymous, publication-ready artifacts. Raw datasets,
model weights, private logs, author metadata, and server-specific paths are
excluded.
