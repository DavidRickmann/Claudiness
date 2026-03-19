# Update AI Writing Style Fingerprints

You are updating the `.style` fingerprint files for the Claudiness project — a multi-model AI writing style detector.

## Your task

1. **Research current AI writing patterns** by searching the web for:
   - AI writing detection research (academic papers, blog posts)
   - Model-specific vocabulary and stylistic quirks (Claude, ChatGPT, Gemini, Grok, Llama, DeepSeek, Mistral, etc.)
   - AI detector methodologies (what patterns they look for)
   - Comparative analyses of AI model outputs
   - Community observations about AI writing tells

2. **Review the existing `.style` files** in `src/claudiness/styles/` to understand the current patterns and format.

3. **Update existing `.style` files** with:
   - New regex patterns discovered from research
   - Adjusted weights if evidence suggests current weights are off
   - Removed patterns that are no longer distinctive (models change over time)

4. **Create new `.style` files** for any AI models not yet covered, if you find enough distinctive patterns to make a useful fingerprint. Use the naming convention `YYYY-MM-DD_ModelName.style`.

## .style file format

Each `.style` file is JSON with this structure:

```json
{
  "$schema_version": "1.0",
  "model": "lowercase_id",
  "family": "model_family",
  "display_name": "Human-Readable Name (Company)",
  "date": "YYYY-MM-DD",
  "scoring": { "normalization_base": 500, "min_word_count": 30 },
  "categories": {
    "category_key": {
      "display_name": "Human-readable category name",
      "patterns": ["\\bregex patterns\\b", "..."],
      "match_mode": "anywhere",
      "weight": 20,
      "multiplier": 5,
      "direction": "positive"
    }
  },
  "structural": {
    "enabled": true,
    "weight": 15,
    "rules": [
      { "feature": "bullet_ratio", "thresholds": [{"max": 0.1, "points": 5}] }
    ]
  },
  "bonuses": {
    "conversational_tone": { "enabled": true, "weight": 10, "multiplier": 0.3 }
  },
  "labels": [
    {"min": 80, "label": "Peak ModelName"},
    {"min": 60, "label": "Very ModelName-like"},
    {"min": 40, "label": "Noticeably ModelName-like"},
    {"min": 20, "label": "Mild ModelName tendencies"},
    {"min": 0, "label": "Not particularly ModelName-like"}
  ]
}
```

### Key rules for patterns

- Patterns are Python regex strings (double-escaped in JSON: `\\b` not `\b`)
- `match_mode`: `"anywhere"` uses `re.findall()` on full text; `"line_start"` uses `re.match()` on each paragraph/sentence start
- `direction`: `"positive"` means this pattern is a signal FOR this model; `"negative"` means it's an anti-signal (penalty)
- The same pattern can appear in multiple `.style` files with different directions (e.g., ChatGPT vocabulary is positive in ChatGPT.style but negative in Claude.style)
- `weight` is the max points a category can contribute
- Final score formula per category: `min(normalized_count * multiplier, weight)` where `normalized_count = raw_matches * (500 / word_count)`
- Total score is clamped to 0-100

### Structural features available

The `structural.rules` can reference these features from `analyse_structure()`:
- `bullet_ratio` — fraction of lines that are bullet/list items
- `em_dash_rate` — em-dashes per 100 words
- `parenthetical_rate` — parenthetical asides per 200 words
- `avg_sentence_length` — mean words per sentence
- `sentence_length_variance` — std dev of sentence lengths
- `heading_density` — fraction of lines that are markdown headings

### Quality guidelines

- Only include patterns that are **distinctive** to a model — not just "words AI uses" but words *this specific model* uses more than others
- Prefer patterns with word boundaries (`\b`) to avoid false matches
- Keep patterns case-insensitive (the matching engine lowercases and uses `re.IGNORECASE`)
- A good fingerprint should score its own model's output >60 and other models' output <30
- Test after updating: `python3 claudiness.py --text "..." --verbose`

## After updating

1. Run the tests: `python3 -m unittest tests.test_scoring -v`
2. Test with sample text from each model to verify discrimination works
3. Update the `date` field in any modified `.style` files to today's date
