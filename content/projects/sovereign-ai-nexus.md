---
title: "Sovereign AI Nexus"
subtitle: "self-hosted AI chat + artifact platform"
date: 2026-08-20
weight: 10
featured: true
summary: "A small, self-hosted FastAPI + PostgreSQL + React platform for AI-assisted chat and generated artifacts — built incrementally, no metered API costs."
repo: "https://github.com/Petrickah/sovereign-ai-nexus"
---

Sovereign AI Nexus is a small, self-hosted AI chat and artifact web app. It uses a FastAPI/PostgreSQL backend, a React/TypeScript frontend, and an LLM layer that delegates to existing tooling instead of adding new metered API costs.

## Why

I had multiple separate ideas for a Backend and AI Engineering portfolio project. None of them got built, mostly because each tried to prove too much at once — a backend split across multiple languages, telemetry, multi-agent orchestration, all at once. This one starts deliberately small: one language on the backend, one real end-to-end flow, everything else as later, unscheduled work.

## Architecture (v1)

- **Backend**: Python, FastAPI, PostgreSQL (SQLAlchemy). A single service, split into separate containers only where it matters (backend, frontend, database).
- **Frontend**: React, TypeScript, Vite. A dashboard-style web app that talks to the backend.
- **LLM layer**: delegates to the Claude Code CLI (subscription-based) or OpenRouter — no pay-as-you-go API key.
- **Infra**: Docker Compose from day one.

## Status

Backend and frontend scaffolds are running locally with a working dev loop (hot-reload, containerized builds), and CI is wired end-to-end — every push builds both images and mirrors the commit to GitHub. No database and no real chat endpoint yet; that's next. No fixed timeline, by design.

Following the build, one small step at a time → [Full build series](/series/sovereign-ai-nexus/)
