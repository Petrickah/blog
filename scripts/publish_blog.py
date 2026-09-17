#!/usr/bin/env python3
"""Generate a Hugo content file from a 09_Blog/drafts/ note.

Reads a draft's frontmatter to locate it, extracts the ``## Draft`` section
verbatim (per the verbatim-text policy in ../CLAUDE.md) and the structured
``yaml`` block under ``## Promovare`` (see
03_Templates/Template - Blog Draft.md), and writes the resulting Hugo
content file under content/posts/ or content/projects/. Never touches git.

Usage:
    python3 publish_blog.py <source_id-or-filename-or-path> [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BLOG_DIR = SCRIPT_DIR.parent
DRAFTS_DIR = BLOG_DIR.parent / "drafts"
CONTENT_DIR = BLOG_DIR / "content"

# Scoped to just the frontmatter block, not the whole file — a draft's body
# can contain pasted yaml/config text that would otherwise false-positive
# (same lesson as .claude/skills/import-chatgpt-export/parse_chatgpt_export.py).
FRONTMATTER_RE = re.compile(r"^---\n(.*?\n)---\n", re.DOTALL)
SOURCE_ID_RE = re.compile(r"^source_id:\s*(\S+)\s*$", re.MULTILINE)


def find_draft(identifier: str) -> Path:
    direct = Path(identifier)
    if direct.is_file():
        return direct

    for candidate in (DRAFTS_DIR / identifier, DRAFTS_DIR / f"{identifier}.md"):
        if candidate.is_file():
            return candidate

    for md in DRAFTS_DIR.glob("*.md"):
        fm_match = FRONTMATTER_RE.match(md.read_text(encoding="utf-8"))
        if not fm_match:
            continue
        sid_match = SOURCE_ID_RE.search(fm_match.group(1))
        if sid_match and sid_match.group(1) == identifier:
            return md

    raise SystemExit(f"No draft found for '{identifier}' under {DRAFTS_DIR}")


def extract_section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE
    )
    match = pattern.search(body)
    if not match:
        raise SystemExit(f"Section '## {heading}' not found in draft")
    return match.group(1).strip("\n")


def extract_draft_body(body: str) -> str:
    text = extract_section(body, "Draft")
    fenced = re.match(r"^```markdown\n(.*)\n```\s*$", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    return text.strip("\n") + "\n"


# Romanian-specific diacritics — a cheap, zero-dependency signal that the
# extracted body still has Romanian text (an editorial note, a teaser)
# that was never meant to be published. Not a general language detector:
# it only catches leftover Romanian, the actual risk this vault produces,
# since drafts are written in whatever language is easiest and the
# publish policy is verbatim copy — nothing strips or rewrites content.
ROMANIAN_DIACRITICS = set("ăâîșțĂÂÎȘȚ")


def check_language(body: str, allow_non_english: bool) -> None:
    found = sorted({c for c in body if c in ROMANIAN_DIACRITICS})
    if found and not allow_non_english:
        raise SystemExit(
            "Extracted draft body contains Romanian diacritics "
            f"({''.join(found)}) — this blog publishes in English only. "
            "Likely cause: '## Draft' has leftover non-English text (an "
            "editorial note to Tiberiu, a teaser) that isn't meant for "
            "publication — see 09_Blog/blog/CLAUDE.md, '## Draft' must "
            "contain only the final publication-ready text. Fix the draft "
            "note and re-run, or pass --allow-non-english if this is "
            "genuinely intentional."
        )


def extract_yaml_block(promovare_text: str) -> str:
    match = re.search(r"```yaml\n(.*?)\n```", promovare_text, re.DOTALL)
    if not match:
        raise SystemExit(
            "No ```yaml block found under '## Promovare' > "
            "'Instrucțiuni specifice articolului'. See "
            "03_Templates/Template - Blog Draft.md for the expected format."
        )
    return match.group(1)


def parse_promotion_yaml(yaml_text: str) -> tuple[str, dict[str, str]]:
    hugo_path: str | None = None
    frontmatter: dict[str, str] = {}
    in_frontmatter = False

    for raw in yaml_text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("hugo_path:"):
            hugo_path = raw.split(":", 1)[1].strip()
            in_frontmatter = False
        elif raw.startswith("frontmatter:"):
            in_frontmatter = True
        elif in_frontmatter and raw.startswith("  "):
            # partition on the first ':' only — a quoted value (title,
            # summary) may itself contain colons/commas, and must survive
            # untouched into the regenerated frontmatter line below.
            key, _, value = raw.strip().partition(":")
            frontmatter[key.strip()] = value.strip()
        else:
            in_frontmatter = False

    if not hugo_path:
        raise SystemExit("'hugo_path' missing from the yaml promotion block")
    if not frontmatter:
        raise SystemExit("'frontmatter' missing/empty in the yaml promotion block")
    return hugo_path, frontmatter


def build_frontmatter(fields: dict[str, str]) -> str:
    lines = ["---", *(f"{key}: {value}" for key, value in fields.items()), "---"]
    return "\n".join(lines) + "\n\n"


def resolve_target(hugo_path: str) -> Path:
    target = (BLOG_DIR / hugo_path).resolve()
    posts_dir = (CONTENT_DIR / "posts").resolve()
    projects_dir = (CONTENT_DIR / "projects").resolve()
    if not (target.is_relative_to(posts_dir) or target.is_relative_to(projects_dir)):
        raise SystemExit(
            f"hugo_path must be under content/posts/ or content/projects/, got: {hugo_path}"
        )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", help="source_id, filename, or path of a draft under ../drafts/")
    parser.add_argument("--dry-run", action="store_true", help="print the generated file instead of writing it")
    parser.add_argument("--force", action="store_true", help="overwrite an existing target file")
    parser.add_argument("--allow-non-english", action="store_true", help="skip the Romanian-diacritics language check")
    args = parser.parse_args()

    draft_path = find_draft(args.draft)
    text = draft_path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        raise SystemExit(f"{draft_path} has no frontmatter block")
    body = text[fm_match.end():]

    hugo_path, frontmatter_fields = parse_promotion_yaml(
        extract_yaml_block(extract_section(body, "Promovare"))
    )
    target = resolve_target(hugo_path)
    draft_body = extract_draft_body(body)
    check_language(draft_body, args.allow_non_english)
    output = build_frontmatter(frontmatter_fields) + draft_body

    if args.dry_run:
        print(f"--- {target.relative_to(BLOG_DIR)} ---")
        print(output)
        return

    if target.exists() and not args.force:
        raise SystemExit(f"{target} already exists — pass --force to overwrite")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output, encoding="utf-8")

    rel = target.relative_to(BLOG_DIR)
    print(f"Wrote {rel}")
    print()
    print("Next steps (manual, per ../CLAUDE.md):")
    print(f"  hugo --buildDrafts -D   # sanity build/skim before committing")
    print(f"  git add {rel} && git commit -m '...'")
    print("  git push origin main && git push github main:main")


if __name__ == "__main__":
    main()
