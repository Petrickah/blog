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

Note: `themes/PaperMod` is a git submodule. Run
`git submodule update --init --recursive` after cloning.

## Branches

This repo's `main` branch (the only one published here) is deployed via
GitHub Actions on push. Content is written and previewed on a separate,
non-public branch before being promoted here article by article — draft
material never enters this branch's history.
