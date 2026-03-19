# Claudiness

A CLI tool that detects AI writing patterns in text. Scores how closely a piece of writing matches the stylistic fingerprint of Claude, ChatGPT, Grok, or any AI model with a `.style` definition.

Unlike AI detectors that use machine learning (and frequently get it wrong), claudiness uses pattern matching against specific, documented markers that readers associate with AI-generated text. It tells you what people will _think_ looks like AI, not whether AI actually wrote it.

## Install

```bash
pipx install claudiness
```

Or with pip:

```bash
pip install claudiness
```

## Usage

```bash
# Score a file against all known models
claudiness essay.txt

# Score against a specific model
claudiness essay.txt --model claude
claudiness essay.txt -claude              # shorthand

# Inline text
claudiness --text "That's a great question. I think..."

# Pipe from stdin
echo "some text" | claudiness

# See which patterns matched
claudiness essay.txt --verbose

# Machine-readable output
claudiness essay.txt --json
claudiness essay.txt --score-only
```

## Interpreting scores

- **0-30**: Natural sounding, low AI fingerprint
- **31-60**: Some AI patterns detected, may warrant editing
- **61-100**: Strong AI writing patterns, should be rewritten

Use `--verbose` to see exactly which patterns triggered and rewrite those specific phrases.

## What it detects

Each model has a `.style` file defining its fingerprint across categories like:

- **Hedging** - "it's worth noting", "it's important to consider"
- **Balance markers** - "on the other hand", "while...also"
- **Vocabulary** - model-specific word choices ("delve", "tapestry", "straightforward")
- **Structural patterns** - bullet ratio, em-dash frequency, parenthetical asides
- **Safety disclaimers** - "I should note", "it's important to remember"
- **Penalties** - patterns associated with _other_ models reduce the score

Scores are normalized per 500 words and capped per category so no single pattern type dominates.

## Bundled models

- **Claude** (Anthropic) - 7 categories
- **ChatGPT** (OpenAI) - 6 categories
- **Grok** (xAI) - 6 categories

## Custom styles

Add your own `.style` files to:

- `~/.config/claudiness/styles/` - user-wide
- `./.claudiness/styles/` - project-local

Or point to a directory:

```bash
claudiness essay.txt --style-dir /path/to/styles
```

See the bundled `.style` files in `src/claudiness/styles/` for the format.

## Updating style definitions

Style fingerprints can be refreshed from the web:

```bash
# Requires: pip install claudiness[fetch]
claudiness fetch                    # Update all models
claudiness fetch --model claude     # Update one model
claudiness fetch --search           # Search for new sources
```

## List available models

```bash
claudiness list-models
```

## No dependencies

Core functionality uses only the Python standard library. The `fetch` subcommand optionally requires `requests`:

```bash
pip install claudiness[fetch]
```

## License

MIT
