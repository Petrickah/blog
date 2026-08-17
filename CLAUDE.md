# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `hugo server --buildDrafts` — local preview, drafts included.
- `hugo` — production build (drafts excluded) into `public/`.
- No linter/test suite; correctness is "does it build and render."

## Architecture

Plain Hugo site: `content/` (articles), `themes/PaperMod` (theme, provisional
— swap freely, it's not a locked-in design choice), `hugo.toml` (config),
`deploy/preview.yaml` (k8s Deployment+Service for the local preview),
`Dockerfile` (multi-stage: builds the Hugo site, then copies `public/` into
an nginx image). `content/` is also exposed inside the author's Obsidian
vault as the `09_Blog` habitat (a relative symlink, `vault/09_Blog ->
05_Projects/code/blog/content`) — there is no separate sync step, it's the
same files.

Note: `themes/PaperMod` is itself a git submodule (nested inside this
submodule). `checkout scm` in the Jenkinsfile does **not** initialize nested
submodules by default — the Checkout stage runs an explicit
`git submodule update --init --recursive` for this reason. Don't remove it
without checking `themes/` still resolves in CI.

## Branch convention (draft/public separation)

- **`drafts`** (default branch, Gitea-only): day-to-day writing branch. Never
  mirrored to GitHub. Jenkins builds this branch with `--buildDrafts` and
  serves a local preview.
- **`main`**: only branch mirrored to GitHub (Gitea push-mirror) and deployed
  publicly via GitHub Actions -> Cloudflare Pages. Built without
  `--buildDrafts`.
- **Promoting an article**: when a draft is ready to publish, `git cherry-pick`
  its specific commit(s) from `drafts` onto `main` — do not merge `drafts`
  into `main` wholesale, and do not rely on Hugo's `draft: true/false`
  frontmatter alone as the publication gate. The point of the two-branch split
  is that unpublished article text never enters `main`'s history at all, so
  it never reaches the public GitHub mirror. Frontmatter `draft:` still
  matters for build-time filtering, but it's not what keeps a draft private.

## CI

- **`drafts` branch** (live, verified 2026-08-17): Jenkins multibranch job
  (Gitea webhook-triggered). Build & Push stage runs Kaniko with
  `--build-arg BUILD_DRAFTS=true` on this branch, pushes to
  `192.168.1.20:5000/blog:drafts-<build>`. Deploy preview stage (branch
  `drafts` only) applies `deploy/preview.yaml` (image tag substituted via
  `sed`) using a `kubectl` container added inline in the Jenkinsfile's pod
  spec (not in the shared `kaniko` pod template, to avoid affecting other
  jobs like `ci-pilot`), running as the dedicated `previews-deployer`
  ServiceAccount (namespace `jenkins-agents`, RBAC scoped to the `previews`
  namespace only). Preview: `http://192.168.1.20:30080/` (NodePort, fixed —
  reusable pattern for future static-site projects on a different port).
- **`main` branch**: not yet wired (planned — Gitea push-mirror to GitHub +
  `.github/workflows/deploy.yml` -> Cloudflare Pages via
  `cloudflare/pages-action`). Update this section once live.

Real gotchas paid for while wiring this up (Hugo-on-Alpine +
Kubernetes-plugin specific, not generic knowledge — worth knowing before
touching this Dockerfile/Jenkinsfile again): `hugo_extended` binaries are
dynamically linked against glibc and fail with a misleading "not found" on
Alpine (musl) unless `libc6-compat`/`libstdc++` are installed; a Hugo site
with zero theme/layouts produces no `index.html` at all (silent — no build
error); `bitnami/kubectl` no longer publishes plain version tags and
`rancher/kubectl` has no shell, hence `alpine/k8s:1.36.2` for the deploy
container. Full list in the project note's "Note tehnice de implementare"
section.
