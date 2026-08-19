---
title: "EvoPASS — An Android Password Manager (2019, Retrospective)"
date: 2019-10-01
draft: false
tags: ["android", "kotlin", "cryptography", "security"]
---

> Retrospective note, written in 2026. Unlike the [ray tracer post]({{< ref "ray-tracer-compute-shaders.md" >}}), there's no surviving Medium article or gist for this one — the source below is everything that's left: a few CV bullet points from October 2019, no source code, no repository. Rather than let it disappear entirely, here's what those bullet points describe.

EvoPASS was a university project built during my Computer Science studies at Petroleum-Gas University of Ploiești — an Android password manager written in Kotlin.

The core idea was hybrid encryption, a standard pattern for this kind of problem: passwords were stored encrypted with **AES**, a fast symmetric cipher well suited to encrypting the actual data — while the AES key itself was wrapped with **RSA**, an asymmetric cipher, so the key protecting your passwords wasn't just sitting on the device in the clear. This combination — symmetric encryption for the bulk data, asymmetric encryption to protect the symmetric key — is why hybrid schemes like this show up so often in real systems: you get AES's speed and RSA's key-management properties without paying RSA's cost for encrypting large amounts of data.

Unlocking the vault supported both a fingerprint and a password, and once in, the app handled the basics you'd expect from a password manager: saving, deleting, modifying, and generating passwords for any account. Everything lived locally on the phone — no sync, no backend, no cloud storage.

That's the honest extent of what's recoverable now. No architecture diagrams, no code, no screenshots — just a description of what it did, from a CV written a few years after the fact. If nothing else, it's a marker that mobile development and applied cryptography were part of the path here too, even if this particular project never made it past a university assignment.
