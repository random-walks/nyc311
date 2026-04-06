"""Download (optional) + catalogue + figures — convenience wrapper around ``download.py`` + ``analyze.py``."""

from __future__ import annotations

from parsers import build_main_parser

from analyze import run_analyze
from download import run_download


def main() -> None:
    args = build_main_parser().parse_args()
    if not args.skip_download:
        run_download(args)
    run_analyze(args)


if __name__ == "__main__":
    main()
