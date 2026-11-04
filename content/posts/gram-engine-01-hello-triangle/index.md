---
title: "Gram Engine - Episode 1: Hello Triangle"
date: 2026-11-04
draft: false
series: ["gram-engine"]
tags: [game-engine, vulkan, cplusplus, rust, gram-build, imgui, ecs, cross-platform, moltenvk, blog-series]
summary: "Wave 1 of Gram Engine in two halves: a Vulkan 1.3 triangle running on Windows, Linux and macOS with an ImGui editor, and a Rust gameplay layer that reloads while the game runs, just a stateless cdylib, generational IDs, components generated from .ron schemas, and runtime-checked borrows across the FFI boundary."
---

In Episode 0 I built a build tool. A good one which grew from a Hello World compiler into something that rebuilds itself, handles C++ and Rust projects, cross-compiles for three platforms and manages dependencies.

But a build tool is not a game engine. After Wave 0 shipped, I still had exactly zero things on a screen.

Episode 1 fixes that. It has two halves, and they are very different kinds of work:

- **Chapter 1 is the C++ half.** Vulkan, a window, a triangle, three operating systems. It is visual, it is satisfying, and it is full of bugs you can see.
- **Chapter 2 is the Rust half.** No pixels at all, just a shared library, an ID table, and the plumbing that lets gameplay code live in a language that can be recompiled while the game is running.

One half you can show someone. The other half is what makes the engine worth building.

---

## Chapter 1 - The C++ side: getting a triangle on screen

### The goal, and why it is harder than it sounds

Open a window, draw a triangle. Every Vulkan tutorial starts here, and every one of them is about a thousand lines of setup before anything appears.

Vulkan is explicit on purpose. It does not guess what you want. You tell it which GPU to use, how many frames to keep in flight, how to hand images to the screen, and what to do when the window changes size. In exchange you get control that OpenGL never gave you, and a stack trace for every mistake.

I wrote this part myself, step by step, with code review between each step. That turned out to matter, because most of the bugs were not Vulkan bugs. They were ordinary C++ bugs wearing a Vulkan costume.

### Building it in pieces

The first version was one file. By the third day `VulkanRenderer.cpp` was 511 lines long and still had no triangle on screen, it was a clear signal to split it up.

The split is one class per Vulkan resource, and each class follows one rule: **if my dependencies are not ready, I stay invalid instead of crashing.**

```
VulkanInstance → VulkanSurface → VulkanDevice → VulkanSwapchain
                                              → VulkanShader
                                              → VulkanPipeline
                                              → VulkanFrame
```

That `IsValid()` convention sounds like a small thing. It is the difference between "the app crashed somewhere in a 500-line file" and "the swapchain says it could not create itself, here is why."

### Three bugs that were really one bug

While refactoring, three separate crashes had the same root cause: **a reference pointing at something that had already been destroyed.**

1. **A set of pointers pretending to be strings.** I kept device extension names in a `std::set<const char*>`. That compares memory addresses, not text, and the pointers pointed into local vectors that no longer existed. Fix: `std::vector<std::string>`, with `const char*` views created when needed.

2. **A shader destroyed by a comma.** I created a `VulkanShader` inside an `if` condition and then put it into a vector with `{a, b}`. The `initializer_list` copies through a temporary, and the temporary's destructor destroyed the Vulkan handles. That one produced `VulkanShader` as move-only, `vk::UniqueShaderModule`, and a rule I now follow everywhere.

3. **A `const vk::Device&` bound to a local.** Vulkan handles are small values. Copy them. Pointing at them is asking for trouble.

The lesson stuck with me for the rest of the project: **in C++, a reference is a promise that something else will stay alive. Most of my bugs were promises I could not keep.**

### The magenta screen

Shaders compile from HLSL to SPIR-V with `dxc`. On Linux I tried building DXC from source and hit a missing backend; then I moved to macOS and discovered the Vulkan SDK ships `dxc` on every platform. One file, two entry points, compiled at build time. Done.

The first frame was bright magenta: the classic "something is very wrong" color. Three problems stacked on top of each other:

- the command buffer was submitted **before** recording ended,
- the same fence was used for acquire and submit,
- one `renderFinished` semaphore was shared across all images.

Fix all three and:

> **19 October, commit `5ac1f41`: "I have the triangle, point up and colored."**

That is the moment the project stopped being an abstraction.

### Three platforms, three drivers

The triangle renders on:

- **Windows**: natively, on an RTX 5060 Ti, from a `.exe` cross-compiled on a Mac,
- **Linux**: WSL2, on `llvmpipe`, which means the CPU is doing the graphics work,
- **macOS**: MoltenVK on an M4 Pro.

Getting there was mostly about accepting that each platform has its own personality:

- **macOS needed MoltenVK's portability extensions** (`VK_KHR_portability_enumeration`, `VK_KHR_portability_subset`), and it has no geometry shader stage at all. Instead of `#ifdef` scattered everywhere, the code has capability macros: `GRAM_PLATFORM_APPLE`, `GRAM_GEOMETRY_SHADERS`.
- **Windows had two GPUs**: an Intel UHD 770 and the RTX, but my device scoring was hiding one of them. Fixing the score also fixed a `uint32_t` underflow.
- **WSL had a lie for an executable path.** `argv[0]` was just `GramEngine.exe`, so shaders could not be found. Fix: a real `GetExecutableDirectory()` per platform.
- **Resizing and minimizing** broke the swapchain. `ErrorOutOfDateKHR` on resize, an assert on minimize. The fix was a proper `Recreate()` path and treating a 0×0 window as "try again later."

The workflow ended up reversed from what I expected: **develop on macOS, cross-compile the Windows executable there, test it natively on the PC.** MoltenVK is a subset of Vulkan, so what works on the Mac usually works everywhere.

### Beyond the triangle: the tools that make the next wave possible

A triangle alone would have been a short article. What made this half of Wave 1 worthwhile was everything around it:

- **A logger** built on spdlog, with check macros that read like assertions (`GramCheck(x)` means "I expect x to be true"). This one had a spectacular bug: my error macro returned `false` on success too, so fences were never created and nothing rendered. The fix was separating logging from control flow, which is a distinction I now understand in my bones.
- **An ImGui overlay** with docking and multi-viewport. It gives me an inspector, a systems panel, and a place to put debug buttons without writing UI code for each one.
- **A layer system**: `Layer<Owner>` / `LayerOwner<Owner>`, one layer per type, started in registration order and stopped in reverse. It is how the renderer, the ImGui backend and the game's own UI coexist without knowing about each other.
- **Frames in flight**, so the GPU is never waiting for the CPU to finish a frame. Four objects leaked at shutdown because I used `reserve` where I needed `resize`, just a one-word bug that took an afternoon.

At the end of Chapter 1, the C++ side had a working window, a triangle, an editor overlay and a clean shutdown on three platforms.

What it did not have was gameplay.

---

## Chapter 2 - The Rust side: gameplay that reloads

### The question that took three tries

I wanted gameplay logic in Rust. Not because Rust is fashionable, but because recompiling a game to change one number is a terrible way to work. I wanted the same thing Unity and Unreal give you: edit the logic, see the change.

That means hot reload. And hot reload across a language boundary is genuinely hard, because the moment you unload a library, everything that pointed into it becomes poison.

I went through three designs:

| When | The plan | Why it did not survive |
|---|---|---|
| September | Rust owns `main()`, C++ is a static library | Inverts the engine; the renderer should not be a guest in the gameplay runtime |
| Late September | A `bevy_ecs` world in a static Rust crate, systems in a reloaded `cdylib` | `TypeId`s drift, and any surviving data pointing into the unloaded library crashes on drop |
| **Adopted 28 October** | **C++ owns everything. Rust is a stateless `cdylib`.** | This one stuck |

The final idea is one sentence: **all state lives in C++; the reloadable library holds only logic.**

It is the "state in the host, code in the DLL" pattern from Handmade Hero, just across a language boundary instead of inside one C++ program. Nothing in surviving memory points into the Rust library, because Rust stores nothing. When the library unloads, it takes nothing with it.

### Two tables and one symbol

The library exports exactly one symbol: `game_get_api()`. Everything else goes through two tables of function pointers.

**C++ fills `HostAPI`**, represents what the engine offers to the game:

```cpp
struct HostAPI {
    void* Host;                                   // C++ hands Rust its own "this"
    void (*Log)(LogLevel, const char*);
    void (*RegisterSystem)(void* host, const System::Descriptor*);
    void* (*GetComponent)(void* host, ObjectID, ComponentID);
};
```

**Rust fills `GameAPI`**, represent what the game offers to the engine:

```rust
#[repr(C)]
pub struct GameAPI {
    pub version: u32,             // checked before anything else
    pub on_load: extern "C" fn(*const HostAPI) -> *const GameAPI,
    pub on_unload: extern "C" fn(),
    pub run_system: extern "C" fn(index: u32, ctx: *mut Context),
}
```

The important bit is what is **not** there: no game-specific function names. `GameAPI` is the same for every game and never grows. The engine does not need to know that `greet` or `spin` exist.

### Reloading without crashing

The loader is an Application layer, and it does the same five things every time:

1. Copy `libGameLogic.dylib` to `hot/libGameLogic_<N>.dylib`.
2. Load **the copy**, never the original.
3. Find `game_get_api`.
4. Check the version.
5. Call `on_load`.

Every part of that is a scar from a real failure:

- **Copy-on-load** because Windows locks a loaded DLL, so the build cannot overwrite it, and on macOS, writing over a mapped library can crash the process.
- **A new name on every load** because macOS often does not actually unload a Rust dylib. `dlopen` on a path that is already in memory hands you the old image, with old statics.
- **Atomic artifacts**: `gram build` writes `<name>.partial` and renames it over the old file. The watcher never sees a half-written library, and macOS does not kill a running process whose executable was rewritten in place.
- **Automatic reload**: every 0.5 s the loader compares the file's write time with the one it last loaded. If they differ, the game reloads itself. No button needed, but now there is one too.

And panics never cross the boundary. Every exported function wraps its body in `catch_unwind`, and the panic hook logs `file:line:col: message` through the engine's logger. A system that panics logs a line, gets skipped that frame, and the game keeps running.

### The ECS: entities that never alias

Now the part I was most curious about.

An ECS (entity-component-system) sounds abstract until you build one. The idea is simple: an **entity** is just an ID. A **component** is plain data attached to an entity. A **system** is a function that reads and writes components.

No MonoBehaviour. No `Update()` method on every object. Just data in memory and functions that walk it.

The C++ `World` does the storage:

- **An `ObjectID` is an index plus a generation.** When an entity dies, its slot goes on a free list, and the generation increments. A stale ID is detected instead of silently pointing at a new entity. This one detail prevents an entire category of "I deleted it and it came back" bugs.
- **Components are stored per type**, packed in a contiguous array, with an owner table to map entity → slot. Destroying an entity swaps the last element into its place.
- **A component's address is not stable.** The array moves when it grows, which is why Rust only ever holds a pointer for the duration of one call.

### Components described once

Here is the part that feels like magic the first time you watch it work.

A component is described in a `.ron` file:

```ron
Component(
    name: "Greeting",
    fields: [
        Field(name: "text", ty: Str(64)),
        Field(name: "scale", ty: F32),
    ],
)
```

`gram build` runs a generator over the whole project before compiling. From that one definition it writes:

- a Rust `#[repr(C)]` struct, with compile-time asserts on size and field offsets,
- a matching C++ struct, with `static_assert`s,
- a descriptor table: names, types, offsets, sizes.

Two languages, one source of truth, and the compilers check each other. If the layouts disagree, the build fails, but not the game, at runtime, three hours later.

It also means **the inspector is generic**. It does not know what a `Greeting` is. It walks the descriptor table and draws a widget per field. Add a field to the schema, rebuild and restart, and it appears in the inspector. Without writing any C++: the generated header brings the new descriptor, and the inspector only knows how to draw field types. A reload alone isn't enough: a schema change alters the data's layout, so it needs a restart.

That is the same idea as Anvil's `.mold` files at Ubisoft, and it is the first time in this project that I have built something that felt like real engine architecture rather than a tutorial with extra steps.

### Query, and the borrow checker's blind spot

Gameplay code should not need `unsafe`, raw pointers, or `extern "C"`. It looks like this:

```rust
pub(crate) fn greet1(target: EventTarget, greetings: Query<Greeting>) {
    let Some(entity) = *target else { return };

    if let Some(greeting) = greetings.get(entity) {
        info!("Greetings from Rust: {}!", greeting.text.as_str());
    }
    if let Some(mut greeting) = greetings.get_mut(entity) {
        greeting.text.set("Hello world from Rust");
    }
}
```

But there is a problem Rust's compiler cannot see. Two `ObjectID`s could name the same component. The borrow checker only knows about Rust references and it has no idea that two integers point at the same C++ memory.

So the check happens at runtime, using the same rules `RefCell` uses:

- A `thread_local!` list tracks active borrows.
- Two reads are fine. A write conflicts with anything on the same entity and component.
- Different entities never conflict, which is what lets you swap a value between two entities.
- The guard releases on `Drop`, including during a panic unwind.

The guard is taken **before** the reference exists, so two references to the same memory never exist at the same time.

This is the kind of design that looks obvious in hindsight and is not obvious at all while you are designing it. It is also the part of the Rust code I am proudest of.

### Systems, and the macro that writes the boring part

A system is an ordinary Rust function. The game lists them in one place:

```rust
export_game! {
    events: { "greet" => [greeter::greet1, greeter::greet2] },
    update: [tick],
}
```

That macro expands into the `GameAPI` table, the registration calls, the dispatcher, and `game_get_api` with every one of them wrapped in the panic guard. The gameplay code stays plain Rust.

Behind the scenes, C++ owns the registry and the schedule. On `on_load`, Rust sends one descriptor per system (name, stage, event, index). Every frame, C++ walks the update systems and then dispatches any queued events. The "Greet" button in the inspector does not call Rust, it **emits an event**, and whoever subscribed to it runs.

That distinction matters more than it sounds. The UI does not know what gameplay exists. It just emits `"greet"` and something, someday, might listen.

### What it looks like when it works

The proof of concept is deliberately unglamorous:

1. The editor shows an entity with a `Greeting` component: one text field and a number.
2. You type something in the inspector.
3. You change a log message in Rust and rebuild.
4. The game reloads by itself with no restart, and the new logic runs.
5. The text you typed is still there.

That sequence is the whole point of Wave 1. Everything in Chapter 2 exists to make step 5 true.

### Bugs from the Rust half

The mistakes here were a different species, less "temporary lifetime" and more "the compiler and the runtime disagree about what just happened":

- **A missing field in a designated initializer is silently zeroed.** Twice. Once it put a null function pointer in `HostAPI` and aborted the load. The second time it left `EventTarget` out of the frame context, so update systems saw entity `{0, 0}` as their target, which is a live entity. The fix was explicit `InvalidObjectID` plus a debug print that made it visible.
- **Layout arithmetic.** My first generator used a field's *size* as the next field's offset, and started the struct alignment at 0. A unit test caught it. Now both compilers check the generator's output, so a mistake fails at build time.
- **`#[track_caller]` stops at closures.** The panic pointed inside `borrow.rs` instead of the game's code. Fix: compute the conflict inside the closure, panic outside it.
- **`Drop` has to find its own borrow, not a conflicting one.** Searching with the conflict condition could remove a different borrow entirely.
- **`let _ = guard` drops immediately. `let _borrow = guard` keeps it alive.** One character is the difference between having protection and having none.
- **An ImGui layer that returns `false` skips every layer after it.** A panel returned its "open" state, so closing it also removed the panels drawn after it.
- **A macro must not lean on the caller's imports.** `export_game!` only compiled because the prelude happened to glob-import the trait it used. Fixing the prelude would have broken every game. Now everything goes through `$crate::`.

Each of those cost real time. Most of them are now covered by 23 unit tests in `gram-core` and 7 command-level tests for the generator.

---

## Where Wave 1 stands

The C++ half is done: a Vulkan 1.3 renderer on three platforms, shaders compiled at build time, a docking ImGui editor with an outliner, an inspector and a systems panel, a logger, and a layer system.

The Rust half is done and working: a stateless `cdylib`, automatic reload, panics contained at the boundary, a generational-ID ECS, components generated from schemas, runtime-checked borrows, systems with real parameter types, and events.

What is deliberately **not** done yet:

- **Iterating a component** (`Query::iter`): it needs a new host function and a version bump. Wave 2 uses it when Rust starts moving spheres.
- **Typed access from C++**: today C++ reaches components through `void*` and a `ComponentID`.
- **System ordering inside a stage**: registration order for now.
- **More schema field types**: `Vec3` first.

## What's next

**Wave 2 is the ray tracer.** A compute shader pipeline, spheres first owned by C++, then driven from Rust entities. That is the first time gameplay logic will actually move something visible on screen, and the first real test of whether the architecture from Chapter 2 holds up.

I am looking forward to it. The plumbing is done. Now I get to make something move.

---

Two chapters, one wave. One half is pixels and platforms and the particular joy of seeing a triangle appear. The other half is contracts, IDs and the quiet satisfaction of changing code in a running game.

Neither half works without the other. That is what an engine is, I think: it's not a renderer, not an editor, but the agreement between them.
