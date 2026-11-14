# Contributing to IntelliReading Calibre Plugins

Thank you for considering contributing to IntelliReading Calibre Plugins! Before diving in, please read these guidelines carefully.

## Before You Write Any Code

**Open an issue first.** For anything beyond a small bug fix, typo, or documentation improvement, please open an issue and wait for a response before writing code. This can save you hours of work on something that won't be merged.

If an issue already exists, comment on it to signal your intent so work isn't duplicated.

## Pull Request Size

**Keep PRs small and focused on a single concern.**

- **Target under ~300 lines changed** (excluding lock files and generated code)
- **One PR = one thing.** Don't bundle a bug fix with a refactor with a new feature
- If your change is naturally large, break it into a chain of smaller PRs

PRs that are too large to review efficiently will be asked to be split.

## Prerequisites

- **Python 3.11**
- **Calibre** installed locally, with `calibre-customize` and `calibre-debug` available. The helper script uses `/opt/calibre` by default; set `CALIBRE_DIR` to point elsewhere
- **black**, **ruff**, and **mypy** installed via pip

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/intellireading-calibre-plugins.git
   ```
3. **Create a branch** with a descriptive name:
   ```bash
   git checkout -b fix/description-of-fix
   # or
   git checkout -b feat/description-of-feature
   ```
4. **Install the lint tools**:
   ```bash
   pip install black ruff mypy
   ```
5. **Make your changes** and validate before pushing:
   ```bash
   black --check . --line-length 120
   ruff check . --ignore=E501,I001
   mypy . --ignore-missing-imports
   ```
6. **Test manually in Calibre** where applicable. You can install the plugins from this checkout with:
   ```bash
   ./debug-plugins.py
   ```
7. **Push and open a PR** against the `master` (or `main`) branch, filling in the PR template completely.

## Response Time Expectations

Reviews may take a few days depending on availability. A PR sitting without a response is not a rejection. Please feel free to leave a polite ping after a week if there's been no activity.

## Thank You

Every contribution makes a real difference. Thank you for taking the time to improve IntelliReading Calibre Plugins.
