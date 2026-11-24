---
title: "Gram Engine - Episode 1.5: Gram Build on Three Platforms"
date: 2026-11-24T10:00:00+02:00
draft: false
rssTeaser: true
series: ["gram-engine"]
tags: [game-engine, gram-build, build-system, cmake, rust, cplusplus, xcode, visual-studio, steamos, cross-platform, blog-series]
summary: "Gram Build grows from a single Debug build into a multi-platform workflow with Debug, Release and Final configurations, native toolchains, generated Xcode and Visual Studio projects, in-editor Play/Pause/Stop, and a real SteamOS test on a Legion Go S."
teaser: |
  To run the ray tracer on three platforms, Gram Build had to do more than pick a compiler. It needed three build modes with different jobs: Debug for development, Release for the game's own tools, and Final for a clean standalone run. It also needed the right compiler for each system.

  I wanted one IDE project that could hold both the engine's C++ and Rust code. Along the way, I typed a zero where the O belonged in one optimization setting, and Xcode couldn't find Cargo because it hadn't inherited Terminal's command path.

  The final test was on a Legion Go S running SteamOS. The game built and ran there too. The fan had its own review of the Debug build.

  The reason I tackled the build first was the ray tracer itself. It was the next engine project that needed to run beyond my Mac. Until then, Gram Build had only one Debug build. If I wanted to test the same renderer on Windows and Linux, the engine needed a build path that could travel with it.

  I gave the three builds different jobs. Debug kept the editor, logs and validation close while I worked. Release was optimized but kept the game's own test panels. Final ran without the editor and validation layers, like a clean standalone game. On Windows, it also opened without a console. Each mode had a different job in the same project.

  The compiler choice had to match the system too. I used Apple clang on the Mac, MSVC for a native Windows build, and GCC on Linux. From the Mac, MinGW could cross-compile for Windows. I kept the choice explicit: if I asked for MSVC and it was missing, Gram should tell me rather than quietly substituting another compiler. On the Mac, I could test that decision without having MSVC installed.

  One typo showed how easily a successful build can hide missing work. I meant the letter O in the link-time optimization setting, but wrote `LT0` with a zero. The build still finished. Cargo ignored the misspelled setting without a message, so it looked as if the optimization had been enabled. My first tests repeated the same typo because they copied the values from the code. I rewrote them to check the rule instead. A test should catch a mistake, not inherit it.

  The IDE project was the next bridge. The engine had C++ at its core and Rust for gameplay. I wanted both visible in one project, with a way to rebuild the Rust part and let the running game pick it up. The project tree could show files that were not compiled as C++, so I could navigate the whole engine without pretending it was one language.

  The first Xcode failure looked unhelpful. It worked from Terminal, but Xcode started from Finder and could not find Cargo. It had not inherited Terminal's command-search folders. Once Gram passed that environment into the generated project, Xcode could start the build. There was still a practical split: Xcode handled C++, while I attached VS Code for Rust debugging. Visual Studio could set Rust breakpoints directly.

  Windows brought a different obstacle. Visual Studio would not build a target while its debugger was running. The rebuild moved into the editor instead. Play rebuilt the gameplay library in the background and reloaded it when ready. Pause stopped the systems. Stop restored the saved world. Those buttons kept the test loop moving without stopping the debugger for every change.

  The last platform was a Legion Go S running SteamOS. I first thought I could sideload the game like an Android app, but SteamOS was Linux, not Android, and its official Devkit client would not install on my Mac. I connected over SSH and used an Ubuntu container on the handheld to build the project. It ran on the Legion's AMD GPU. The useful result was that the same project built on a Mac, a Windows machine and a Linux handheld.

  Gram Build did not replace the tools it brought together. It learned enough to make one engine project build in different places, so I could get back to the part I actually wanted to test: the ray tracer. Read the full story in [Episode 1.5 on petretiberiu.dev](https://petretiberiu.dev/posts/gram-engine-01-5-gram-build-three-platforms/).
---

# Gram Engine - Episode 1.5: Gram Build on Three Platforms

Episode 1 put a triangle on screen. [Episode 2 is already published](https://petretiberiu.dev/posts/gram-engine-02-ray-tracing-in-one-weekend-on-the-gpu/), and it takes that engine into the book's ray tracer. It comes before Episode 2: the build work that let me test the ray tracer on more than my Mac.

To run the ray tracer on three platforms, Gram Build had to do more than pick a compiler. It needed three build modes with different jobs: Debug for development, Release for the game's own tools, and Final for a clean standalone run. It also needed the right compiler for each system, one IDE project for C++ and Rust, and a Linux handheld to test the whole path.

### A compiler prelude

A separate session on November 13 produced repository commits fixing several compiler and build issues. GCC rejected a member with the same name as its class, and `stb_image`'s SSE2 resampler was disabled for GCC. On Windows, `windows.h`'s `min` and `max` macros interfered with `std::max`.

Windows also would not let Gram overwrite a running `.exe`. Gram writes the replacement to `.partial`, moves the old executable to `.old`, then puts the new file in place. The main Gram Build story starts on the Mac the next day.

## Chapter 1 - Three configurations, three jobs

Until this work, `gram build` had one choice: Debug. One symptom showed what was missing: a breakpoint would not stop because CMake's build type was empty, so the compiler had left out debug symbols. I wanted three configurations with different jobs. Debug keeps the editor, logs and Vulkan validation for development. Release is optimized but keeps symbols and the game's own test panels. Final is a cleaner runtime, without the editor or validation layers; on Windows, it also opens without a console.

I wrote the small `Profile` model that describes what each configuration means to CMake and Cargo. Claude connected it to the `--config` option and gave each configuration its own output directory. That kept Debug and Release from reusing the same build files.

CMake was the part I had never written. I asked to learn it from the beginning. The first useful distinction was between **configure** and **build**. Configure reads the project and generates build files. Build runs them. With Make or Ninja, you choose Debug or Release during configure. Xcode and Visual Studio can generate one project containing all three configurations, then choose one when you build.

I also learned that CMake does not know the compiler at the same moment it starts. `CMAKE_PROJECT_TOP_LEVEL_INCLUDES` includes a file before compiler detection. `CMAKE_USER_MAKE_RULES_OVERRIDE` runs after CMake identifies the compiler, but before its default flags settle. I wrote the two CMake files with Claude's step-by-step guidance. We put a `message()` in each hook and ran configure. The output showed their order directly. CMake stopped feeling like a black box and started behaving like a sequence I could follow.

That order mattered. Final first configured without optimization because CMake did not yet know about a configuration named Final. The files we added register Debug, Release and Final, then derive their flags from the compiler's own defaults. Release inherits the compiler's “optimized but debuggable” settings. Final starts there and adds link-time optimization, which lets the compiler optimize across the finished program. The same CMake files worked on MSVC without hard-coded compiler flags.

Final still linked Debug versions of some libraries from vcpkg, the C++ dependency manager. `CMAKE_MAP_IMPORTED_CONFIG_FINAL` tells CMake which prebuilt dependency configuration to use. Claude's first suggestion was `Release`, but the mapping needed the trailing semicolon: `Release;`. That selects Release libraries and leaves an empty fallback for targets with no configuration of their own. One such target is `Vulkan::Vulkan`, created by CMake's `FindVulkan` module. The linker command exposed the difference between compiling optimized code and linking the right libraries.

A quieter mistake was `LT0` with a zero instead of the “O” in `LTO`. Cargo silently ignores environment variables it does not recognize, so the build would still have completed, just without link-time optimization. My early tests copied the same table as the implementation and repeated the typo. I rewrote them to check the rule instead of copying the values. That was a better test of what the configuration was supposed to do.

The configuration also had to reach C++. I wrote the `GRAM_CONFIG_*` macros and generator expressions with guidance. A generator expression waits until the selected configuration is known. A normal `CMAKE_BUILD_TYPE` check would fail in Xcode and Visual Studio, where configure happens once for all configurations. That is how Release could keep the game's panels while leaving the engine editor out.

Final without ImGui compiled on the first try, then opened as a black window. The only image had been drawn inside the editor's Viewport. I wrote a final display step that copies the scene image straight to the window, without needing an engine-owned shader. Testing it in Debug with ImGui disabled kept Vulkan validation on while I checked the standalone path. Claude separated the Engine and Game panels so Release could keep game-level tools without compiling the engine editor.

## Chapter 2 - Choosing a toolchain

The next problem was choosing the right compiler. MinGW can cross-compile Windows from macOS; MSVC runs natively on Windows.

I first wrote nested `if` statements for the choice. During review, a simpler model emerged: list the available toolchains in preference order, and let that order be the fallback. I wrote the resolver and its tests. Claude connected it to `gram build`, added automatic detection from `PATH`, and made fallback visible with a warning.

An explicit `--toolchain` is different from the default. If I ask for MSVC and it is missing, Gram should say so rather than silently switching. On my Mac, I made toolchain availability an input to the resolver, so I could test Windows decision paths without having MSVC installed.

I kept the settings in one model: the CMake generator and arguments, the vcpkg triplet for C++ dependencies, and the Rust target when one is needed. Claude wired it into the existing build commands. Some early tests showed how easy it was to get a green result without checking anything: I had an `assert!(true)` and an early return. Rewriting them to assert each expected result made the tests useful.

The resolver gained 17 focused tests. More importantly, the roughly 120 existing command tests passed unchanged. The new option had not changed the old default behavior.

## Chapter 3 - One IDE project for the whole tree

The repository held C++, Rust, shaders and schemas. I wanted one IDE project that showed the whole tree, built the C++ runtime and could ask Gram to rebuild the Rust gameplay library. I wrote the top-level CMake project that gathers the modules. Claude wrote the `gram ide` command and its project-generation plumbing.

The generated project includes a target for `GameLogic`. Building it in the IDE calls Gram, and the new library lands beside the game so hot reload can find it. Source and shader files appear in the project tree without being sent to the C++ compiler.

Xcode produced an error that said only “PhaseScriptExecution failed.” The project worked from Terminal, but Xcode opened from Finder did not inherit Terminal's `PATH`—the list of folders where the shell looks for commands—so it could not find Cargo. Claude made Gram pass its launch environment to the generated target. The failure was about where the IDE started, not about Rust.

Xcode could show Rust files but could not set breakpoints in files it did not compile. I used Xcode for C++ and attached VS Code to the running game for Rust. Visual Studio could set breakpoints directly in Rust source. It was a workable split, even if it was not one perfect IDE for everything.

### A separate Windows session

The fourth phase happened on Windows on November 16. It came from a separate session and a repository report, not from the Mac conversation. MSVC built the tree on the first try; the earlier GCC fixes had already removed the C++ assumptions that would have broken it.

I wrote the MSVC settings, the world snapshot and the replay state machine. Claude wrote Visual Studio detection and IDE integration, the Final setting that suppresses its console, and the process runner and toolbar. That let Gram find the compiler and its bundled CMake from an ordinary PowerShell. Visual Studio would not build while its debugger was running, so the build moved into the game. Play rebuilds `GameLogic` in the background and reloads it when ready. Pause stops the systems from ticking. Stop restores the saved world. When we returned to macOS, Claude's POSIX process runner let me test the same loop: a Rust panic appeared in the editor log, and Stop restored the simulation.

## Chapter 4 - A real Linux device

The third platform was a Legion Go S running SteamOS. I first thought about sideloading the game over USB-C, like an Android app. SteamOS was a read-only Linux system, not an Android device, and the official Devkit client would not install on macOS.

The workable route was SSH and a distrobox: an Ubuntu container that gives development tools a place to run without changing SteamOS. macOS cannot build Linux, so the sources went to the handheld and the build ran inside that container.

Claude handled the setup commands over SSH. I tested Play, Greet and Stop on the device. The game ran on the Legion Go S's AMD GPU without validation errors, and Stop restored the world. The book's scene read about 15 FPS in Debug. The fan sounded like it wanted to join the build too.

That was a counter reading, not a performance comparison. The useful result was that the project built and ran on a real Linux GPU, outside WSL2's software renderer. It was the reason to keep improving the build path.

## Where the interlude leaves Gram Build

By November 16, the same project tree could be built with Apple clang on macOS, MSVC on Windows and GCC on Linux. Gram could select configurations and toolchains, generate Xcode and Visual Studio projects, and run the gameplay rebuild from inside the editor when Visual Studio's debugger would not allow an IDE build.

The MinGW fallback on a native Windows machine remained untested because that machine did not have MinGW installed. The three items left open on November 16—`gram deploy`, screen scaling (DPI) and fullscreen—were resolved afterward; [Interlude 2.5 tells that part of the story](https://petretiberiu.dev/posts/gram-engine-02-5-optimizing-for-real-hardware/). Packaging remained future work: the configurations and standalone Final build are groundwork, not a package format or deployment pipeline.

## What's next

[Episode 2 is already published](https://petretiberiu.dev/posts/gram-engine-02-ray-tracing-in-one-weekend-on-the-gpu/). It picks up with the ray tracer this build work helped me test across platforms.

---

A build system is easy to mistake for plumbing that only matters before the interesting work starts. This interlude made it part of the engine's daily loop: choose a configuration, choose a compiler, open the right project, build while the game is running, and test on a device that is not the machine where the code was written. Gram did not replace CMake, Cargo or the IDEs. It made them agree about one project.
