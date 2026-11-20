# Contributing to layerkit

Thanks for your interest. This page explains how to propose a change.

## Before you start

- Look through the [open issues](https://github.com/JimmyHerreraIs/layerkit/issues). Comment on one to say you are working on it, or open a new one to discuss your idea first.
- Check the "Scope" table in the [README](README.md). Ideas outside it are welcome as issues, but they are revisited after v1.0.

## Set up

```bash
git clone https://github.com/JimmyHerreraIs/layerkit.git
cd layerkit
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

`main` only holds published releases. Day-to-day work happens on `develop`.

1. Create a branch **from `develop`**, named `<type>/<issue>-<short-description>`:
   `feature/12-mask-cleanup`, `fix/15-rotation`, `docs/18-readme-example`.
   Lowercase, hyphens, no spaces.
2. Make small commits. Each commit does one thing.
3. Push your branch and open a pull request **into `develop`** (never `main`).
4. Wait for the `quality` check to pass, then address any review comments.
5. A maintainer merges with *Squash and merge*.

One branch is one issue and one pull request. If a change grows past roughly 400 lines, split it.

## Commit messages

Format: `type: what it does`, present tense, lowercase, about 60 characters.

| Type | Use it for |
|---|---|
| `feat` | A new user-facing capability |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Code changes that do not change behavior |
| `chore` | Tooling, dependencies, CI |

Good: `fix: avoid crash when the image has no alpha channel`
Bad: `changes`, `fix stuff`, `final version v2`

The pull request title follows the same format: with *Squash and merge* it becomes the commit on `develop`.

## Code standards

Automated (the `quality` check runs all of these, and so does `pre-commit` locally):

- **Types everywhere.** Public functions declare their parameters and return type. `mypy --strict` passes.
- **Style.** `ruff check` and `ruff format` report nothing.
- **Tests.** Every `feat` and `fix` comes with a test. `pytest` passes.

By review:

- Names explain themselves: `filter_small_masks(masks, min_area)`, not `proc(m, x)`.
- Short functions that do one thing (about 30 lines at most).
- No magic numbers: give thresholds a named constant at the top of the module.
- Errors are clear and never silent: no bare `except: pass`; raise specific exceptions with a useful message.
- Use `logging`, not `print`. Only the CLI talks to the user.
- No secrets, no commented-out code, no large binary files.
- Public code has a docstring: what it does, arguments, return value, errors raised.
- `layerkit.core` must never import from the CLI or the API.

## Before you open a pull request

- [ ] `pre-commit run --all-files` passes
- [ ] I read my own diff in "Files changed"
- [ ] New functions have type hints, a docstring and a test
- [ ] No `print`, commented-out code or stray files
- [ ] The title follows the commit format and the description links the issue (`Closes #123`)
- [ ] I updated the README or docs if visible behavior changed

## Reporting bugs and vulnerabilities

Use the issue forms for bugs and ideas. For security problems, do **not** open a public issue: follow [SECURITY.md](SECURITY.md).
