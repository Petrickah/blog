---
title: "Sovereign AI Nexus, Part 3: Making It Actually Talk"
date: 2026-08-26
draft: false
series: ["sovereign-ai-nexus"]
categories: ["DevLogs"]
tags: ["fastapi", "postgresql", "claude-code", "debugging", "backend"]
---

Part 2 was about the scaffold breaking in four different ways before it worked. This one is about the day the app actually started talking back and about three more bugs, quieter than the ones before.

## Postgres, and a client that shouldn't be reborn every request

Wiring up Postgres was the easy part: a table for `exchanges` (prompt, response, timestamp) and a `DatabaseClient` wrapping a SQLAlchemy connection. The first version created a new client and a new connection on every single request. It worked, but it's the wrong shape: a real app should open one connection when it starts and reuse it, not pay connection overhead on every prompt.

The fix uses FastAPI's `lifespan` context manager: the client is created once, as a global, when the app starts, and closed once, when it stops. It's a small thing, but the difference between "works in a demo" and "works under real traffic." is very important.

```python
db_client = DatabaseClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    db_client.close()

app = FastAPI(lifespan=lifespan)
```

One more bug here, easy to miss: the Postgres container's credentials were hardcoded directly in `docker-compose.yml` (`admin`/`example`), while the backend correctly read them from `.env`. They happened to match, so everything worked right up until someone changes `.env` and the two sides silently disagree. This was fixed by making the database service read the same environment variables as the backend.

## Teaching the backend to delegate

The interesting part: how does a Python backend running in a container actually talk to Claude Code?

The obvious-looking answer is to mount the host's `~/.claude` directory into the container but it turns out to be the wrong one. The real mechanism, already proven in a different part of this same infrastructure (a local AI agent I run for other things), is simpler: `claude setup-token` generates a long-lived OAuth token once and the CLI picks it up from a `CLAUDE_CODE_OAUTH_TOKEN` environment variable. No mounted credentials directory, no interactive login inside the container.

The rest is a normal Docker build: `claude` installed via npm (Node's official Alpine build, chosen specifically to avoid repeating a glibc-vs-musl binary compatibility trap I'd already hit once with a different tool), a persistent named volume for the CLI's own config so it doesn't reset on every restart, and a minimal, empty working directory. For now, there is no need for a real project, since the backend is using Claude Code as a text-generation engine here, not as a coding agent that needs to touch real files.

Delegation itself is a subprocess call, deliberately async so one slow request doesn't block every other one:

```python
proc = await asyncio.create_subprocess_exec(
    "claude", "-p", full_prompt,
    cwd="/workspace",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await proc.communicate()
```

It worked on the first real test. Measured round-trip for a simple prompt: about 3.6 seconds for a full CLI process starting up. Worth knowing before this becomes the path for anything latency-sensitive.

## The bugs that don't announce themselves

The endpoint needed conversation history. I've decided to get the last N exchanges and fed them back in as context so the model isn't starting cold every time. This is where the quiet bugs live.

**Bug one, the loud one.** The query to fetch recent exchanges was written as:

```sql
SELECT (prompt, response, created_at) FROM exchanges ...
```

Those parentheses around the column list look harmless. My wrong assumption was to prevent SQL Injection attacks without knowing Postgres reads that as *one* composite column, not three separate ones. The first test request worked fine, because there was no history yet to fetch. The second one crashed:

```
AttributeError: Could not locate column in row for column 'prompt'
```

A one-word explanation, once you see it: no parentheses, three real columns.

**Bug two, the silent one.** The timestamp was meant to be captured the moment a request arrives right before it goes anywhere near the LLM. The code looked right:

```python
response = ChatResponse(
    prompt=msg.prompt,
    response=await call_llm(msg.prompt),   # ~3.6s
    created_at=datetime.now(timezone.utc),
)
```

But... Python evaluates keyword arguments in the order they're written, not by name. The `created_at` argument is the last one on the page, so it's the last thing evaluated after the multi-second LLM call already finished. The timestamp was quietly measuring the wrong moment. Fixed by capturing it as its own variable, first line of the function, before anything else runs.

**Bug three, the one that ate its own fix.** Recent-history queries naturally come back newest-first. Fed straight into a prompt, that reads backwards to the model: the last message first and the first message last. The fix is to reverse the list in Python before building the context, except the first attempt changed the SQL to sort oldest-first *and* added the Python-side reverse. Confirmed by literally asking the model to recite the conversation back in order and it gave the order correctly, 1 through 4.

None of these three would show up in a five-minute demo. Two of them only show up once there's enough data or enough history for the wrong behavior to matter. It is exactly the kind of bug that's cheap to fix now and expensive to debug later, in production, with a confused conversation to untangle.

## What's next

Backend and database talk to each other, and the backend talks to Claude Code. What's still missing is a way for a person to talk to any of it. Task 4 is the chat UI. No deadline on when that happens; it happens when it happens.

---

→ [Full build series](/series/sovereign-ai-nexus/) · [Project page](/projects/sovereign-ai-nexus/)
