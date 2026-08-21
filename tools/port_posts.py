#!/usr/bin/env python3
"""Port Jekyll/Chirpy _posts to Astro content collection.

- slug = filename without the leading YYYY-MM-DD- and .md (preserves /posts/:slug/)
- normalize front matter to the Astro schema (title, date, categories, tags, image, pin)
- strip Liquid {% raw %}/{% endraw %} wrappers (Astro .md keeps {{ }} literal)
- map ```null code fences to ```text (Shiki has no 'null' grammar)
- drop kramdown IAL markers {: .foo }
"""
import json
import os
import re
import glob

SRC = "_posts"
DST = "src/content/posts"
os.makedirs(DST, exist_ok=True)

FM_LIST_RE = re.compile(r"^\[(.*)\]$")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def parse_list(v):
    v = v.strip()
    m = FM_LIST_RE.match(v)
    if not m:
        return [v.strip().strip("'\"")] if v else []
    inner = m.group(1).strip()
    if not inner:
        return []
    out = []
    for part in inner.split(","):
        p = part.strip().strip("'\"").strip()
        if p:
            out.append(p)
    return out


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    fm = {}
    for line in fm_block.split("\n"):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm, body


def clean_body(body):
    lines = body.split("\n")
    out = []
    for ln in lines:
        s = ln.strip()
        if s == "{% raw %}" or s == "{% endraw %}":
            continue
        out.append(ln)
    body = "\n".join(out)
    body = re.sub(r"```null\b", "```text", body)
    body = re.sub(r"\{:\s*\.[^}]*\}", "", body)
    return body


def norm_date(v):
    v = v.strip().strip("'\"")
    m = re.match(r"(\d{4}-\d{2}-\d{2})", v)
    return m.group(1) if m else v


ported = []
for path in sorted(glob.glob(os.path.join(SRC, "*.md"))):
    fname = os.path.basename(path)
    slug = DATE_PREFIX_RE.sub("", fname[:-3]).replace("?", "").replace("#", "").strip()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, body = split_front_matter(text)

    file_date_m = re.match(r"(\d{4}-\d{2}-\d{2})", fname)
    date = norm_date(fm.get("date", "")) or (file_date_m.group(1) if file_date_m else "")

    title = fm.get("title", slug).strip().strip("'\"")
    categories = parse_list(fm.get("categories", "")) if "categories" in fm else []
    tags = parse_list(fm.get("tags", "")) if "tags" in fm else []
    image = (fm.get("image", "").strip() or fm.get("path", "").strip()).strip("'\"")
    pin = fm.get("pin", "").strip().lower() in ("true", "yes")

    fm_lines = ["---", f"title: {json.dumps(title, ensure_ascii=False)}", f"date: {date}"]
    fm_lines.append(f"categories: {json.dumps(categories, ensure_ascii=False)}")
    fm_lines.append(f"tags: {json.dumps(tags, ensure_ascii=False)}")
    if image:
        fm_lines.append(f"image: {json.dumps(image, ensure_ascii=False)}")
    if pin:
        fm_lines.append("pin: true")
    fm_lines.append("---")

    out = "\n".join(fm_lines) + "\n\n" + clean_body(body).lstrip("\n")
    with open(os.path.join(DST, slug + ".md"), "w", encoding="utf-8") as f:
        f.write(out)
    ported.append(slug)

print(f"ported {len(ported)} posts")
for s in ported[:5]:
    print("  slug:", s)
