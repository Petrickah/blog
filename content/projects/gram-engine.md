---
title: "Gram Engine"
subtitle: "personal game engine — C++ and Rust, built in the open"
date: 2026-09-17
lastmod: 2026-11-24
weight: 10
featured: true
summary: "A personal C++20 and Rust game engine on Vulkan 1.3. Wave 0 built a self-hosting build tool; Wave 1 delivered a cross-platform triangle and reloadable gameplay. Wave 2 is in progress: a compute-shader ray tracer with Rust-driven spheres, BVH, GPU profiling and FSR 1. Triangles and Blender scenes (.obj/.mtl) are next."
repo: "https://github.com/Petrickah/gram-engine"
repo_private: true
---

Gram Engine is a personal game engine (C++ and Rust, Vulkan), started from rediscovered passion rather than a portfolio obligation. No deadline, no stress. It is structured in **waves**: each wave produces one working artifact plus a devlog post on this blog.

The name is provisional: Gram, the sword of Sigurd, following the same philosophy as Scimitar → Anvil at Ubisoft. If the engine grows enough, Gram could become Hearth. If not, the name was always fine as a working title.

## Waves

| Wave | When | What it produces | Devlog |
|---|---|---|---|
| **Wave 0** — Gram Build | Sep 7 – Sep 17, 2026 | A self-hosting, pure-Rust build tool for C++ and Rust projects. | ✅ [Episode 0: Gram Build](/posts/gram-engine-00-gram-build/) |
| **Wave 1** — Hello Triangle | Sep 27 – Nov 10, 2026 | A Vulkan 1.3 triangle across three platforms, with an ImGui editor and reloadable Rust gameplay. | ✅ [Episode 1: Hello Triangle](/posts/gram-engine-01-hello-triangle/) |
| **Wave 2** — Ray Tracer | Since Nov 10, 2026 | **In progress.** *Ray Tracing in One Weekend* in a Vulkan compute shader; Rust-driven sphere entities; `.pass.ron` shader passes; SAH BVH; GPU profiler; FSR 1. Next: triangles and Blender scenes (`.obj`/`.mtl`). | [Interlude 1.5: Gram Build on Three Platforms](/posts/gram-engine-01-5-gram-build-three-platforms/) (prepares Wave 2) → [Episode 2: Ray Tracing in One Weekend on the GPU](/posts/gram-engine-02-ray-tracing-in-one-weekend-on-the-gpu/) · [Interlude 2.5: Optimizing for Real Hardware](/posts/gram-engine-02-5-optimizing-for-real-hardware/) · Episode 3 next |
| **Wave 3+** | — | Raster pipeline, post-processing, asset manager, world serialization. | 🔮 Noted, unscheduled |

A “.5” is an interlude that prepares the next full episode.

## How it fits together

**C++ owns the state; Rust owns the gameplay logic.** C++ holds the renderer and the `World`, including entity and component state. Rust gameplay is a stateless, reloadable `cdylib`; its systems move those C++-owned entities through the shared host interface. Render passes are described in `.pass.ron`; `gram` generates the matching C++ and shader definitions, while CMake runs `dxc` to compile HLSL. `gram build` builds Gram, the engine and the game, while `gram deploy` sends the project to configured devices, builds on-device where needed, and launches it.

- **Renderer** — C++20, Vulkan 1.3 and GLFW; HLSL compiles to SPIR-V with `dxc`. On macOS, MoltenVK is selected over KosmicKrisp.
- **World and gameplay** — C++ owns the `World` and entity/component state; Rust gameplay runs in a stateless, reloadable `cdylib`. Components are described in `.ron` schemas.
- **Editor and dependencies** — ImGui panels and spdlog logging; vcpkg supplies Vulkan, GLFW, GLM, ImGui and stb, while spdlog comes from FetchContent.
- **Build and deploy** — `gram` has Debug/Release/Final configurations and Apple clang, MSVC, GCC and MinGW toolchains. It generates Xcode and Visual Studio projects; `gram deploy` has been tested with a SteamOS handheld and a Windows device.
- **Platforms tried** — macOS (M4 Pro), Windows (MSVC/Visual Studio), and SteamOS (Legion Go S).

## The unexpected outcome

Wave 0 was supposed to be a build tool for this engine only. It became a general tool: the same `gram` CLI that compiles the Vulkan renderer can build any C++ or Rust project — including my standalone socket-programming practice project (`cpp-socket-chat`), a POSIX IRC chat server that has nothing to do with game development. That wasn't planned; it happened because I kept solving the next real problem instead of staying inside the original scope. A second surprise was `gram deploy`: it builds and launches on the Legion Go S running SteamOS, and was also tested with a Windows device.

→ [Full build series](/series/gram-engine/)
