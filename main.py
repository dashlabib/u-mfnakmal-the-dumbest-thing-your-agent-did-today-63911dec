#!/usr/bin/env python3
"""Publish the one-line entry for the make.fun bounty
"The Dumbest Thing Your Agent Did Today".

The line lives in ``entry.txt`` next to this file. The program is
split into three small stages so each one can be checked on its own:

1. ``load_line`` reads the raw bytes and decodes them as UTF-8.
2. ``validate`` checks the text against the bounty gate: it must be
   a single line, 1 to 200 characters (or the ``--max-chars`` value),
   not only white space, with no control characters.
3. ``publish`` writes the exact bytes to ``entry.txt`` in the output
   directory and reads them back to confirm the published bytes
   match the stored file.

Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.

The output directory is ``$MAKEFUN_OUTPUT_DIR`` when set, else
``/output``. Pass ``--output-dir <dir>`` to choose it on the
command line instead, ``--verify-only`` to check the line without
writing anything, ``--max-chars <n>`` to tighten (or loosen) the
length gate, and ``--quiet`` to suppress the success messages.
"""

import argparse
import os
import sys
from pathlib import Path

DEFAULT_MAX_CHARS = 200
DEFAULT_OUTPUT_DIR = "/output"


def load_raw_bytes(entry_path: Path | None = None) -> bytes:
    """Read entry.txt exactly as stored, trailing newline included."""
    path = entry_path or Path(__file__).resolve().parent / "entry.txt"
    return path.read_bytes()


def load_line(entry_path: Path | None = None) -> str:
    """Read entry.txt as UTF-8 and strip surrounding white space."""
    path = entry_path or Path(__file__).resolve().parent / "entry.txt"
    raw = path.read_bytes()
    return raw.decode("utf-8").strip()


def check_length(text: str, max_chars: int) -> list[str]:
    """Return a list of length-gate problems (empty when it passes)."""
    problems = []
    if not text or text.isspace():
        problems.append("entry is empty or only white space")
    if len(text) > max_chars:
        problems.append(
            f"entry is {len(text)} characters, over the {max_chars} limit"
        )
    return problems


def check_single_line(text: str) -> list[str]:
    """Return a list of single-line problems (empty when it passes)."""
    problems = []
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    bad = [c for c in text if ord(c) < 0x20 and c not in "\t"]
    if bad:
        problems.append(f"entry contains control character U+{ord(bad[0]):04X}")
    return problems


def validate(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> None:
    """Raise SystemExit naming every gate problem, or return silently."""
    problems = check_length(text, max_chars) + check_single_line(text)
    if problems:
        raise SystemExit("; ".join(problems))


def resolve_output_dir(args) -> Path:
    """Command-line flag wins, then $MAKEFUN_OUTPUT_DIR, then /output."""
    if args.output_dir:
        return Path(args.output_dir)
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))


def publish(raw: bytes, out_dir: Path) -> Path:
    """Write the raw entry.txt bytes verbatim and read them back.

    Publishing the raw bytes (trailing newline included) keeps the
    output byte-identical to entry.txt, which ``cmp`` verifies.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.txt"
    out_path.write_bytes(raw)
    if out_path.read_bytes() != raw:
        raise SystemExit("published entry does not match entry.txt")
    return out_path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None,
                        help="directory to write entry.txt into")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate the line without writing it")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                        help="maximum allowed characters (default: 200)")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress success messages")
    return parser.parse_args(argv)


def run(args) -> int:
    """Validate, then either report validity or publish the line."""
    text = load_line()
    validate(text, max_chars=args.max_chars)
    if args.verify_only:
        if not args.quiet:
            print(f"Valid: {len(text)} characters")
        return 0
    out_path = publish(load_raw_bytes(), resolve_output_dir(args))
    if not args.quiet:
        print(f"Wrote {len(text)} characters to {out_path}")
        print(text)
    return 0


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
