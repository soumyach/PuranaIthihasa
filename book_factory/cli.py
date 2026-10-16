"""Command-line interface for the Book Factory Director."""

import argparse
import json
from pathlib import Path

from .director import FactoryDirector
from .errors import FactoryError


def build_parser():
    parser = argparse.ArgumentParser(prog="factory", description="Khatakshetra Book Factory Foundation PR6")
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
    subparsers.add_parser("missing-inputs", help="show the exact authoritative-input inventory")
    dossier = subparsers.add_parser("source-dossier", help="build a source-readiness dossier")
    dossier.add_argument("--book-id", required=True)
    dossier.add_argument("--write", action="store_true", help="persist an immutable dossier version")
    packet = subparsers.add_parser("story-packet", help="build a story packet from one graph spine")
    packet.add_argument("--spine-id", required=True)
    evaluate = subparsers.add_parser("evaluate-catalogue", help="reconcile mappings and rank controlled-pilot candidates")
    evaluate.add_argument("--write", action="store_true")
    prepare = subparsers.add_parser("prepare-pilot", help="store the source dossier and Story Packet only")
    prepare.add_argument("--book-id", required=True)
    draft = subparsers.add_parser("draft-manuscript", help="build a provider request without using the interactive model")
    draft.add_argument("--book-id", required=True)
    draft.add_argument("--dry-run", action="store_true")
    review = subparsers.add_parser("review-manuscript", help="check independent editorial-review capability")
    review.add_argument("--book-id", required=True)
    clearance = subparsers.add_parser("import-source-clearance", help="validate and store a private-draft source clearance")
    clearance.add_argument("--book-id", required=True)
    clearance.add_argument("--record", required=True)
    manuscript_handoff = subparsers.add_parser("prepare-manuscript-handoff", help="prepare a locked Codex manuscript-agent request")
    manuscript_handoff.add_argument("--book-id", required=True)
    manuscript_handoff.add_argument("--revision-review-hash")
    manuscript_handoff.add_argument("--pr5-quality-revision", action="store_true")
    import_manuscript = subparsers.add_parser("import-manuscript-handoff", help="validate and store a Codex manuscript-agent response")
    import_manuscript.add_argument("--book-id", required=True)
    import_manuscript.add_argument("--handoff", required=True)
    import_manuscript.add_argument("--response", required=True)
    review_handoff = subparsers.add_parser("prepare-review-handoff", help="prepare a locked independent-review request")
    review_handoff.add_argument("--book-id", required=True)
    review_handoff.add_argument("--perspective", choices=["SOURCE_FIDELITY", "LITERARY_EXPERIENCE"])
    import_review = subparsers.add_parser("import-review-handoff", help="validate and store an independent-review response")
    import_review.add_argument("--book-id", required=True)
    import_review.add_argument("--handoff", required=True)
    import_review.add_argument("--response", required=True)
    manuscript_status = subparsers.add_parser("manuscript-status", help="show separated DM04 production dimensions")
    manuscript_status.add_argument("--book-id", required=True)
    preproduction_handoff = subparsers.add_parser("prepare-preproduction-handoff", help="prepare locked bibles, storyboard, typography and proof-spec request")
    preproduction_handoff.add_argument("--book-id", required=True)
    import_preproduction = subparsers.add_parser("import-preproduction-handoff", help="validate and store a visual-preproduction specialist response")
    import_preproduction.add_argument("--book-id", required=True)
    import_preproduction.add_argument("--handoff", required=True)
    import_preproduction.add_argument("--response", required=True)
    subparsers.add_parser("image-capabilities", help="report discovered and authorized image backends")
    prepare_proof = subparsers.add_parser("prepare-proof-generation", help="persist a locked zero-cost proof-generation intent")
    prepare_proof.add_argument("--book-id", required=True)
    prepare_proof.add_argument("--proof-id", required=True)
    import_proof = subparsers.add_parser("import-proof-image", help="validate and import real generated proof pixels")
    import_proof.add_argument("--book-id", required=True)
    import_proof.add_argument("--request", required=True)
    import_proof.add_argument("--image", required=True)
    import_proof.add_argument("--provider-receipt", required=True)
    prepare_visual = subparsers.add_parser("prepare-visual-review", help="prepare independent exact-image review")
    prepare_visual.add_argument("--book-id", required=True)
    prepare_visual.add_argument("--proof-id", required=True)
    import_visual = subparsers.add_parser("import-visual-review", help="import independent pixel-inspection review")
    import_visual.add_argument("--book-id", required=True)
    import_visual.add_argument("--handoff", required=True)
    import_visual.add_argument("--response", required=True)
    contact_sheet = subparsers.add_parser("build-proof-contact-sheet", help="build an internal contact sheet from real proofs")
    contact_sheet.add_argument("--book-id", required=True)
    style_approval = subparsers.add_parser("prepare-style-approval", help="freeze the proof package for human style approval")
    style_approval.add_argument("--book-id", required=True)
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
    if args.command == "missing-inputs":
        return director.input_report()
    if args.command == "source-dossier":
        return director.source_dossier(args.book_id, args.write)
    if args.command == "story-packet":
        return director.story_packet(args.spine_id)
    if args.command == "evaluate-catalogue":
        return director.evaluate_catalogue(args.write)
    if args.command == "prepare-pilot":
        return director.prepare_pilot(args.book_id)
    if args.command == "draft-manuscript":
        return director.draft_manuscript(args.book_id, args.dry_run)
    if args.command == "review-manuscript":
        return director.review_manuscript(args.book_id)
    if args.command == "import-source-clearance":
        return director.import_source_clearance(args.book_id, args.record)
    if args.command == "prepare-manuscript-handoff":
        return director.prepare_manuscript_handoff(
            args.book_id, args.revision_review_hash, args.pr5_quality_revision
        )
    if args.command == "import-manuscript-handoff":
        return director.import_manuscript_handoff(args.book_id, args.handoff, args.response)
    if args.command == "prepare-review-handoff":
        return director.prepare_review_handoff(args.book_id, args.perspective)
    if args.command == "import-review-handoff":
        return director.import_review_handoff(args.book_id, args.handoff, args.response)
    if args.command == "manuscript-status":
        return director.manuscript_status(args.book_id)
    if args.command == "prepare-preproduction-handoff":
        return director.prepare_preproduction_handoff(args.book_id)
    if args.command == "import-preproduction-handoff":
        return director.import_preproduction_handoff(args.book_id, args.handoff, args.response)
    if args.command == "image-capabilities":
        return director.image_capabilities()
    if args.command == "prepare-proof-generation":
        return director.prepare_proof_generation(args.book_id, args.proof_id)
    if args.command == "import-proof-image":
        return director.import_proof_image(args.book_id, args.request, args.image, args.provider_receipt)
    if args.command == "prepare-visual-review":
        return director.prepare_visual_review(args.book_id, args.proof_id)
    if args.command == "import-visual-review":
        return director.import_visual_review(args.book_id, args.handoff, args.response)
    if args.command == "build-proof-contact-sheet":
        return director.build_proof_contact_sheet(args.book_id)
    if args.command == "prepare-style-approval":
        return director.prepare_style_approval(args.book_id)
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
