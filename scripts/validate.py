#!/usr/bin/env python3
"""Checks that the skill is complete and safe to publish."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill"
README = ROOT / "README.md"
errors = []


def check(ok, message):
    if not ok:
        errors.append(message)


def section(text, heading):
    """Body of a markdown section, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    match = re.search(rf"^{re.escape(heading)}\b.*$", text, re.M)
    if not match:
        return ""
    rest = text[match.end():]
    end = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return rest[: end.start()] if end else rest


main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
front = re.match(r"^---\n(.*?)\n---\n", main, re.S)
check(front, "SKILL.md: missing frontmatter")
if front:
    check("name: pr-orchestrator" in front[1], "SKILL.md: wrong name")
    check("description:" in front[1], "SKILL.md: missing description")

docs = sorted(SKILL.rglob("*.md")) + [README]
for path in docs:
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\((?!https?:|#)([^)#]+)", text):
        check((path.parent / target).exists(), f"{path.name}: broken link {target}")

# Rubric: the block under `rubric:` runs to the next top-level key. Blank and comment lines are skipped;
# every other line must be `  key: <non-negative int>`, with no duplicate keys or blocks.
config = (SKILL / "config.example.yml").read_text(encoding="utf-8")
lines = config.splitlines()
rubric = {}
starts = [i for i, line in enumerate(lines) if re.match(r"rubric:\s*(#.*)?$", line)]
check(len(starts) == 1, f"config: expected one rubric block, found {len(starts)}")
if starts:
    for line in lines[starts[0] + 1:]:
        if re.match(r"\S", line) and not line.startswith("#"):
            break
        if not line.strip() or line.strip().startswith("#"):
            continue
        match = re.fullmatch(r"  (\w+): (\d+)(?:\s+#.*)?\s*", line)
        check(match, f"config: bad rubric line {line.strip()!r}")
        if match:
            check(match[1] not in rubric, f"config: duplicate rubric key {match[1]}")
            rubric[match[1]] = int(match[2])
    check(rubric, "config: empty rubric")
    total = sum(rubric.values())
    check(total == 100, f"config: rubric sums to {total}, expected 100")

# Every published rubric table must list the config categories, by name and weight, in the same order.
LABELS = {  # config key -> (Vietnamese label prefix, English label prefix)
    "correctness": ("Đúng đắn", "Correctness"),
    "requirements": ("Yêu cầu", "Requirements"),
    "quality": ("Chất lượng", "Quality"),
    "tests": ("Test", "Tests"),
    "scope": ("Phạm vi", "Scope"),
}
for key in rubric:
    check(key in LABELS, f"config: rubric key {key} has no label in validate.py")
tables = {
    "SKILL.md ## 6. Chấm": (section(main, "## 6. Chấm"), 0, r"^\|([^|]+)\|\s*(\d+)%\s*\|\s*$"),
    "pr-comment.md ### Bảng điểm": (
        section((SKILL / "templates/pr-comment.md").read_text(encoding="utf-8"), "### Bảng điểm"),
        0,
        r"^\|([^|]+)\|\s*(\d+)%\s*\|",
    ),
    "README.md ## Scoring": (section(README.read_text(encoding="utf-8"), "## Scoring"), 1, r"^\|([^|]+)\|\s*(\d+)\s*\|\s*$"),
}
for name, (body, lang, row) in tables.items():
    found = [(label.strip(), int(n)) for label, n in re.findall(row, body, re.M)]
    expected = [(LABELS.get(key, ("?", "?"))[lang], weight) for key, weight in rubric.items()]
    ok = len(found) == len(expected) and all(
        label.startswith(want) and n == weight for (label, n), (want, weight) in zip(found, expected)
    )
    check(ok, f"{name}: rubric {found} does not match config {expected}")

# Every config key must be documented: top-level as `key` or `key.…`, keys under audit/merge as `parent.key`.
skill_text = "\n".join(p.read_text(encoding="utf-8") for p in SKILL.rglob("*.md"))
parent = None
for line in lines:
    match = re.match(r"^( *)(\w+):", line)
    if not match:
        continue
    indent, key = match[1], match[2]
    if not indent:
        parent = key
        check(re.search(rf"`{key}[`.]", skill_text), f"config: `{key}` not documented in skill/*.md")
    elif parent in ("audit", "merge"):
        check(re.search(rf"`{parent}\.{key}[`: ]", skill_text), f"config: `{parent}.{key}` not documented in skill/*.md")

for path in [p for p in SKILL.rglob("*") if p.is_file()] + [README]:
    text = path.read_text(encoding="utf-8")
    check(not re.search(r"/Users/|/home/\w", text), f"{path.name}: personal path")
    check(not re.search(r"\b(ghp_|sk-ant-|AKIA)[A-Za-z0-9]", text), f"{path.name}: looks like a secret")

for error in errors:
    print(f"FAIL {error}")
print(f"{'FAILED' if errors else 'OK'}: {len(docs)} documents checked")
sys.exit(1 if errors else 0)
