---
title: "EvoAgents"
subtitle: "bachelor's thesis"
date: 2021-10-12
featured: true
summary: "AI framework using behavior trees for NPC decision-making — an action-adventure game with procedurally generated terrain, built as a bachelor's thesis."
repo: "https://github.com/Petrickah/EvoAgents"
---

EvoAgents ("Rabbit Catcher") is a video game built for my Bachelor's thesis, centered on an asynchronous Behavior Tree implementation for NPC AI.

## The AI algorithm

The core of the thesis is an asynchronous Behavior Tree implementation, built on top of UniTask. The specific problem it tackles is evaluating a tree whose action nodes are themselves asynchronous — rather than blocking evaluation on each node's completion, the tree walks and resolves branches concurrently, matching how real gameplay logic (animations, timers, pathing) actually behaves.

## The game

The world is procedurally generated using Perlin Noise combined with mesh manipulation — voxel-style terrain, built at runtime rather than hand-authored. Rabbits and wolves populate this world, both driven by the same Behavior Tree algorithm: the player's goal is to catch every rabbit before the wolves do. Losing a rabbit to a wolf ends the run.

## A bug from back then, finally found

At the time, there was a bug where a caught rabbit's death animation would play correctly (the animation state machine reached and stayed in `Dead`), but the rabbit could still keep moving. I remembered the symptom but never tracked down the cause — the code just sat there for years. Revisiting the actual source made it obvious: cancellation of the tree's `CancellationToken` was implemented (a `CancellationTokenSource` created per tree run, cancelled on death), but the `Parallel` composite never propagated it to its children — every other composite (`Sequencer`, `Selector`, `RepeatForever`, and friends) explicitly calls `SetToken` on each child before awaiting it; `Parallel` was the one place that didn't. The movement branch (`Wander`/`ApplyForce`) happened to live inside a `Parallel` node, so it kept running on a token that could never be cancelled — while the animation code had an independent `animation.IsDead` escape hatch the movement code didn't, which is why only one of the two actually stopped.

Separately, `Parallel` also always returned `Success` regardless of its children's outcomes — a `UniTask.WhenAll` with no policy layered on top. Real behavior-tree implementations define `Parallel`'s result from an explicit success/failure policy (succeed when any child succeeds vs. when all do, and the equivalent for failure) — `WhenAll` is just the "wait for everyone" primitive underneath that, not a policy by itself. At the time, this wasn't a deliberate design choice, just an incomplete understanding of what the node was supposed to do.
