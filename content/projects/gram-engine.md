---
title: "Gram Engine"
subtitle: "personal game engine — C++ and Rust, built in the open"
date: 2026-09-17
lastmod: 2026-11-04
weight: 20
featured: true
summary: "A personal game engine in C++ and Rust. Wave 0 built a self-hosting `gram` build tool; Wave 1 put a Vulkan 1.3 triangle on Windows, Linux and macOS and added a Rust gameplay layer that hot-reloads while the game runs — stateless cdylib, generational IDs, schema-generated components."
repo: "https://github.com/Petrickah/gram-engine"
---

Gram Engine is a personal game engine (C++ and Rust, Vulkan), started from rediscovered passion rather than a portfolio obligation. No deadline, no stress. It is structured in **waves**: each wave produces one working artifact plus a devlog post on this blog.

The name is provisional: Gram, the sword of Sigurd, following the same philosophy as Scimitar → Anvil at Ubisoft. If the engine grows enough, Gram becomes Hearth. If not, the name was always fine as a working title.

## Waves

| Wave | What it produces | Devlog |
|---|---|---|
| **Wave 0** — Gram Build | A pure-Rust CLI build tool that orchestrates Cargo, multi-file CMake (FetchContent, vcpkg) and nested Gram projects. Self-hosting, cross-compilation, dependency management from a single `.ron` file. | ✅ [Gram Build](/posts/gram-engine-00-gram-build/) |
| **Wave 1** — Hello Triangle | A Vulkan 1.3 triangle on Windows, Linux and macOS, with a docking ImGui editor, an spdlog logger and a layer system — plus a Rust gameplay layer that reloads while the game runs: stateless `cdylib`, generational IDs, components generated from `.ron` schemas, runtime-checked borrows across FFI. | ✅ [Hello Triangle](/posts/gram-engine-01-hello-triangle/) |
| **Wave 2** — Ray Tracer | A Vulkan compute pipeline with spheres: first owned by C++, then driven from Rust entities. | 🔮 Next |
| **Wave 3+** | Raster pipeline, post-processing, asset manager, world serialization. Everything that makes a game engine tick. | 🔮 Noted, unscheduled |

## How it fits together

**C++ owns the state; Rust owns the logic.** The engine is a static C++ library holding the renderer, the ECS world and every entity. Gameplay is a stateless Rust `cdylib` that the executable loads and reloads: it keeps no game data between calls, reaches components through IDs, and gets a table of host functions instead of linking against C++. Recompile the Rust code and the game picks it up without restarting; the data stays where it was.

- **Renderer** — C++20, Vulkan 1.3 (dynamic rendering, two frames in flight), GLFW, MoltenVK on macOS. HLSL shaders compiled to SPIR-V at build time.
- **World** — a C++ ECS with generational entity IDs and packed per-type component storage. Components are described once in `.ron` schemas; `gram build` generates the C++ struct, the Rust struct and a descriptor table, and both compilers verify the layout.
- **Gameplay** — Rust systems registered into a C++-owned schedule, with events, a `Query` API and runtime borrow checks where the Rust borrow checker can't see (two IDs can name the same C++ memory).
- **Editor** — ImGui panels shared by every game: outliner, inspector drawn from component descriptors, and a systems panel with reload, timing and per-system enable.
- **Build** — `gram build` orchestrates cargo, cmake and nested projects, and builds the whole repository, itself included.

## The unexpected outcome

Wave 0 was supposed to be a build tool for this engine only. It became a general tool: the same `gram` CLI that compiles the Vulkan renderer can build any C++ or Rust project — including my standalone socket-programming practice project (`cpp-socket-chat`), a POSIX IRC chat server that has nothing to do with game development. That wasn't planned; it happened because I kept solving the next real problem instead of staying inside the original scope.

→ [Full build series](/series/gram-engine/)
