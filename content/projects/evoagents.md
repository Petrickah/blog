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
