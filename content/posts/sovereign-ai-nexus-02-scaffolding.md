---
title: "Sovereign AI Nexus, Part 2: What Broke While Scaffolding"
date: 2026-08-20
draft: false
series: ["sovereign-ai-nexus"]
tags: ["fastapi", "docker", "kaniko", "ci-cd", "jenkins"]
---

The first post in this series was about the decision — why I'm starting small, why the earlier project ideas never got built. This one is about the day I actually wrote code, and about what broke along the way — because almost nothing worked on the first try, and I think that part is more interesting than if it had gone perfectly.

## The scaffold itself

For the backend I used FastAPI and uvicorn, managed with `uv` — fast, and about as simple as it gets to wire up: a `@app.get(path="/")` decorator over the handler function. For the frontend, React and TypeScript, scaffolded with Vite.

Each service becomes its own image via its own Dockerfile. The project orchestrates both containers through a `docker-compose.yml` at the root. Nothing unusual so far.

## The reload that refused to work

The first thing I tested was backend hot-reload — edit a local file, expect to see the change without a rebuild. Nothing happened. I added `--reload` to uvicorn. Still nothing.

The real cause: the volume in `docker-compose.yml` mounted the host code to `/code/app` inside the container, but uvicorn was importing the app from `core.main:app` — i.e. from `/code/core`, a completely different path. My edits were landing in a directory nobody was reading. Simple fix once found: the mount has to target the exact import path, not a generic convention copied from a tutorial.

## `pnpm add -g` and a PATH that doesn't exist

On the frontend, the production build needed to serve static files through a package called `serve`, installed globally (`pnpm add -g serve`). The error: pnpm's global bin directory wasn't on `PATH` — and it had no way to be, since `pnpm setup` (which would normally fix this) edits a `.bashrc`, and a Docker `RUN` step has no interactive shell to read it.

The cleaner fix wasn't patching PATH — it was avoiding the global install entirely: add `serve` as a normal project dependency and run it through `pnpm exec serve`, which resolves the binary from `node_modules/.bin` with nothing global involved.

## A mount that broke exactly what it was meant to help

After fixing reload on the backend, I tried the same trick on the frontend — mount the whole codebase over `/app`. Result: a 404 on every request. The reason: the frontend container runs the already-built app (`serve -s dist`), not a dev server watching for changes. The mount replaced the entire `/app` from the image — including `dist/`, built at image-build time — with the host directory, which had no `dist/` at all.

The lesson: not every container benefits from a volume mount. For real frontend iteration, the right answer isn't Docker — it's running `pnpm dev` directly. Vite already has native HMR, faster than anything I could build through a container.

## Kaniko is not BuildKit

The most subtle bug came from CI, not local development. I used `uv`'s own official Docker recipe — `RUN --mount=type=bind,source=uv.lock,...` — which worked perfectly locally. On Jenkins, the build failed with "No pyproject.toml found," an error that made no sense at first glance.

The cause, found straight from the Kaniko build log: `RUN --mount` is BuildKit-specific syntax, and Kaniko — the actual builder behind this CI — ignores it entirely, silently. No unknown-syntax error, it just runs the command without the mounts it was promised. The files never landed where `uv sync` was looking for them. The fix was a plain `COPY` — less elegant than the official recipe, but portable across builders, not just my machine.

On top of that: a `uv.lock` that had ended up gitignored by mistake, from a template meant for libraries rather than applications. A lockfile should always be committed for an application, exactly like a `package-lock.json`.

## CI/CD: one image per service, one SSH key per repo

For the build side, I went with a single `Jenkinsfile` with separate stages per service (backend, frontend) rather than separate Jenkins jobs — a build failure in one service doesn't block the other, without paying the setup cost of a whole new job.

The more interesting part was mirroring to GitHub. I wanted a single SSH key, with its blast radius scoped per-repo via GitHub Deploy Keys, rather than a new token to manage for every mirrored project. Gitea's native Push Mirror doesn't support SSH — confirmed directly from source, not just from failed attempts. The fix: the push happens from a dedicated Jenkins stage, right after checkout, using the key as a Jenkins credential — independent of whether the Docker build succeeds, so syncing to GitHub never depends on anything else.

## What's next

The next real step is Postgres — one table, one SQLAlchemy model, nothing more. No deadline attached; it happens when it happens.

---

→ [Full build series](/series/sovereign-ai-nexus/) · [Project page](/projects/sovereign-ai-nexus/)
