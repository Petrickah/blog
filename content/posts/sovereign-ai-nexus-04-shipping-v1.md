---
title: "Sovereign AI Nexus, Part 4: Shipping v1"
date: 2026-08-26
draft: false
series: ["sovereign-ai-nexus"]
tags: ["fastapi", "react", "docker", "postgresql", "testing", "pytest"]
---

Part 3 ended with the backend able to talk to Claude Code, but no way for a person to talk to any of it. This one covers the rest of the distance to v1: a UI, a Docker Compose stack that actually works end to end, a way to see and delete conversation history, and lastly, a test suite, built specifically so the next change doesn't need a live browser to verify.

## A UI, and a bug that only shows up in markdown

The chat UI itself is unremarkable in the good way: a controlled input, Enter to send, Shift+Enter for a new line, disabled while a response is pending. The more interesting part is what happens to the response once it arrives. Claude Code's replies come back as markdown and rendering that as plain text loses all of it. Using the `react-markdown` plus `remark-gfm` modules fixed that in about ten lines; user messages stay plain text, since they're not meant to be formatted.

## The bug that only exists in the built version

Docker Compose was already running backend, frontend, and Postgres separately in dev (`pnpm dev`, `docker compose up` for the rest). The actual test: a full `docker compose up` from nothing, then a real browser hitting `:3000` is where things fell apart, in two layers.

The first layer was the one I expected: no CORS headers on the backend, so a browser calling `:8000` directly from `:3000` gets blocked. The fix was small: use the `CORSMiddleware` module scoped to a `FRONTEND_ORIGIN` environment variable. CORS stands for Cross-Origin Resource Sharing and is a security feature used by web browsers to control how a website on one domain can request and access resources from a different domain. It was chosen over a reverse proxy specifically because this app still isn't exposed publicly; a proxy earns its complexity once that changes, not before.

The second layer was quieter, and CORS headers wouldn't have fixed it. The frontend's `fetch('/chat')` and `fetch('/history')` calls use relative paths. In `pnpm dev`, Vite's own proxy rewrites those transparently to `:8000` so it looked correct. But the Docker frontend serves a static production build (`serve -s dist`), with no proxy layer at all. A relative `/history` request there just hits the frontend's own static server, finds no matching file, and falls through to `index.html`. This caused the app's own shell to be silently returned in place of JSON. No error, no crash, just the wrong response shape. It surfaced by literally running `curl :3000/history` and noticing HTML come back where JSON should have been. This is the kind of gap that only shows up when you run the real, built artifact, not when you re-read the code that produced it.

The fix: bake the backend's real origin into the static build itself as a `VITE_API_BASE_URL` build argument threaded through `frontend/Dockerfile` and `docker-compose.yml`. Vite inlines `VITE_*` variables at build time, so the compiled JS calls the backend directly, origin and all, with no proxy required.

## Conversation history, for real this time

The `exchanges` table always had an `id` column but nothing before now had ever selected it. Adding it to the response model was the easy part; three endpoints followed naturally: `GET /history` for the full conversation, `DELETE /history/{id}` for a single exchange, and `DELETE /history` for everything.

The UI treats a prompt/response pair as the actual unit of storage, which makes it the natural unit of deletion too so history loads on page mount (a refresh won't lose the conversation in this way), each exchange gets its own delete control, and clearing everything sits behind an explicit confirm/cancel step, since there's no undo once it's gone.

## Tests, so the browser stops being the test

Every one of the bugs above and the two from Part 3 were caught by hand: reading a stack trace, running `curl`, opening a real browser. That works, but it doesn't scale, and it doesn't repeat automatically. The last piece of v1 was a test suite built specifically so a future change can be verified without a browser at all.

The one real decision here was the backend's test database: a disposable Postgres, not SQLite. It would have been faster to fake it but the raw SQL in this codebase is Postgres-specific, and two of the bugs already found (the composite-column `SELECT` and the timestamp-ordering one) are exactly the kind that a friendlier substitute database could paper over instead of catching. Testing against the real thing paid for itself immediately: writing the fixtures surfaced a genuine deadlock where the app's read methods never closed their implicit transaction, which was harmless in a long-lived production connection but left a lock held just long enough to hang the next test's cleanup. Something SQLite would never have shown at all. This could've been prevented by explictly calling SQLAlchemy's own `.commit()` on the connection after a query was called.

The two regression tests for Part 3's bugs weren't just written to check current behavior. This was done so each one can be verified by literally reintroducing the original bug, watching the test fail, then reverting it. The frontend side is smaller in comparison: Vitest and React Testing Library, `fetch` mocked, covering send-and-render, per-exchange delete, and the clear-all confirmation gate.

## Where it stands

The v1 is done: the chat, the persisted and deletable history, a Docker Compose stack that survives a clean checkout, and a test suite that means the next change doesn't have to be verified by hand. What comes after this is a larger, deliberately undated idea. Turning this into something closer to a content system than a chat demo and it stays exactly that: available whenever there's real appetite for it, not scheduled. This would include a deliberate stage for automatic deployment of the app over to Kubernetes, using a lightwight version of it called K3s.

---

**[All posts in this series →](/series/sovereign-ai-nexus/)** · **[Project page →](/projects/sovereign-ai-nexus/)**
