#!/usr/bin/env python3
"""Checks that the skill is complete and safe to publish."""
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skill"
errors = []


def check(ok, message):
    if not ok:
        errors.append(message)


main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
front = re.match(r"^---\n(.*?)\n---\n", main, re.S)
check(front, "SKILL.md: missing frontmatter")
if front:
    check("name: pr-orchestrator" in front[1], "SKILL.md: wrong name")
    check("description:" in front[1], "SKILL.md: missing description")

for path in SKILL.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\((?!https?:|#)([^)#]+)", text):
        check((path.parent / target).exists(), f"{path.name}: broken link {target}")

config = (SKILL / "config.example.yml").read_text(encoding="utf-8")
block = re.search(r"^rubric:\n((?:  \w+: \d+\n)+)", config, re.M)
check(block, "config: missing rubric")
if block:
    total = sum(int(n) for n in re.findall(r": (\d+)", block[1]))
    check(total == 100, f"config: rubric sums to {total}, expected 100")

for path in SKILL.rglob("*"):
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        check(not re.search(r"/Users/|/home/\w", text), f"{path.name}: personal path")
        check(not re.search(r"\b(ghp_|sk-ant-|AKIA)[A-Za-z0-9]", text), f"{path.name}: looks like a secret")

for error in errors:
    print(f"FAIL {error}")
print(f"{'FAILED' if errors else 'OK'}: {sum(1 for _ in SKILL.rglob('*.md'))} documents checked")
sys.exit(1 if errors else 0)
