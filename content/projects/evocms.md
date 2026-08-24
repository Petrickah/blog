---
title: "EvoCMS"
subtitle: "personal project, Laravel"
date: 2020-02-02
weight: 60
featured: false
summary: "A Laravel 6 content-management system built around a plugin/theme architecture — service-provider-based plugins and swappable themes instead of hardcoded features."
repo: "https://github.com/Petrickah/EvoCMS"
---

EvoCMS is a Laravel 6 content-management system, built as a personal project rather than a specific course assignment. The point of it wasn't any single feature — it was the architecture underneath: a CMS where functionality is added as plugins and presentation is swapped as themes, instead of both being hardcoded into the app.

## Plugins

Each plugin is a class extending a shared `Plugin` base (itself a Laravel controller, with the usual `DispatchesJobs`/`ValidatesRequests`/`AuthorizesRequests` traits mixed in), registered by name in a single `plugins.php` map and wired up through its own Laravel service provider. `Articole` (articles) and `Meniu` (menu) ship as the first two plugins — less "the point of the CMS" and more a proof that the plugin system actually works end to end: routes, views, and an admin-facing controller, all scoped to the plugin rather than living in the main app.

## Themes

Presentation is a separate concern from plugins, handled by its own `ThemesServiceProvider` and a `Theme` base class — `My_Theme` is the one theme that exists, with its own controllers, routes, providers, and views, kept apart from both the plugins and the core app.

## Where this went next

This is also the architecture [InfoTest](/projects/infotest/)'s evaluation platform borrowed for its own plugin/theme system — same pattern (a Laravel `app` folder hosting plugin/theme classes, registered centrally, resolved at request time), reused on a second project rather than designed twice.
