"""Web fetch workflow for discovering and assembling .style files."""

import json
import os
import re
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# Curated sources for AI writing style patterns
CURATED_SOURCES = [
    {
        "url": "https://aidetectors.io/claude-detection",
        "model": "claude",
        "description": "Claude-specific detection patterns",
    },
    {
        "url": "https://aidetectors.io/chatgpt-detection",
        "model": "chatgpt",
        "description": "ChatGPT-specific detection patterns",
    },
]


def _fetch_url(url, timeout=15):
    """Fetch a URL and return its text content."""
    headers = {
        'User-Agent': 'claudiness/2.0 (AI writing style detector)',
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or 'utf-8'
            return resp.read().decode(charset)
    except (URLError, OSError) as e:
        print(f"  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def _search_duckduckgo(query, max_results=5):
    """Scrape DuckDuckGo HTML results for a query. Returns list of URLs."""
    encoded = query.replace(' ', '+')
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    html = _fetch_url(url)
    if not html:
        return []

    # Extract result URLs from DDG HTML
    urls = re.findall(r'href="(https?://[^"]+)"', html)
    # Filter out DDG's own URLs
    results = []
    for u in urls:
        if 'duckduckgo.com' in u:
            continue
        if u not in results:
            results.append(u)
        if len(results) >= max_results:
            break
    return results


def _user_styles_dir():
    """Return the user config styles directory, creating it if needed."""
    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    d = Path(config_home) / "claudiness" / "styles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _extract_patterns_from_text(text, model=None):
    """
    Attempt to extract stylistic patterns from fetched web content.

    This is a best-effort heuristic that looks for quoted phrases,
    pattern lists, and vocabulary sections in the fetched content.

    Returns a list of extracted phrase strings (not regex patterns).
    """
    phrases = []

    # Look for quoted phrases that might be AI writing markers
    quoted = re.findall(r'"([^"]{5,60})"', text)
    phrases.extend(quoted[:50])

    # Look for items in lists (markdown-style)
    list_items = re.findall(r'^\s*[-*]\s+(.{5,80})', text, re.MULTILINE)
    phrases.extend(list_items[:50])

    return phrases


def run_fetch(model=None, url=None, search=False):
    """
    Run the fetch workflow.

    Args:
        model: Filter to fetch only for this model.
        url: A specific URL to fetch from.
        search: If True, also search DuckDuckGo.
    """
    print("Claudiness Fetch - Updating style fingerprints")
    print("=" * 50)

    urls_to_fetch = []

    # Curated sources
    for source in CURATED_SOURCES:
        if model and source['model'] != model.lower():
            continue
        urls_to_fetch.append(source)

    # User-provided URL
    if url:
        urls_to_fetch.append({
            'url': url,
            'model': model or 'unknown',
            'description': 'User-provided URL',
        })

    # DuckDuckGo search
    if search:
        queries = [
            f"AI writing style patterns {model or ''}",
            f"AI detector {model or 'Claude ChatGPT'} vocabulary",
        ]
        for q in queries:
            print(f"\n  Searching: {q}")
            found_urls = _search_duckduckgo(q.strip())
            for u in found_urls:
                urls_to_fetch.append({
                    'url': u,
                    'model': model or 'unknown',
                    'description': f'Search result for: {q.strip()}',
                })

    if not urls_to_fetch:
        print("\n  No sources to fetch. Use --url or --search to find sources.")
        return

    print(f"\n  Found {len(urls_to_fetch)} source(s) to process.")

    fetched_data = {}
    for source in urls_to_fetch:
        src_url = source['url']
        src_model = source.get('model', 'unknown')
        print(f"\n  Fetching: {src_url}")
        content = _fetch_url(src_url)
        if content:
            phrases = _extract_patterns_from_text(content, src_model)
            if phrases:
                if src_model not in fetched_data:
                    fetched_data[src_model] = []
                fetched_data[src_model].extend(phrases)
                print(f"    Extracted {len(phrases)} potential patterns")
            else:
                print("    No patterns extracted")
        else:
            print("    Fetch failed")

    # Report results
    out_dir = _user_styles_dir()
    print(f"\n  Output directory: {out_dir}")

    if not fetched_data:
        print("\n  No patterns were extracted. The bundled .style files are still available.")
        return

    for model_name, phrases in fetched_data.items():
        unique_phrases = list(dict.fromkeys(phrases))  # deduplicate preserving order
        print(f"\n  {model_name}: {len(unique_phrases)} unique phrases extracted")
        print(f"    These phrases can be reviewed and added to a .style file manually.")

        # Save raw extracted data as a reference file
        ref_path = out_dir / f"fetched_{model_name}_raw.json"
        with open(ref_path, 'w', encoding='utf-8') as f:
            json.dump({
                'model': model_name,
                'extracted_phrases': unique_phrases[:100],
                'note': 'Raw extracted phrases. Review and convert to regex patterns for a .style file.',
            }, f, indent=2)
        print(f"    Saved to: {ref_path}")

    print("\n  Done. Review extracted data and update .style files as needed.")
    print("  Bundled .style files remain as the primary fingerprints.")
