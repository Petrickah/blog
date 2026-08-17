---
title: "InfoTest"
subtitle: "university project"
date: 2021-10-12
featured: true
summary: "HackerRank-style code evaluation platform — Python-based evaluator, Laravel/PHP/MySQL backend, Dockerized. Applied, academic-scope SQL/backend experience."
repo: "https://github.com/Petrickah/InfoTest"
---

InfoTest is a web platform for evaluating algorithmic problem submissions — students upload solutions to Data Structures & Algorithms problems, and the platform compiles and runs them automatically. Built as an internship project at Petroleum-Gas University of Ploiești, with three fellow students.

## How it works

Submissions are compiled and executed in isolated subprocesses: GCC handles C/C++ compilation, while a Python-based evaluator drives the whole pipeline — spawning the compilation/run subprocess, parsing its output, and redirecting Linux I/O for logging. The backend (Apache, MySQL, PHP, Laravel) manages users and submissions, built around Laravel's OOP/MVC conventions. The frontend used static-generated pages (HTML/CSS, React via Gatsby).

## Extensibility

Rather than hardcoding features, we built a plugin/theme system on top of Laravel: an `app` folder hosts plugin and theme files, each registered as a class in `plugins.php`; theme files are stored in the database and resolved at request time. The same system exposes a RESTful API path for anything a plugin shouldn't need direct app access for.

## Deployment

Docker containers handled CI and environment consistency across the team, rather than relying on everyone's local PHP/MySQL setup matching.
