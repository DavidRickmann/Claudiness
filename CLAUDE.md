# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## What This Is

Claudiness is a multi-model AI writing style detector. It scores text (0-100) against `.style` fingerprint files for Claude, ChatGPT, Grok, or custom models. Pattern-matching based, not ML - it detects what people _think_ looks like AI.

## Running

```bash
claudiness myfile.txt                  # Score against all models
claudiness myfile.txt --model claude   # Score against one model
claudiness myfile.txt -claude          # Shorthand
claudiness --text "some text"          # Inline text
echo "text" | claudiness               # Stdin
claudiness myfile.txt --verbose        # Show matched patterns
claudiness myfile.txt --json           # JSON output
claudiness fetch                       # Update styles from web (requires requests)
claudiness list-models                 # Show loaded .style files
```

## Testing

```bash
python -m pytest tests/ -v
```

## Architecture

Modular `src/` layout:

- `cli.py` - Entry point, subcommand routing, argument parsing
- `scoring.py` - Generic scoring engine (scores text against any .style definition)
- `patterns.py` - Pattern matching helpers (count, find, line-start matching)
- `structural.py` - Structural text analysis (bullet ratio, em-dash rate, sentence variance)
- `style_loader.py` - Discover/load .style files from bundled, user, project, and custom dirs
- `report.py` - Terminal output formatting with bar charts
- `fetch.py` - Web fetch workflow for discovering and assembling new .style files
- `styles/*.style` - Bundled fingerprint definitions (JSON)

## Publishing

Automated via GitHub Actions. To release:

1. Bump `version` in `pyproject.toml`
2. Commit: `git commit -am "Bump to vX.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Push: `git push && git push --tags`

The workflow runs tests, builds, and publishes to PyPI via trusted publisher.
