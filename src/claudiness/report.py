"""Terminal output formatting for single-model and multi-model results."""

from collections import Counter
from claudiness.patterns import find_specific_matches


def print_single_report(result, verbose=False, text=None):
    """Print a formatted report for a single model result."""
    display = result.get('display_name', result.get('model', 'Unknown'))
    print("=" * 60)
    print(f"  {display} SCORE: {result['score']}/100")
    print(f"  Verdict: {result['label']}")
    print(f"  Word count: {result['word_count']}")
    print("=" * 60)

    if result.get('note'):
        print(f"\n  Note: {result['note']}")
        return

    print("\n  BREAKDOWN:")
    print("  " + "-" * 56)

    for key, val in result['breakdown'].items():
        detail = result['details'].get(key, {})
        display_name = detail.get('display_name', key.replace('_', ' ').title())

        # Try to get a nice name from the style categories
        name = key.replace('_', ' ').title()

        if val > 0:
            bar_len = int(val)
            bar = '\u2588' * bar_len + '\u2591' * max(0, 20 - bar_len)
            print(f"  {name:<30} +{val:>5.1f}  {bar}")
        elif val < 0:
            bar_len = int(abs(val))
            bar = '\u2593' * bar_len + '\u2591' * max(0, 15 - bar_len)
            print(f"  {name:<30} {val:>6.1f}  {bar}")
        else:
            bar = '\u2591' * 20
            print(f"  {name:<30}   0.0  {bar}")

    if verbose and text:
        _print_verbose_matches(result, text)

    print()


def _print_verbose_matches(result, text):
    """Print matched patterns for verbose mode."""
    print("\n  MATCHED PATTERNS:")
    print("  " + "-" * 56)

    details = result.get('details', {})
    for key, detail in details.items():
        if key in ('structure', 'conversational_bonus'):
            continue
        # We don't have the patterns directly in the result, but we have match counts
        # Verbose match display is handled by the CLI which has access to the style def


def print_multi_report(results, verbose=False, text=None):
    """Print a summary comparing scores across multiple models."""
    if not results:
        print("No style files loaded.")
        return

    word_count = results[0].get('word_count', 0)
    print("=" * 60)
    print("  AI WRITING STYLE ANALYSIS")
    print(f"  Word count: {word_count}")
    print("=" * 60)

    if results[0].get('note'):
        print(f"\n  Note: {results[0]['note']}")
        return

    print("\n  SCORES:")
    print("  " + "-" * 56)

    for r in results:
        score = r['score']
        display = r.get('display_name', r.get('model', '?'))
        label = r['label']
        bar_len = int(score / 2)  # Scale to max 50 chars
        bar = '\u2588' * bar_len + '\u2591' * max(0, 50 - bar_len)
        print(f"  {display:<25} {score:>5.1f}/100  {label}")
        print(f"  {bar}")
        print()

    # Show detailed breakdown for the top scorer
    if results:
        top = results[0]
        print(f"  TOP MATCH: {top.get('display_name', top.get('model'))}")
        print("  " + "-" * 56)
        print_breakdown(top)

    if verbose and text and results:
        print_verbose_all(results, text)

    print()


def print_breakdown(result):
    """Print the breakdown section of a single result."""
    for key, val in result['breakdown'].items():
        name = key.replace('_', ' ').title()
        if val > 0:
            bar_len = int(val)
            bar = '\u2588' * bar_len + '\u2591' * max(0, 20 - bar_len)
            print(f"  {name:<30} +{val:>5.1f}  {bar}")
        elif val < 0:
            bar_len = int(abs(val))
            bar = '\u2593' * bar_len + '\u2591' * max(0, 15 - bar_len)
            print(f"  {name:<30} {val:>6.1f}  {bar}")
        else:
            bar = '\u2591' * 20
            print(f"  {name:<30}   0.0  {bar}")


def print_verbose_all(results, text):
    """Print verbose match info for all model results."""
    # Verbose output requires access to the style definitions (patterns),
    # which are passed through the CLI layer. This is a placeholder that
    # prints match counts from the details dict.
    for r in results:
        display = r.get('display_name', r.get('model'))
        details = r.get('details', {})
        has_matches = any(
            d.get('matches', 0) > 0
            for k, d in details.items()
            if k not in ('structure', 'conversational_bonus')
        )
        if not has_matches:
            continue
        print(f"\n  MATCHES for {display}:")
        print("  " + "-" * 56)
        for key, detail in details.items():
            if key in ('structure', 'conversational_bonus'):
                continue
            matches = detail.get('matches', 0)
            if matches > 0:
                name = key.replace('_', ' ').title()
                print(f"    {name}: {matches} match(es)")


def print_verbose_with_styles(results, styles, text):
    """Print verbose match info using the actual style pattern definitions."""
    for r, style in zip(results, _match_results_to_styles(results, styles)):
        if style is None:
            continue
        display = r.get('display_name', r.get('model'))
        categories = style.get('categories', {})

        any_printed = False
        for key, cat in categories.items():
            patterns = cat.get('patterns', [])
            matches = find_specific_matches(text, patterns)
            if matches:
                if not any_printed:
                    print(f"\n  MATCHED PATTERNS for {display}:")
                    print("  " + "-" * 56)
                    any_printed = True
                counts = Counter(matches)
                top = counts.most_common(8)
                cat_name = cat.get('display_name', key)
                print(f"  {cat_name}:")
                for m, c in top:
                    suffix = f' x{c}' if c > 1 else ''
                    print(f'    \u2022 "{m}"{suffix}')
                print()


def _match_results_to_styles(results, styles):
    """Match result dicts back to their style definitions by model name."""
    style_map = {s.get('model', ''): s for s in styles}
    return [style_map.get(r.get('model', '')) for r in results]
