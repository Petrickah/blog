---
title: "GrilaTV"
subtitle: "university project, Databases & DBMS course"
date: 2020-02-05
weight: 40
featured: true
summary: "Relational database design and normalization for a TV-guide domain, redocumented across two semester iterations, Dockerized deployment. Applied, academic-scope schema-design experience."
repo: "https://github.com/Petrickah/BazaDate-GrilaTV"
---

GrilaTV is a relational database design project built for a Databases & DBMS course — modeling a TV-guide-style domain (people, broadcasts, schedules, subscriptions) and iterating on its schema across two semester passes.

## Two iterations, one schema story

The first semester produced a working schema and its PhpMyAdmin export (`grilatv.sql`). The second iteration went back to normalize it properly — the redocumented, normalized version (`grilatv-normalizata.sql`) is what the current write-up covers. Keeping both exports side by side made the normalization work concrete: a before/after on the same domain, not just a description of what normalization is supposed to fix.

## Deployment

Three Docker containers (`docker-compose.yml`): PHP, MySQL, and Apache, each with its own Dockerfile. The Apache config serves the project straight from the root — no virtual host needed, so a WAMP-based local setup can just step aside temporarily. The PHP entry points cover the domain's core pages: people, broadcasts, schedules, offers, and subscribers.
