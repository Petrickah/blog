---
title: "Gram Engine — Episode 0: Gram Build"
date: 2026-09-16
draft: false
tags: [game-engine, vulkan, cplusplus, rust, gram-build, cmake, vcpkg, fetchcontent, ron-format, passion-project, blog-series]
summary: "Wave 0 of Gram Engine started as a simple build CLI and grew into a universal build tool for C++ (CMake, FetchContent, vcpkg) and Rust (Cargo) projects — self-hosting, cross-compilation, module cross-linking, all from a single .ron definition. The first step before writing any rendering code, now usable for any project."
---

Every game engine starts somewhere. Most start with a window, a triangle, and a dream. I started with a build tool.

It sounds backwards until you think about it: a game engine is a system for turning source code into something that runs on a screen. Before you write the renderer, before you design the ECS, before you even open a window — you need to know how you're going to build it. What compiler flags matter. How the C++ and Rust code link together. Where the binary ends up when Jenkins builds it on three platforms at once.

But somewhere along the way, that build tool outgrew its original purpose. Before I wrote a single line of rendering code, Gram Build became a tool I can use for any C++ or Rust project. This is the story of how that happened, one iteration at a time.

### About this article

This article has its own small story. I started a draft for it weeks ago, after Task 0.4, then I built self-hosting, then I added CMake modules, FetchContent, vcpkg, module references, `gram run`. Each time, the article was waiting, the tool had changed again by the time I sat down to write. The draft became a mix of old and new, and I kept getting tripped up by which version of Gram I was describing.

So before writing this, I had Claude Code produce a chronological history document: a single, linear account of Wave 0 from the first `todo!()` stub to where it stands today. Every command in this article was cross-checked against that document, so the tool I'm describing matches the tool that actually exists on disk.

### The name

Gram, the sword of Sigurd, is following the same philosophy as Scimitar → Anvil at Ubisoft, where codenames start descriptive and get replaced when the thing earns its real name. If the engine grows enough, Gram becomes Hearth. If not, it was always fine as a working title.

Either way: the first thing Gram needed was a tool that knows how to build itself, or so I thought.

### What Gram Build does now

A CLI, grown across six tasks and several unplanned iterations:

```
gram init <name> [--lang cargo|cmake] [--kind runtime|library]
gram build [--path <dir>] [--ci] [--target <t>]
gram add [<dep>] [--module <m>] [--lang ..] [--kind ..] [--url .. --tag ..] [--vcpkg] [--module-ref]
gram remove [<dep>] [--module <m>] [--purge]
gram run [--module <m>] [--target ..] [-- <arguments>]
```

`gram init` creates a project directory with a `Gram.ron` definition file and the scaffolding for your first module. For CMake modules: `kind: runtime` gives you `src/main.cpp` with a `CMakeLists.txt`, `kind: library` gives you `src/` + `include/<name>/` for headers. For Cargo modules it generates the `Cargo.toml` and a `src/main.rs` or `src/lib.rs`.

`gram build` reads the `.ron` file, invokes the right build system (`cmake -S -B` for CMake modules, `cargo build` for Cargo modules), and puts the binary in `build/<project>/<target>/<bin>`. One target, one build, zero ceremony. `--ci` iterates over all declared targets and places artifacts in a standard layout located at `build/<project>_<version>_<target>/<binary>`.

`gram add` creates modules or adds dependencies. Two paths for CMake: FetchContent (`--url`/`--tag`) for repos with their own `CMakeLists.txt`, or vcpkg manifest mode (`--vcpkg`) for libraries with complex builds where someone already wrote a port. `--module-ref` links one Gram module to another (same language only — cargo↔cargo via `cargo add --path`, cmake↔cmake via `add_subdirectory()`), with automatic `target_link_libraries` since Gram generated both CMake targets and knows their names.

`gram remove` deletes a dependency from a module, or the whole module with `--purge`. Non-destructive by default — accidental `remove` only touches the `.ron` file, not your source on disk.

`gram run` executes the already-compiled binary of a runtime module. Arguments after `--` pass through untouched. No `--ci` variant: `gram run` is for you, the developer, not the pipeline.

### The evolution (three acts, plus a prologue)

#### Act 0: the skeleton that did nothing

The first commit was almost disappointing. A Rust binary with `clap` derive, two subcommands (`init` and `build`), both stubs (`todo!()`). Nothing worked because the entire point was that `gram --help` printed something that looked right.

It mattered more than it sounds. Having a CLI skeleton that parsed correctly meant every subsequent task started from a known-shape foundation: I knew exactly where each subcommand's handler lived, what arguments it received, and how `Gram.ron` would eventually be threaded through. Getting the shape right before any real logic existed is the kind of discipline that prevents a project from being blocked by analysis paralysis. I had something that didn't work yet, but I knew what it would look like when it did.

That shape, by the way, has stayed stable across the entire evolution. The subcommands today are the same subcommands from that first commit, they are just implemented.

#### Act I: single-file, direct compilation

The first version that actually did something was simple: `gram init hello-world --lang cpp` created a single `src/main.cpp` and a `Gram.ron`, and `gram build` invoked `g++` directly on that one file. Same for Rust, via `rustc`.

It worked. It compiled Hello World in two languages, for Linux and Windows (via `x86_64-w64-mingw32-g++` and `rustc --target x86_64-pc-windows-gnu`). The Windows binaries ran under Wine. But it was limited: one file, no dependencies, no project structure. Fine for a proof of concept, useless for a real project.

#### Act II: eating your own dog food — `lang: "cargo"` and self-hosting (2026-09-09)

The project note called Wave 0 "a build tool that knows how to build itself" but I realized it wasn't true yet. `gram` was still compiled with plain `cargo build`, never with `gram build` itself.

To fix that, I added `lang: "cargo"` which is a module type that delegates to real Cargo instead of reimplementing dependency resolution. A `cargo` module points `src` at a `Cargo.toml`, and `gram build` runs `cargo build --manifest-path <src>`.

Then I moved `gram`'s own source into `gram-engine/gram/`, wrote a `Gram.ron` at the repo root declaring it as a single `cargo` module, and ran `gram build`. It compiled. Then `gram build --ci` cross-compiled for both Linux and Windows. The Windows `.exe` ran under Wine.

Three bugs found and fixed along the way:
1. `gram init --git` was initializing git in the caller's working directory, not the new project.
2. `cargo init` without `--edition` defaulted to 2015, where `use` without `extern crate` doesn't compile. This looked like it missed a dependency, classic misdiagnosis bait.
3. A `std::env::set_current_dir` in a helper function was changing the global process `cwd` permanently, producing a doubled project directory (`hello-world/hello-world/`) because a later path computation used the wrong base.

The third bug taught me the most: I had consciously chosen `--path` to do `chdir` at entry precisely to avoid threading paths through every function. Then a helper function inside `build` did the same `chdir` again, and the two collided. The design decision was sound but the mistake was applying the same pattern *nested*, inside a function that wasn't the entry point.

#### Act III: real C++ projects — `lang: "cmake"`, FetchContent, vcpkg (2026-09-16)

Wave 1 needs real C++ modules like Vulkan, GLFW, and multi-file projects. A single-file `g++` invocation wasn't going to cut it. The obvious question: do I wait until Wave 1 to solve this, or do I solve it now in Gram Build, since it's pure scaffolding work (CMake setup, dependency wiring, those are explicitly "Claude Code writes" per my methodology)?

I solved it now by using two paths for CMake dependencies:

- **FetchContent** (default, `--url`/`--tag`): for libraries distributed as git repos with their own `CMakeLists.txt`. Verified with `olcPixelGameEngine` (javidx9's own single-file game engine implementation).
- **vcpkg manifest mode** (`--vcpkg`): for libraries with complex builds or system dependencies where someone already wrote a port. Verified with `fmt` (a common library for C++ pretty formatting and logging).

Both write the dependency resolution part into a managed, marker-delimited region of `CMakeLists.txt`. The actual `target_link_libraries` call stays manual. Here's what that looks like in practice after running `gram add --vcpkg fmt` on a module:

```cmake
cmake_minimum_required(VERSION 3.20)
project(main LANGUAGES CXX)

# ——— gram managed: dependencies ———
find_package(fmt CONFIG REQUIRED)
# ——— end gram managed ———

add_executable(main src/main.cpp)

# You write this line yourself:
target_link_libraries(main PRIVATE fmt::fmt)
```

**Why this stays manual:** a CMake package can export its targets under any name: `fmt::fmt`, `fmt::fmt-header-only`, or something entirely different depending on how the author wrote the `*Config.cmake` file. There's no standard field that says "this is the library target name." To guess it correctly, Gram would need to parse every package's CMake configuration at `add` time, which is a dependency-resolution engine's job. This is out of scope for Gram. Writing one line after the marker is the pragmatic trade-off: it keeps Gram simple, it keeps your `CMakeLists.txt` editable by hand, and it works for every package on the internet without Gram having to know anything about them.

On the same day, I added `gram run`, `--purge`, `--target` per module, and `--module-ref` for cross-linking same-language modules: cargo↔cargo and cmake↔cmake, both tested end-to-end with actual compilation and linking. The cmake↔cargo bridge (exactly what Wave 1 needs for `gram-core`/`gram-hot` + `cxx` + Corrosion) was deliberately left undone. That's the actual architectural heart of Wave 1, not something to generalize before there's a real use case to validate it against.

Four more bugs surfaced during this act:
1. `rm_dependency` was deleting the entire module every time, not just the dependency. It contradicted its own docstring.
2. `add_dependency` had the order inverted (checking the dependency before creating the module). It would have panicked on `gram add serde --module gram` in a single step.
3. `CMAKE_TOOLCHAIN_FILE` (needed for vcpkg) only applies on the *first* `cmake -S -B`. If a build directory is configured before `vcpkg.json` existed, it would be silently ignored by the toolchain. Fixed by adding `--fresh` to every `cmake -S -B` call, which is consistent with Gram Build's model (it regenerates `CMakeLists.txt` on every `add`/`remove` anyway).
4. `pkg-config` was missing from the VM. It is the real cause of a build failure that initially looked like a missing toolchain.

### How I worked

The methodology stayed consistent across all three acts: I write the logic where I'm learning something new (RON parsing, compiler invocation, the `init`/`add`/`remove` commands), and delegate the plumbing to Claude Code (CLI scaffolding with `clap`, `serde`/`ron-rs` integration, CMake FetchContent/vcpkg wiring). The rule is the first time I'm diving into some kind of code, I write it. When it becomes a second nature for the tenth time, I delegate.

Self-hosting and the CMake module push were both exceptions, it was entirely my initiative, triggered by realizing the project claimed something that wasn't yet true, or by seeing a problem that was blocking progress and deciding to solve it *now* rather than deferring it.

Total effort across Wave 0: about 8-10 hours of cumulative work across all tasks on multiple sessions.

### Seven bugs, seven lessons

Looking back at all seven real bugs (three from self-hosting, four from the CMake push), a pattern emerges:

- **The easy bugs look like dependency problems** (wrong edition, missing toolchain), but the actual fix is rarely about dependencies. The real root is usually a wrong assumption about what state a tool or process is in (a fresh config vs. a cached one, a first run vs. a repeated one, etc).
- **Global state is the enemy.** the `set_current_dir` already applied somewhere, the `select()` mutating the `fd_set` in place, the cached `CMAKE_TOOLCHAIN_FILE`... every time I assumed a piece of persistent state was safe to reach into from a helper, but I was wrong. The fix was always: don't touch global state from a helper; thread it explicitly.
- **Docstrings lie.**  `rm_dependency` said "removes a dependency" but the code removed the module. This was caused by copy-pasting code from a different source, written by me at an earlier time, or by someone else on the internet... even AI generated one. The fix wasn't to change the code to match the docstring, it was to align the code with what the function name promised.

### The unexpected outcome: a universal build tool

When I started Gram Build, I thought I was building a tool specifically for Gram Engine... Something that would know about the engine's modules, its build conventions, its quirks. But somewhere around act III, I realized it had become generic. The `gram init --lang cmake --kind runtime` gives you a `CMakeLists.txt` that builds on any Linux machine with `cmake` and any toolchain. The `gram add fmt --vcpkg` wires `find_package(fmt CONFIG REQUIRED)` into a managed section of your CMake but you manually have to link it into the final build. The `gram build --ci` cross-compiles for as many targets as you declare.

I can now use `gram build` for my socket-programming practice project (`cpp-socket-chat`), which has nothing to do with Gram Engine. It's a standalone C++ project with POSIX sockets and a `select()` event loop but I can convert it to a Gram Project and it will handle its own CMake scaffolding, dependency wiring, cross-compilation, and CI artifact layout.

A build tool built for a game engine, now building things that have never touched a game engine. That wasn't planned. It just happened because I kept solving the next real problem instead of staying inside the original scope. And this is the biggest advantage for a software engineer, the ability to think outside the box.

### What's next

Wave 0 is functionally complete. The tool exists, rebuilds itself, handles CMake and Cargo projects, links same-language modules, cross-compiles, runs binaries, and manages dependencies. It works for all sorts of C++ or Rust projects other than Gram Engine.

The next article starts Wave 1: a Vulkan window with a colored triangle, C++ owning the main game engine features, Rust providing gameplay logic through its own dynamically built runtime. And for the first time, the build tool that builds all of it was done by the same person building the engine.

---

The repo is private for now, but the articles are public. If building in the open resonates — Wave 1's article follows once a triangle actually renders on screen. Until then: `gram build`, run the binary, watch it print Hello World. Then watch it rebuild itself. Then realize you can use it for anything.
