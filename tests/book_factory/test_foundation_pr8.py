import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from book_factory.director import FactoryDirector
from book_factory.errors import BlockedError, ContractError
from book_factory.page_engine import (
    CANVAS,
    LAYOUT_TYPES,
    FontResolver,
    _cover_crop,
    _fit_text,
    _layout_boxes,
    _wrap,
    compose_book,
    compose_page,
    expected_panel_count,
    export_pdf,
    inspect_pdf,
    lettering_source_hash,
    repair_page,
    validate_page_spec,
    validate_rendered_page,
)
from book_factory.util import content_hash, load_json, sha256_bytes
from book_factory.versioning import PageCompositionVersionStore


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "book-factory" / "fixtures" / "page-engine" / "demo-book.json"
FONT_CONFIG = ROOT / "book-factory" / "config" / "page-renderer-fonts.json"


class PageEnginePR8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.manifest = load_json(FIXTURE)
        cls.composed = compose_book(deepcopy(cls.manifest), ROOT, cls.output / "pages", True, FONT_CONFIG)
        cls.composed_manifest = load_json(Path(cls.composed["manifest"]))
        cls.pdf = export_pdf(cls.composed_manifest, cls.output / "fixture.pdf", True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, index=0):
        return deepcopy(self.manifest["pages"][index])

    def codes(self, report):
        return {item["code"] for item in report["findings"]}

    def test_01_each_supported_layout_type(self):
        counts = {name: expected_panel_count(name) for name in LAYOUT_TYPES}
        self.assertEqual(set(counts), set(LAYOUT_TYPES))
        self.assertEqual(counts["FOUR_PANEL_GRID"], 4)
        self.assertEqual(counts["TWO_PAGE_SPREAD"], 1)
        self.assertTrue(all(_layout_boxes(name) for name in LAYOUT_TYPES))
        base = self.page(2)
        source_panel = deepcopy(base["panels"][0])
        for layout_name, count in counts.items():
            spec = deepcopy(base)
            spec["page_id"] = "layout-fixture-%s" % layout_name.lower()
            spec["layout_type"] = layout_name
            spec["panels"] = []
            for order in range(1, count + 1):
                item = deepcopy(source_panel)
                item["panel_id"] = "%s-panel-%02d" % (spec["page_id"], order)
                item["reading_order"] = order
                spec["panels"].append(item)
            spec["lettering"] = []
            spec["required_lettering_ids"] = []
            rendered = compose_page(spec, ROOT, self.output / "layouts" / layout_name.lower(), True, FONT_CONFIG)
            self.assertEqual(rendered["status"], "PASS")

    def test_02_exact_lettering_preservation(self):
        original = self.manifest["pages"][0]["lettering"]
        composition = load_json(Path(self.composed["pages"][0]["composition"]))
        self.assertEqual([item["text"] for item in composition["lettering"]], [item["text"] for item in original])
        self.assertTrue(all(item["source_script_hash"] == lettering_source_hash(item) for item in original))

    def test_03_text_wrapping(self):
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (300, 100))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FontResolver(FONT_CONFIG).resolve()["regular"], 24)
        lines = _wrap(draw, "one two three four five six", font, 120)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines), "one two three four five six")

    def test_04_minimum_font_size(self):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (400, 200))
        draw = ImageDraw.Draw(image)
        font_path = FontResolver(FONT_CONFIG).resolve()["regular"]
        _, _, size, _, _ = _fit_text(draw, "exact words remain exact", font_path, 31, 22, (0, 0, 180, 80), 8)
        self.assertGreaterEqual(size, 22)

    def test_05_missing_font_behavior(self):
        path = self.output / "missing-fonts.json"
        path.write_text(json.dumps({"candidates": [{"family": "Missing", "regular": "/missing/a.ttf", "bold": "/missing/b.ttf"}]}), encoding="utf-8")
        with self.assertRaises(BlockedError):
            FontResolver(path).resolve("Missing")

    def test_06_correct_speaker_tail_references(self):
        spec = self.page()
        spec["panels"][0]["speaker_anchors"] = []
        self.assertIn("SPEAKER_TAIL_REFERENCE", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_07_speaker_anchor_not_hidden_by_balloon(self):
        spec = self.page()
        item = next(value for value in spec["lettering"] if value["channel"] == "DIALOGUE")
        anchor = next(value for value in spec["panels"][0]["speaker_anchors"] if value["speaker_id"] == item["speaker_id"])
        anchor.update({"x": item["box"]["x"] + 0.01, "y": item["box"]["y"] + 0.01})
        self.assertIn("SPEAKER_ANCHOR_OCCLUDED", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_08_narration_badge_numbering(self):
        spec = self.page()
        next(item for item in spec["lettering"] if item["channel"] == "NARRATION")["badge_number"] = 4
        self.assertIn("NARRATION_SEQUENCE", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_09_panel_reading_order(self):
        spec = self.page()
        spec["panels"][1]["reading_order"] = 1
        self.assertIn("PANEL_READING_ORDER", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_10_image_aspect_ratio_preservation(self):
        composition = load_json(Path(self.composed["pages"][1]["composition"]))
        for panel in composition["resolved_panels"]:
            source_crop = panel["source_crop"]
            box = panel["box"]
            source_ratio = (source_crop[2] - source_crop[0]) / (source_crop[3] - source_crop[1])
            target_ratio = (box[2] - box[0] - 10) / (box[3] - box[1] - 10)
            self.assertAlmostEqual(source_ratio, target_ratio, places=2)
            self.assertEqual(panel["scale_mode"], "ASPECT_PRESERVING_COVER")

    def test_11_full_page_artwork_support(self):
        result = self.composed["pages"][2]
        composition = load_json(Path(result["composition"]))
        self.assertEqual(composition["layout_type"], "SINGLE_PANEL_IMMERSIVE")
        self.assertEqual(len(composition["resolved_panels"]), 1)

    def test_12_crop_boundaries(self):
        crop = _cover_crop((800, 600), (200, 400), {"x": 1.0, "y": 0.0})
        self.assertGreaterEqual(min(crop), 0)
        self.assertLessEqual(crop[2], 800)
        self.assertLessEqual(crop[3], 600)
        spec = self.page()
        spec["panels"][0]["crop"]["focal_point"]["x"] = 2
        self.assertIn("CROP_BOUNDS", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_12b_crop_zoom_is_bounded_and_preserves_aspect(self):
        base = _cover_crop((800, 600), (400, 200), {"x": 0.75, "y": 0.5})
        zoomed = _cover_crop((800, 600), (400, 200), {"x": 0.75, "y": 0.5}, 2.0)
        self.assertLess(zoomed[2] - zoomed[0], base[2] - base[0])
        self.assertLess(zoomed[3] - zoomed[1], base[3] - base[1])
        self.assertAlmostEqual((zoomed[2] - zoomed[0]) / (zoomed[3] - zoomed[1]), 2.0, places=2)

    def test_13_layout_collision_detection(self):
        spec = self.page()
        spec["lettering"][1]["box"] = deepcopy(spec["lettering"][0]["box"])
        self.assertIn("LETTERING_COLLISION", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_14_text_overflow(self):
        spec = self.page(2)
        item = spec["lettering"][0]
        item["text"] = "word " * 500
        item["box"] = {"x": 0.1, "y": 0.2, "width": 0.12, "height": 0.06}
        item["source_script_hash"] = lettering_source_hash(item)
        with self.assertRaisesRegex(ContractError, "overflowed"):
            compose_page(spec, ROOT, self.output / "overflow", True, FONT_CONFIG)

    def test_14b_optional_lettering_padding_is_bounded_and_recorded(self):
        spec = self.page(2)
        spec["lettering"][0]["padding"] = 16
        rendered = compose_page(spec, ROOT, self.output / "compact-padding", True, FONT_CONFIG)
        composition = load_json(Path(rendered["composition"]))
        self.assertEqual(composition["resolved_lettering"][0]["padding"], 16)
        spec["lettering"][0]["padding"] = 0
        self.assertIn("LETTERING_PADDING", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))
        spec["lettering"][0]["padding"] = 16.5
        self.assertIn("LETTERING_PADDING", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_15_page_id_uniqueness(self):
        manifest = deepcopy(self.manifest)
        manifest["pages"][1]["page_id"] = manifest["pages"][0]["page_id"]
        with self.assertRaisesRegex(ContractError, "duplicate page IDs"):
            compose_book(manifest, ROOT, self.output / "duplicates", True, FONT_CONFIG)

    def test_16_pdf_page_ordering(self):
        report = inspect_pdf(self.pdf["pdf_path"], self.composed_manifest)
        self.assertEqual(report["page_order"], [item["page_id"] for item in self.composed_manifest["pages"]])

    def test_17_pdf_page_count(self):
        report = inspect_pdf(self.pdf["pdf_path"], self.composed_manifest)
        self.assertEqual(report["page_count"], 4)

    def test_18_pdf_orientation_and_dimensions(self):
        report = inspect_pdf(self.pdf["pdf_path"], self.composed_manifest)
        self.assertTrue(all(item["orientation"] == "PORTRAIT" for item in report["pages"]))
        self.assertTrue(all(round(item["width"]) == CANVAS["width"] and round(item["height"]) == CANVAS["height"] for item in report["pages"]))

    def test_19_duplicate_page_detection(self):
        manifest = deepcopy(self.composed_manifest)
        manifest["pages"] = [deepcopy(manifest["pages"][0]), deepcopy(manifest["pages"][0])]
        manifest["pages"][1].update({"page_number": 2, "reading_order": 2, "page_id": "different-id"})
        manifest["manifest_hash"] = content_hash({key: value for key, value in manifest.items() if key != "manifest_hash"})
        with self.assertRaisesRegex(ContractError, "duplicate pages"):
            export_pdf(manifest, self.output / "duplicate.pdf", True)

    def test_20_artifact_hash_integrity(self):
        composition = load_json(Path(self.composed["pages"][0]["composition"]))
        metadata = load_json(Path(self.composed["pages"][0]["metadata"]))
        metadata["rendered_png_sha256"] = "0" * 64
        self.assertIn("ARTIFACT_HASH_MISMATCH", self.codes(validate_rendered_page(composition, metadata, ROOT, True)))

    def test_21_approval_gate_enforcement(self):
        spec = self.page()
        spec["fixture"] = False
        spec["publication_eligible"] = False
        report = validate_page_spec(spec, ROOT, False, FONT_CONFIG)
        self.assertIn("MISSING_APPROVAL", self.codes(report))

    def test_22_fixture_production_isolation(self):
        spec = self.page()
        spec["publication_eligible"] = True
        self.assertIn("FIXTURE_PROMOTION", self.codes(validate_page_spec(spec, ROOT, True, FONT_CONFIG)))

    def test_23_rejected_pr6_art_cannot_pass_production_gate(self):
        spec = self.page()
        pr6 = ROOT / "books" / "DM04" / "illustration-proofs" / "images" / "dm04-proof-quiet-conversation" / "attempt-02-578e0fcdb4dcf016.png"
        spec["fixture"] = False
        spec["publication_eligible"] = False
        spec["book_id"] = "DM04"
        spec["panels"][0]["asset"] = {
            "path": pr6.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(pr6.read_bytes()),
            "usage": "REJECTED_PR6_LOCAL_VALIDATION_ONLY", "approval": {"status": "FIX", "subject_hash": sha256_bytes(pr6.read_bytes())},
        }
        self.assertIn("MISSING_APPROVAL", self.codes(validate_page_spec(spec, ROOT, False, FONT_CONFIG)))
        with self.assertRaisesRegex(ContractError, "existing reference editions"):
            FactoryDirector(ROOT)._page_engine_gate("DM08", "LETTERING", False)

    def test_24_page_local_repair(self):
        composition = load_json(Path(self.composed["pages"][0]["composition"]))
        lettering = deepcopy(composition["lettering"])
        lettering[0]["box"]["x"] += 0.01
        repaired = repair_page(composition, {"lettering": lettering}, ["BALLOON_COLLISION"])
        self.assertEqual(repaired["manuscript_hash"], composition["manuscript_hash"])
        self.assertEqual(repaired["storyboard_hash"], composition["storyboard_hash"])
        self.assertNotEqual(repaired["composition_hash"], composition["composition_hash"])
        self.assertEqual(repaired["repair_history"][-1]["failure_causes"], ["BALLOON_COLLISION"])
        store = PageCompositionVersionStore(self.output / "version-books")
        first = store.put("TEST", composition["page_id"], composition)
        second = store.put("TEST", repaired["page_id"], repaired, first["content_hash"])
        self.assertEqual([item["version"] for item in store.versions("TEST", composition["page_id"])], [1, 2])
        self.assertEqual(second["parent_hash"], first["content_hash"])
        with self.assertRaises(ContractError):
            repair_page(composition, {"manuscript_hash": "changed"})

    def test_25_private_preview_is_labeled_and_not_production_approved(self):
        spec = self.page()
        spec["fixture"] = False
        spec["private_preview"] = True
        spec["publication_eligible"] = False
        spec["non_production_label"] = "INTERNAL PREVIEW — NOT APPROVED FOR PUBLICATION"
        for panel in spec["panels"]:
            panel["asset"]["usage"] = "PRIVATE_INTERNAL_DIAGNOSTIC"
            panel["asset"]["approval"] = {"status": "FIX", "subject_hash": panel["asset"]["sha256"]}
        subjects = {
            "manuscript": spec["manuscript_hash"],
            "storyboard": spec["storyboard_hash"],
            "series_standard": content_hash(spec["series_standard"]),
        }
        spec["approvals"] = {
            key: {"status": "LOCKED_FOR_PRIVATE_PREVIEW", "subject_hash": value}
            for key, value in subjects.items()
        }
        preview = validate_page_spec(spec, ROOT, False, FONT_CONFIG, True)
        self.assertEqual(preview["result"], "PASS")
        self.assertIn("MISSING_APPROVAL", self.codes(validate_page_spec(spec, ROOT, False, FONT_CONFIG)))

    def test_25_idempotent_resume(self):
        director = FactoryDirector(ROOT)
        path = self.composed["pages"][0]["composition"]
        first = director.resume_layout("DM04-RENDERER-FIXTURE", path, None, True)
        second = director.resume_layout("DM04-RENDERER-FIXTURE", path, None, True)
        self.assertEqual(first, second)
        self.assertFalse(first["mutated"])

    def test_26_source_graph_immutability(self):
        graph = ROOT / "research" / "source-graph"
        before = content_hash({path.relative_to(graph).as_posix(): sha256_bytes(path.read_bytes()) for path in sorted(graph.rglob("*")) if path.is_file()})
        FactoryDirector(ROOT).validate_page(self.composed["pages"][0]["composition"], True)
        after = content_hash({path.relative_to(graph).as_posix(): sha256_bytes(path.read_bytes()) for path in sorted(graph.rglob("*")) if path.is_file()})
        self.assertEqual(before, after)

    def test_27_existing_factory_regression_validation(self):
        result = FactoryDirector(ROOT).validate()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_graph"]["passed"])


if __name__ == "__main__":
    unittest.main()
