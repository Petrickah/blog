---
title: "EvoAgents"
subtitle: "bachelor's thesis"
date: 2021-10-12
weight: 20
featured: true
summary: "AI framework using behavior trees for NPC decision-making — an action-adventure game with procedurally generated terrain, built as a bachelor's thesis."
repo: "https://github.com/Petrickah/EvoAgents"
---

EvoAgents ("Rabbit Catcher") is a video game built for my Bachelor's thesis, centered on an asynchronous Behavior Tree implementation for NPC AI.

## The AI algorithm

The core of the thesis is an asynchronous Behavior Tree implementation, built on top of UniTask. The specific problem it tackles is evaluating a tree whose action nodes are themselves asynchronous — rather than blocking evaluation on each node's completion, the tree walks and resolves branches concurrently, matching how real gameplay logic (animations, timers, pathing) actually behaves.

## The game

The world is procedurally generated using Perlin Noise combined with mesh manipulation — voxel-style terrain, built at runtime rather than hand-authored. Rabbits and wolves populate this world, both driven by the same Behavior Tree algorithm: the player's goal is to catch every rabbit before the wolves do. Losing a rabbit to a wolf ends the run.

## Pursue, evade, and a global alarm

Rabbits and wolves both move on Unity's NavMesh, but pure NavMesh pathing (walk to point, arrive) isn't enough to make a chase feel reactive — so each species layers a Craig Reynolds-style steering behavior on top of it. Wolves run **Pursue**: extrapolate a target's future position from its current velocity (`enemy.transform.position + enemy.velocity * lookahead`), then steer toward that predicted point rather than the target's current position. Rabbits run the mirror image, **Evade**: extrapolate the same way, then steer away. In both cases the steering vector (desired velocity minus current velocity) is applied as an additive force on top of whatever destination NavMesh is already walking toward, via `ApplyForce`.

The interesting part isn't the steering itself — it's how a rabbit finds out there's a wolf to evade in the first place. Detection isn't purely local: a rabbit that spots a wolf within its own `Awareness` radius broadcasts an `Enemy = true` message through a `Mediator` (Mediator pattern, decoupling sender from receivers), and `Mediator.BroadcastMessage` loops over *every* subscribed rabbit unconditionally — no distance check at all. So the alert itself is global: every rabbit "hears" it at the same instant, regardless of where the wolf actually is. What keeps this from looking like every rabbit in the world bolting at once is a second, independent gate: the actual evasion steering only produces a non-zero vector if that specific rabbit's *own* proximity check finds a wolf nearby — if it doesn't, `Enemy` quietly resets itself back to `false` on that rabbit, and nothing visibly happens.

The result isn't Boids (there's no separation, alignment, or cohesion between rabbits — none of them react to each other at all) — it's closer to a global alarm flag gated by a local reaction check, which happens to look locally plausible from the outside without actually being local underneath.

## A bug from back then, finally found

At the time, there was a bug where a caught rabbit's death animation would play correctly (the animation state machine reached and stayed in `Dead`), but the rabbit could still keep moving. I remembered the symptom but never tracked down the cause — the code just sat there for years. Revisiting the actual source made it obvious: cancellation of the tree's `CancellationToken` was implemented (a `CancellationTokenSource` created per tree run, cancelled on death), but the `Parallel` composite never propagated it to its children — every other composite (`Sequencer`, `Selector`, `RepeatForever`, and friends) explicitly calls `SetToken` on each child before awaiting it; `Parallel` was the one place that didn't. The movement branch (`Wander`/`ApplyForce`) happened to live inside a `Parallel` node, so it kept running on a token that could never be cancelled — while the animation code had an independent `animation.IsDead` escape hatch the movement code didn't, which is why only one of the two actually stopped.

Separately, `Parallel` also always returned `Success` regardless of its children's outcomes — a `UniTask.WhenAll` with no policy layered on top. Real behavior-tree implementations define `Parallel`'s result from an explicit success/failure policy (succeed when any child succeeds vs. when all do, and the equivalent for failure) — `WhenAll` is just the "wait for everyone" primitive underneath that, not a policy by itself. At the time, this wasn't a deliberate design choice, just an incomplete understanding of what the node was supposed to do.
