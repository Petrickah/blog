---
title: "Console Maze Generator"
subtitle: "university coursework, C++"
date: 2019-02-22
featured: false
summary: "A randomized depth-first-search maze generator, animated live in a Windows console, with Dijkstra's algorithm tracing the shortest path once generation finishes."
repo: "https://github.com/Petrickah/maze-generating"
---

There's no README in this repo — it's a single 2019 coursework submission, one commit, one `main.cpp`. Everything below is read directly from the code, not from any write-up, so treat it as a description rather than a recollection.

## Generating the maze

The algorithm is a randomized depth-first-search — the classic "recursive backtracker" maze algorithm, implemented iteratively with an explicit stack rather than recursion. From a random starting cell, it repeatedly looks at the current cell's unvisited cardinal neighbors (N/E/S/W), picks one at random, carves a passage into it (tracked as bitflags per cell), and pushes it onto the stack. When a cell has no unvisited neighbors left, the algorithm pops the stack and backtracks, until every cell has been visited.

Alongside the maze grid itself, the same carving step builds a graph — an adjacency list mapping each cell to its connected neighbors — which is what makes the next part possible.

## Finding the way out

Once the maze is fully generated, the program runs Dijkstra's shortest-path algorithm over that graph, from the starting cell to wherever generation ended, and animates the result: the shortest path back is traced and drawn in blue over the rest of the maze.

## Rendering

Drawing happens through a small custom console engine (`evoConsoleGameEngine.h`) — Windows-only, built directly on the Win32 console API, adapted from javidx9's (OneLoneCoder) `olcConsoleGameEngine`, widely used at the time in his C++ tutorials.

Controls: `C` regenerates a new random maze, `V` skips the generation animation and jumps straight to the finished maze, and `Escape` exits, cleaning up the maze array, stack, and graph.
