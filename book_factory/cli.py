"""Command-line interface for the Book Factory Director."""

import argparse
import json
from pathlib import Path

from .director import FactoryDirector
from .errors import FactoryError


def _fixture_arguments(parser):
    parser.add_argument("--fixture-mode", action="store_true", help="use isolated, publication-ineligible acceptance fixtures")
    parser.add_argument("--fixture-plan", help="explicit synthetic lifecycle plan (requires --fixture-mode)")


def build_parser():
    parser = argparse.ArgumentParser(prog="factory", description="Khatakshetra Book Factory controlled visual pilot PR11")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--catalogue", help="explicit catalogue path (intended for offline fixtures and validation)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="show factory capabilities and blockers")
    subparsers.add_parser("list-books", help="list authoritative catalogue records")
    readiness = subparsers.add_parser("check-readiness", help="run graph and readiness checks")
    readiness.add_argument("--book-id")
    produce = subparsers.add_parser("produce-next", help="select the next eligible book")
    produce.add_argument("--dry-run", action="store_true")
    _fixture_arguments(produce)
    produce_book = subparsers.add_parser("produce-book", help="start or continue the supported workflow for one exact book")
    produce_book.add_argument("--book-id", required=True)
    _fixture_arguments(produce_book)
    resume_book = subparsers.add_parser("resume-book", help="idempotently resume one durable orchestration run")
    resume_book.add_argument("--book-id", required=True)
    _fixture_arguments(resume_book)
    production_slice = subparsers.add_parser("prepare-production-slice", help="prepare the locked DM04 PR10 two-page campaign")
    production_slice.add_argument("--book-id", required=True)
    production_status = subparsers.add_parser("production-slice-status", help="inspect the real DM04 PR10 slice without executing art")
    production_status.add_argument("--book-id", required=True)
    campaign_approval = subparsers.add_parser("import-production-campaign-approval", help="import a separate exact-hash PR10 human authorization")
    campaign_approval.add_argument("--book-id", required=True)
    campaign_approval.add_argument("--approval", required=True)
    production_generation = subparsers.add_parser("prepare-production-generation", help="prepare one authorized reference-conditioned host request")
    production_generation.add_argument("--book-id", required=True)
    production_generation.add_argument("--page-id", required=True)
    production_image = subparsers.add_parser("import-production-image", help="import one exact authorized PR11 host image and execution receipt")
    production_image.add_argument("--book-id", required=True)
    production_image.add_argument("--page-id", required=True)
    production_image.add_argument("--request", required=True)
    production_image.add_argument("--image", required=True)
    production_image.add_argument("--provider-receipt", required=True)
    production_review = subparsers.add_parser("prepare-production-visual-review", help="prepare independent actual-pixel review for one PR11 image")
    production_review.add_argument("--book-id", required=True)
    production_review.add_argument("--page-id", required=True)
    import_production_review = subparsers.add_parser("import-production-visual-review", help="import one independent PR11 actual-pixel review")
    import_production_review.add_argument("--book-id", required=True)
    import_production_review.add_argument("--page-id", required=True)
    import_production_review.add_argument("--request", required=True)
    import_production_review.add_argument("--response", required=True)
    for command, help_text in (
        ("queue", "show deterministic queue selection and skip reasons"),
        ("blocked", "show exact blocked and excluded catalogue entries"),
        ("approvals", "show persisted and pending approvals"),
        ("costs", "show estimated and actual orchestration costs"),
    ):
        control = subparsers.add_parser(command, help=help_text)
        control.add_argument("--fixture-mode", action="store_true")
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
    gold = subparsers.add_parser("visual-gold-standard", help="verify the curated actual-page visual benchmark")
    gold.add_argument("--require-source-assets", action="store_true", help="fail unless both exact local benchmark PDFs are present")
    recovery = subparsers.add_parser("prepare-proof-recovery", help="persist four non-executable PR8 recovery requests")
    recovery.add_argument("--book-id", required=True)
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
    compose_page = subparsers.add_parser("compose-page", help="render one approved page composition")
    compose_page.add_argument("--spec", required=True)
    compose_page.add_argument("--output-dir", required=True)
    compose_page.add_argument("--fixture-mode", action="store_true")
    validate_page = subparsers.add_parser("validate-page", help="validate an editable or rendered page composition")
    validate_page.add_argument("--source", required=True)
    validate_page.add_argument("--fixture-mode", action="store_true")
    compose_book = subparsers.add_parser("compose-book", help="compose an explicitly ordered set of pages")
    compose_book.add_argument("--manifest", required=True)
    compose_book.add_argument("--output-dir", required=True)
    compose_book.add_argument("--fixture-mode", action="store_true")
    export_pdf = subparsers.add_parser("export-pdf", help="export one native page raster per PDF page")
    export_pdf.add_argument("--manifest", required=True)
    export_pdf.add_argument("--output", required=True)
    export_pdf.add_argument("--fixture-mode", action="store_true")
    inspect_pdf = subparsers.add_parser("inspect-pdf", help="inspect page count, order, dimensions and embedded pixels")
    inspect_pdf.add_argument("--pdf", required=True)
    inspect_pdf.add_argument("--manifest")
    inspect_pdf.add_argument("--fixture-mode", action="store_true")
    resume_layout = subparsers.add_parser("resume-layout", help="resume from the latest immutable composition without re-rendering")
    resume_layout.add_argument("--book-id", required=True)
    resume_layout.add_argument("--composition")
    resume_layout.add_argument("--page-id")
    resume_layout.add_argument("--fixture-mode", action="store_true")
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
        if args.fixture_plan and not args.fixture_mode:
            raise FactoryError("--fixture-plan requires --fixture-mode")
        return director.produce_next(args.dry_run, args.fixture_mode, args.fixture_plan)
    if args.command == "produce-book":
        if args.fixture_plan and not args.fixture_mode:
            raise FactoryError("--fixture-plan requires --fixture-mode")
        return director.produce_book(args.book_id, args.fixture_mode, args.fixture_plan)
    if args.command == "resume-book":
        if args.fixture_plan and not args.fixture_mode:
            raise FactoryError("--fixture-plan requires --fixture-mode")
        return director.resume_book(args.book_id, args.fixture_mode, args.fixture_plan)
    if args.command == "prepare-production-slice":
        return director.prepare_production_slice(args.book_id)
    if args.command == "production-slice-status":
        return director.production_slice_status(args.book_id)
    if args.command == "import-production-campaign-approval":
        return director.import_production_campaign_approval(args.book_id, args.approval)
    if args.command == "prepare-production-generation":
        return director.prepare_production_generation(args.book_id, args.page_id)
    if args.command == "import-production-image":
        return director.import_production_image(
            args.book_id, args.page_id, args.request, args.image, args.provider_receipt
        )
    if args.command == "prepare-production-visual-review":
        return director.prepare_production_visual_review(args.book_id, args.page_id)
    if args.command == "import-production-visual-review":
        return director.import_production_visual_review(
            args.book_id, args.page_id, args.request, args.response
        )
    if args.command == "queue":
        return director.factory_queue(args.fixture_mode)
    if args.command == "blocked":
        return director.factory_blocked(args.fixture_mode)
    if args.command == "approvals":
        return director.factory_approvals(args.fixture_mode)
    if args.command == "costs":
        return director.factory_costs(args.fixture_mode)
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
    if args.command == "visual-gold-standard":
        return director.visual_gold_standard(args.require_source_assets)
    if args.command == "prepare-proof-recovery":
        return director.prepare_proof_recovery(args.book_id)
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
    if args.command == "compose-page":
        return director.compose_page(args.spec, args.output_dir, args.fixture_mode)
    if args.command == "validate-page":
        return director.validate_page(args.source, args.fixture_mode)
    if args.command == "compose-book":
        return director.compose_book(args.manifest, args.output_dir, args.fixture_mode)
    if args.command == "export-pdf":
        return director.export_pdf(args.manifest, args.output, args.fixture_mode)
    if args.command == "inspect-pdf":
        return director.inspect_pdf(args.pdf, args.manifest, args.fixture_mode)
    if args.command == "resume-layout":
        return director.resume_layout(args.book_id, args.composition, args.page_id, args.fixture_mode)
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
