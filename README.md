# PR Orchestrator

[![validate](https://github.com/dakiquang/pr-orchestrator/actions/workflows/validate.yml/badge.svg)](https://github.com/dakiquang/pr-orchestrator/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One model writes, another reviews, a person decides.

PR Orchestrator is an agent skill that reviews a pull request with two models from different families. They cross-check each other's findings, each finding is verified against the code, and the PR gets a score against a weighted rubric. It works with any repository: nothing about the language, package manager or branch names is assumed.

## Why

A model reviewing its own work tends to agree with itself. A second model catches a different class of mistake, but two opinions are not enough: findings still need evidence, and merging still needs a person's permission.

## Modes

| Mode | What it does | Changes anything? |
|---|---|---|
| `review` | Reads the PR, cross-audits, verifies, scores | No |
| `fix` | Reviews, makes the smallest fix, tests, scores again | Yes, within the findings |
| `full` | Reviews, fixes, tests, comments, merges this PR | Yes |
| `test` | Finds and runs the relevant tests | Runs tests only |
| `sync` | Cherry-picks merged commits to a target branch | Yes, cherry-picks only |

A PR with no mode runs `review`.

## Guardrails

- Repository rules win over the skill: `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, then contributing docs.
- `review` is read-only, and the working tree must be unchanged afterwards.
- No force-push, `--no-verify`, destructive reset or secret commit.
- Permission covers one PR. Anything else needs a separate request.
- Commands are discovered from the repository, never guessed.
- On your own PR (author matches any `gh` login on the machine), the comment drops the mention and the personal voice: score and findings only.

## Scoring

| Area | Weight |
|---|---|
| Correctness | 35 |
| Requirements | 25 |
| Quality | 15 |
| Tests | 15 |
| Scope | 10 |

Hard caps and merge gates are in [gates.md](skill/gates.md). A repository can override all of this with `.pr-orchestrator.yml`; see [config.example.yml](skill/config.example.yml).

## Install

Copy `skill/` into your agent's skills folder as `pr-orchestrator`:

```bash
git clone https://github.com/dakiquang/pr-orchestrator
cp -R pr-orchestrator/skill ~/.claude/skills/pr-orchestrator
```

Then ask your agent to run it on a PR. The instructions are written in Vietnamese; agents follow them in any language, and comments can use another language through `language` in the config.

## Validate

```bash
python3 scripts/validate.py
```

CI runs the same check on every push: required metadata, internal links (README included), a rubric with non-negative weights that sums to 100 and matches every published rubric table, every config key documented in the skill, and no personal paths or secrets.

Built by [Quang Dang](https://quangdk.com).
