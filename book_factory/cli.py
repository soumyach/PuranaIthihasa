"""Command-line interface for the Book Factory Director."""

import argparse
import json
from pathlib import Path

from .director import FactoryDirector
from .errors import FactoryError


def build_parser():
    parser = argparse.ArgumentParser(prog="factory", description="Khatakshetra Book Factory Foundation PR1")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--catalogue", help="explicit catalogue path (intended for offline fixtures and validation)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="show factory capabilities and blockers")
    subparsers.add_parser("list-books", help="list authoritative catalogue records")
    readiness = subparsers.add_parser("check-readiness", help="run graph and readiness checks")
    readiness.add_argument("--book-id")
    produce = subparsers.add_parser("produce-next", help="select the next eligible book")
    produce.add_argument("--dry-run", action="store_true")
    resume = subparsers.add_parser("resume", help="inspect resumable state without fabricating work")
    resume.add_argument("--book-id", required=True)
    subparsers.add_parser("validate", help="validate foundation contracts and the source graph")
    subparsers.add_parser("next", help="alias for a dry-run next-book selection")
    return parser


def run(args):
    director = FactoryDirector(Path(args.root), args.catalogue)
    if args.command == "status":
        return director.status()
    if args.command == "list-books":
        return director.list_books()
    if args.command == "check-readiness":
        return director.check_readiness(args.book_id)
    if args.command == "produce-next":
        return director.produce_next(args.dry_run)
    if args.command == "resume":
        return director.resume(args.book_id)
    if args.command == "validate":
        return director.validate()
    if args.command == "next":
        return director.produce_next(True)
    raise AssertionError("unreachable")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except FactoryError as exc:
        print(json.dumps({
            "status": "ERROR",
            "code": exc.code,
            "message": str(exc),
            "details": exc.details,
        }, indent=2, sort_keys=True, ensure_ascii=False))
        return 2
