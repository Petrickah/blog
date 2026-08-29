# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `hugo server --buildDrafts` — local preview, drafts included.
- `hugo` — production build (drafts excluded) into `public/`.
- No linter/test suite; correctness is "does it build and render."

## Architecture

Plain Hugo site: `content/` (articles), `themes/PaperMod` (theme, provisional
— swap freely, it's not a locked-in design choice), `hugo.toml` (config),
`Dockerfile` (multi-stage: builds the Hugo site, then copies `public/` into
an nginx image).

**Who writes a new article's raw voice (decided 2026-08-29)**: Hermes Agent,
not this Claude Code instance — see that project note's "Cine scrie vocea
articolelor" section. This repo's own job is promotion only (rewrite as a
real Hugo file, branch discipline, CI, deploy) — don't originate a new
article's prose here even if asked to "write a blog post," unless the
request is explicitly about editing/formatting an already-drafted piece.

Note: `themes/PaperMod` is itself a git submodule (nested inside this
submodule). `checkout scm` in the Jenkinsfile does **not** initialize nested
submodules by default — the Checkout stage runs an explicit
`git submodule update --init --recursive` for this reason. Don't remove it
without checking `themes/` still resolves in CI.

## Branches

This repo's `main` branch (the only one published here) is deployed via
GitHub Actions on push. Content is written and previewed on a separate,
non-public branch before being promoted here article by article — draft
material never enters this branch's history.
