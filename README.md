# Blog

Blog personal de portofoliu (Hugo static site) — articole despre proiectele din
acest monorepo și, eventual, despre traiectoria profesională a autorului.
Deploy public pe Cloudflare Pages; conținutul draft trăiește separat de cel
public (vezi `CLAUDE.md` din acest folder pentru convenția de branch-uri).

## Overview

Site static generat cu [Hugo](https://gohugo.io/). Conținutul e alimentat
direct din `content/`, care e și expus în vault-ul Obsidian al autorului ca
habitat (`09_Blog`, symlink relativ) — un singur set de fișiere, fără
sincronizare separată.

## Setup

```bash
# Hugo extended, instalat local (binar din github.com/gohugoio/hugo/releases)
hugo version
```

## Usage

```bash
hugo server --buildDrafts   # preview local, cu draft-uri
hugo                        # build public (fără draft-uri) -> public/
```

Build-ul CI (Jenkins pentru branch-ul `drafts`, GitHub Actions pentru `main`)
e documentat în `CLAUDE.md`.
