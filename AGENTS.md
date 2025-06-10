# AGENTS.md

## Overview

This project contains a SvelteKit web frontend, a Flask-based search service, Python generation scripts, and VitePress documentation. Use Node.js 20.x and Python 3.12.

## Commands to Run

1. **Node build & tests**
    ```bash
    npm ci
    npm run check     # TypeScript and Svelte checks
    npm test          # runs Vitest tests
    ```
2. **Documentation**
   If you modify files in `docs/`, ensure the documentation builds:
    ```bash
    npm run docs:build
    ```
3. **Python search or generation code**
    ```bash
    cd search        # or 'generation'
    pipenv sync
    ```
    There is no dedicated test suite, but verify `pipenv run python app.py --help`
    (or `main.py --help` for generation) runs without errors.

## Coding Conventions

- Use 4‑space indentation in TypeScript, Svelte, and Python files.
- Strings generally use double quotes.
- Keep TypeScript strict mode enabled (see `tsconfig.json`).

## Pull Requests

- Ensure Node tests and checks pass before submitting.
- Include a short summary in the PR body describing the change.
- Follow the guidelines from `CONTRIBUTING.md` and respect the Code of Conduct.
