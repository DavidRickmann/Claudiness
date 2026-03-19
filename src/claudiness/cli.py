"""CLI entry point with subcommands for the claudiness tool."""

import argparse
import json
import sys

from claudiness.style_loader import discover_styles, list_models
from claudiness.scoring import score_text, score_text_all_models
from claudiness.report import (
    print_single_report, print_multi_report, print_verbose_with_styles,
)


def _preprocess_argv(argv):
    """
    Translate shorthand -<word> (e.g. -claude) into --model <word>.

    Only applies when <word> is alphabetic, >1 char, and not a known flag.
    """
    known_short_flags = {'-t', '-v', '-j', '-s', '-h'}
    result = []
    for arg in argv:
        if (arg.startswith('-')
                and not arg.startswith('--')
                and arg not in known_short_flags
                and len(arg) > 2
                and arg[1:].isalpha()):
            result.extend(['--model', arg[1:]])
        else:
            result.append(arg)
    return result


def _get_text(args, parser):
    """Extract text from args.text, args.file, or stdin."""
    if args.text:
        return args.text
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            return f.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def cmd_analyse(args, parser):
    """Handle the default analyse command."""
    text = _get_text(args, parser)
    if text is None:
        parser.print_help()
        print("\nExamples:")
        print('  claudiness essay.txt')
        print('  claudiness essay.txt --model claude')
        print('  claudiness essay.txt -claude')
        print('  claudiness --text "That\'s a great question. I think..."')
        print('  echo "some text" | claudiness')
        print('  claudiness essay.txt --verbose')
        sys.exit(1)

    style_dirs = [args.style_dir] if args.style_dir else None
    styles = discover_styles(style_dirs=style_dirs, model_filter=args.model)

    if not styles:
        print(f"No style files found{' for model ' + repr(args.model) if args.model else ''}.",
              file=sys.stderr)
        sys.exit(1)

    if len(styles) == 1:
        result = score_text(text, styles[0])
        if args.score_only:
            print(result['score'])
        elif args.json:
            print(json.dumps(result, indent=2))
        else:
            print_single_report(result, verbose=args.verbose, text=text)
            if args.verbose:
                print_verbose_with_styles([result], styles, text)
    else:
        results = score_text_all_models(text, styles)
        if args.score_only:
            for r in results:
                print(f"{r['model']}: {r['score']}")
        elif args.json:
            print(json.dumps(results, indent=2))
        else:
            print_multi_report(results, verbose=args.verbose, text=text)
            if args.verbose:
                print_verbose_with_styles(results, styles, text)


def cmd_fetch(args):
    """Handle the fetch subcommand."""
    from claudiness.fetch import run_fetch
    run_fetch(
        model=getattr(args, 'model', None),
        url=getattr(args, 'url', None),
        search=getattr(args, 'search', False),
    )


def cmd_list_models(args):
    """Handle the list-models subcommand."""
    style_dirs = [args.style_dir] if hasattr(args, 'style_dir') and args.style_dir else None
    models = list_models(style_dirs=style_dirs)
    if not models:
        print("No style files found.")
        return
    print(f"{'Model':<15} {'Display Name':<25} {'Date':<12} {'Categories':<5} Path")
    print("-" * 80)
    for m in models:
        print(f"{m['model']:<15} {m['display_name']:<25} {m['date']:<12} {m['categories']:<5} {m['path']}")


def _build_analyse_parser():
    """Build the parser for the default analyse command."""
    parser = argparse.ArgumentParser(
        prog='claudiness',
        description='Multi-model AI writing style detector.',
        epilog='Reads from file, stdin, or use --text for inline text.',
    )
    parser.add_argument('file', nargs='?', help='Text file to analyse')
    parser.add_argument('--text', '-t', help='Inline text to analyse')
    parser.add_argument('--model', help='Filter to a specific model family')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show specific matched patterns')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--score-only', '-s', action='store_true',
                        help='Output just the score(s)')
    parser.add_argument('--style-dir', help='Additional style directory')
    return parser


def _build_fetch_parser():
    """Build the parser for the fetch subcommand."""
    parser = argparse.ArgumentParser(
        prog='claudiness fetch',
        description='Fetch/update style fingerprints.',
    )
    parser.add_argument('--model', help='Only fetch for this model')
    parser.add_argument('--url', help='Fetch from a specific URL')
    parser.add_argument('--search', action='store_true',
                        help='Search DuckDuckGo for new sources')
    return parser


def _build_list_models_parser():
    """Build the parser for the list-models subcommand."""
    parser = argparse.ArgumentParser(
        prog='claudiness list-models',
        description='Show loaded .style files.',
    )
    parser.add_argument('--style-dir', help='Additional style directory')
    return parser


SUBCOMMANDS = {'fetch', 'list-models'}


def main(argv=None):
    """Main CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    argv = _preprocess_argv(argv)

    # Route to subcommand if the first non-flag arg is a known subcommand
    command = None
    for arg in argv:
        if arg.startswith('-'):
            continue
        if arg in SUBCOMMANDS:
            command = arg
            argv = argv[argv.index(arg) + 1:]
        break

    if command == 'fetch':
        args = _build_fetch_parser().parse_args(argv)
        cmd_fetch(args)
    elif command == 'list-models':
        args = _build_list_models_parser().parse_args(argv)
        cmd_list_models(args)
    else:
        parser = _build_analyse_parser()
        args = parser.parse_args(argv)
        cmd_analyse(args, parser)


if __name__ == '__main__':
    main()
