# Blog

Personal portfolio blog (Hugo static site) — articles about the projects in
this monorepo and, eventually, about the author's professional path.
Deployed on Cloudflare Workers (static assets).

## Overview

Static site generated with [Hugo](https://gohugo.io/), theme
[PaperMod](https://github.com/adityatelange/hugo-PaperMod) (provisional).

## Setup

```bash
hugo version   # tested with v0.165.0
```

## Usage

```bash
hugo server   # local preview
hugo build    # production build -> public/
```

Deployed automatically on push to `main` via GitHub Actions
(`.github/workflows/deploy.yml`), which runs `wrangler deploy` against
`wrangler.jsonc` + `build.sh`.
