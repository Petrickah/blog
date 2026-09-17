---
title: "Gram Engine"
subtitle: "personal game engine — Rust + C++, built in the open"
date: 2026-09-17
weight: 20
featured: true
summary: "A personal game engine, built from rediscovered passion not portfolio pressure. No deadlines, structured in waves — each wave produces a working artifact and a devlog post."
repo: "https://github.com/Petrickah/gram-engine"
---

Gram Engine is a personal game engine (Rust + C++, Vulkan), started from rediscovered passion, not a portfolio obligation. Without a deadline and no stress. It is structured in "waves": each wave produces one working artifact plus a devlog post on this blog. Stay in touch to follow for more episodes from this series.

The name is provisional: Gram, the sword of Sigurd, following the same philosophy as Scimitar → Anvil at Ubisoft. If the engine grows enough, Gram becomes Hearth. If not, the name was always fine as a working title.

### Waves

| Wave | What it produces | Blog post |
|---|---|---|
| **Wave 0** — Gram Build | A pure-Rust CLI build tool that handles CMake (FetchContent, vcpkg) and Cargo projects. Self-hosting, cross-compilation, same-language module linking. | ✅ [Gram Build devlog](/posts/gram-engine-00-gram-build/) |
| **Wave 1** — Hello Triangle | A Vulkan window with a colored triangle — C++ owns the window and renders, Rust providing gameplay logic through a dynamically runtime build. This is subject to change. | 🚧 Next |
| **Wave 2** — Ray Tracer | Compute shader pipeline, spheres rendered from Rust entities. | 🔮 Planned |
| **Wave 3+** | Raster pipeline, post-processing, asset manager, world serialization. Everything that makes a game engine tick. | 🔮 Noted, unscheduled |

### Technical stack

- **CLI**: Rust, pure binary (no runtime deps), its just the `gram` CLI tool, for now.
- **Engine core**: C++17, Vulkan SDK, GLFW. The core libraries for a game engine.
- **Gameplay layer**: Rust, `bevy_ecs` standalone runtime.
- **Build system**: `gram build` orchestrates CMake + Cargo underneath.
- **CI/CD**: Jenkins / GitHub Actions, multi-platform (Linux + Windows + macOS), undecided.
- **Format**: RON (Rusty Object Notation) for build definitions and later asset definitions.

### The unexpected outcome

What started as "a build tool for the engine" became a universal build tool usable for any C++ or Rust project. The same `gram` CLI that compiles the engine's Vulkan renderer could also handle my standalone socket-programming practice project (`cpp-socket-chat`), a POSIX IRC chat server that has nothing to do with game development. This wasn't planned... but it happened because I kept solving the next real problem instead of staying inside the original scope.

→ [Full build series](/series/gram-engine/)
