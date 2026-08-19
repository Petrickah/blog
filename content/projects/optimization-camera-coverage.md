---
title: "Optimization Algorithms for Camera Coverage"
subtitle: "university project"
date: 2021-10-12
featured: false
summary: "Comparing Hill Climbing (with and without retrace) against Simulated Annealing for maximizing three ceiling cameras' coverage area — Simulated Annealing won."
repo: "https://github.com/Petrickah/Optimization"
---

A coursework problem: three video cameras, mounted on the ceiling of a room, need to be positioned to maximize the total floor area they cover between them. Built in Python, comparing three search algorithms against each other on the same problem instance.

## The three algorithms

Hill Climbing without retrace, Hill Climbing with retrace, and Simulated Annealing — all applied to the same coverage-maximization problem. Simulated Annealing came out ahead: it found the maximum coverage area and camera positions in a few minutes on the example instance, where the Hill Climbing variants were more prone to getting stuck.

Took about two weeks end to end, and scored a 10/10 on the exam.
