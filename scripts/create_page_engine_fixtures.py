#!/usr/bin/env python3
"""Create deterministic, obviously synthetic renderer fixtures and their manifest."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from book_factory.page_engine import FIXTURE_LABEL, lettering_source_hash
from book_factory.util import atomic_json_write, content_hash, load_json, sha256_bytes


FIXTURES = ROOT / "book-factory" / "fixtures" / "page-engine"
ASSETS = FIXTURES / "assets"
FONT_CONFIG = ROOT / "book-factory" / "config" / "page-renderer-fonts.json"


def font(size, bold=False):
    preferred = Path("/System/Library/Fonts/Supplemental/STIXGeneralBol.otf" if bold else "/System/Library/Fonts/Supplemental/STIXGeneral.otf")
    if preferred.is_file():
        return ImageFont.truetype(str(preferred), size)
    import reportlab
    name = "VeraBd.ttf" if bold else "Vera.ttf"
    return ImageFont.truetype(str(Path(reportlab.__file__).parent / "fonts" / name), size)


def asset(name, subtitle, colors, motif):
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / (name + ".png")
    image = Image.new("RGB", (1086, 1448), colors[0])
    draw = ImageDraw.Draw(image)
    for index in range(12):
        inset = 34 + index * 38
        draw.rounded_rectangle((inset, inset, 1086 - inset, 1448 - inset), radius=40, outline=colors[index % len(colors)], width=8)
    if motif == "dialogue":
        draw.ellipse((160, 360, 440, 720), fill=colors[1], outline="#F0CF76", width=10)
        draw.ellipse((646, 620, 926, 980), fill=colors[2], outline="#F0CF76", width=10)
    elif motif == "action":
        for offset in range(-200, 1300, 150):
            draw.line((offset, 1160, offset + 500, 250), fill=colors[(offset // 150) % len(colors)], width=24)
        draw.polygon(((543, 260), (820, 850), (543, 1160), (270, 850)), fill=colors[1], outline="#F0CF76")
    elif motif == "immersive":
        for radius in range(520, 30, -45):
            shade = colors[(radius // 45) % len(colors)]
            draw.ellipse((543 - radius, 724 - radius, 543 + radius, 724 + radius), fill=shade)
        draw.polygon(((543, 230), (750, 1090), (543, 1260), (335, 1090)), fill="#F0CF76")
    else:
        draw.rounded_rectangle((120, 290, 966, 1150), radius=28, fill="#F6E8C6", outline="#D8AC4E", width=12)
        for y in range(410, 1040, 95):
            draw.line((220, y, 866, y), fill="#692019", width=8)
    draw.rectangle((0, 0, 1086, 150), fill="#692019")
    draw.text((543, 54), "SYNTHETIC NON-PRODUCTION FIXTURE", font=font(35, True), fill="#FFF9EF", anchor="ma")
    draw.rectangle((0, 1275, 1086, 1448), fill="#071F35")
    draw.text((543, 1310), subtitle, font=font(38, True), fill="#F0CF76", anchor="ma")
    draw.text((543, 1370), "NOT APPROVED ART • TEST GEOMETRY ONLY", font=font(25), fill="#FFF9EF", anchor="ma")
    image.save(path, format="PNG", optimize=False, compress_level=9)
    return path


def lettering(item):
    item["source_script_hash"] = lettering_source_hash(item)
    return item


def panel(page, order, asset_path, speakers):
    return {
        "panel_id": "fixture-p%02d-panel-%02d" % (page, order), "reading_order": order,
        "asset": {
            "path": asset_path.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(asset_path.read_bytes()),
            "usage": "SYNTHETIC_TEST_ONLY", "approval": {"status": "NOT_APPLICABLE_FIXTURE", "subject_hash": sha256_bytes(asset_path.read_bytes())},
        },
        "crop": {"mode": "COVER", "focal_point": {"x": 0.5, "y": 0.5}, "protected_subjects": speakers},
        "speaker_anchors": [{"speaker_id": speaker, "x": x, "y": y} for speaker, x, y in speakers],
    }


def page(number, layout, page_title, panels, lettering_items):
    return {
        "schema_version": "1.0", "book_id": "DM04-RENDERER-FIXTURE", "book_version": "PR8-TECHNICAL-DEMO",
        "manuscript_hash": load_json(ROOT / "books" / "DM04" / "manuscripts" / "v0005.json")["content_hash"],
        "storyboard_hash": load_json(ROOT / "books" / "DM04" / "storyboards" / "v0003.json")["content_hash"],
        "page_id": "dm04-renderer-fixture-page-%02d" % number, "page_number": number, "reading_order": number,
        "chapter_masthead": "PR8 TECHNICAL FIXTURE", "page_title": page_title,
        "layout_type": layout, "panels": panels, "lettering": lettering_items,
        "required_lettering_ids": [item["lettering_id"] for item in lettering_items],
        "typography": {"family": None, "title_size": 34, "body_size": 28},
        "series_standard": {"id": "KHATAKSHETRA_NAVY_GOLD_3X4", "palette": ["#071F35", "#D8AC4E", "#F0CF76", "#F6E8C6", "#FFF9EF", "#251C18", "#692019"]},
        "approvals": {"manuscript": {"status": "FIXTURE_ONLY"}, "storyboard": {"status": "FIXTURE_ONLY"}, "series_standard": {"status": "FIXTURE_ONLY"}},
        "fixture": True, "publication_eligible": False, "non_production_label": FIXTURE_LABEL,
    }


def main():
    dialog = asset("dialogue-geometry", "DIALOGUE-HEAVY TEST ASSET", ("#153D59", "#7C4660", "#315F68"), "dialogue")
    action = asset("action-geometry", "MIXED-PANEL ACTION TEST ASSET", ("#0D3047", "#8B3A38", "#3E6D61"), "action")
    immersive = asset("immersive-geometry", "FULL-PAGE IMMERSIVE TEST ASSET", ("#09263E", "#74516A", "#2D666A"), "immersive")
    note = asset("source-note-geometry", "REFLECTION / SOURCE-NOTE TEST ASSET", ("#17354D", "#F6E8C6", "#D8AC4E"), "note")
    p1_panels = [panel(1, 1, dialog, [("fixture-speaker-a", 0.28, 0.38), ("fixture-speaker-b", 0.72, 0.42)]), panel(1, 2, dialog, [("fixture-speaker-a", 0.28, 0.76), ("fixture-speaker-b", 0.72, 0.80)])]
    p1_text = [
        lettering({"lettering_id": "fixture-p01-n01", "channel": "NARRATION", "text": "A compact narration plaque establishes the technical scene without repeating the dialogue.", "speaker_id": "narrator", "panel_id": p1_panels[0]["panel_id"], "reading_order": 1, "badge_number": 1, "box": {"x": 0.07, "y": 0.13, "width": 0.42, "height": 0.11}, "font": {"size": 26, "minimum_size": 22}}),
        lettering({"lettering_id": "fixture-p01-d01", "channel": "DIALOGUE", "text": "Does every word remain editable after the art is placed?", "speaker_id": "fixture-speaker-b", "panel_id": p1_panels[0]["panel_id"], "reading_order": 2, "box": {"x": 0.54, "y": 0.25, "width": 0.34, "height": 0.13}, "font": {"size": 28, "minimum_size": 22}}),
        lettering({"lettering_id": "fixture-p01-d02", "channel": "DIALOGUE", "text": "Yes. The script, geometry, font and tail anchor remain separate records.", "speaker_id": "fixture-speaker-a", "panel_id": p1_panels[1]["panel_id"], "reading_order": 3, "box": {"x": 0.08, "y": 0.58, "width": 0.38, "height": 0.15}, "font": {"size": 27, "minimum_size": 22}}),
        lettering({"lettering_id": "fixture-p01-d03", "channel": "DIALOGUE", "text": "Then a layout repair does not regenerate the illustration.", "speaker_id": "fixture-speaker-b", "panel_id": p1_panels[1]["panel_id"], "reading_order": 4, "box": {"x": 0.55, "y": 0.58, "width": 0.34, "height": 0.14}, "font": {"size": 27, "minimum_size": 22}}),
    ]
    p2_panels = [panel(2, index, action, [("fixture-actor", 0.50, 0.29 + index * 0.16)]) for index in range(1, 4)]
    p2_text = [
        lettering({"lettering_id": "fixture-p02-n01", "channel": "NARRATION", "text": "A wide opening beat gives way to two asymmetric reaction panels.", "speaker_id": "narrator", "panel_id": p2_panels[0]["panel_id"], "reading_order": 1, "badge_number": 1, "box": {"x": 0.07, "y": 0.13, "width": 0.45, "height": 0.10}, "font": {"size": 26, "minimum_size": 22}}),
        lettering({"lettering_id": "fixture-p02-d01", "channel": "DIALOGUE", "text": "The reading order remains explicit.", "speaker_id": "fixture-actor", "panel_id": p2_panels[1]["panel_id"], "reading_order": 2, "box": {"x": 0.10, "y": 0.60, "width": 0.35, "height": 0.12}, "font": {"size": 27, "minimum_size": 22}}),
    ]
    p3_panels = [panel(3, 1, immersive, [("fixture-observer", 0.50, 0.63)])]
    p3_text = [lettering({"lettering_id": "fixture-p03-n01", "channel": "NARRATION", "text": "The immersive template protects a large uninterrupted image field.", "speaker_id": "narrator", "panel_id": p3_panels[0]["panel_id"], "reading_order": 1, "badge_number": 1, "box": {"x": 0.08, "y": 0.77, "width": 0.45, "height": 0.10}, "font": {"size": 26, "minimum_size": 22}})]
    p4_panels = [panel(4, 1, note, [])]
    p4_text = [
        lettering({"lettering_id": "fixture-p04-i01", "channel": "INSET_EXPLANATION", "text": "TECHNICAL SOURCE NOTE\nThis page demonstrates a distinct expository channel. Its wording is fixture text, not scripture and not an editorial claim about DM04.", "speaker_id": "editorial-inset", "panel_id": p4_panels[0]["panel_id"], "reading_order": 1, "box": {"x": 0.10, "y": 0.20, "width": 0.80, "height": 0.27}, "font": {"size": 29, "minimum_size": 22, "weight": "bold"}}),
        lettering({"lettering_id": "fixture-p04-n01", "channel": "NARRATION", "text": "Reflection pages remain readable, restrained and separately editable.", "speaker_id": "narrator", "panel_id": p4_panels[0]["panel_id"], "reading_order": 2, "badge_number": 1, "box": {"x": 0.16, "y": 0.58, "width": 0.68, "height": 0.13}, "font": {"size": 27, "minimum_size": 22}}),
    ]
    pages = [
        page(1, "TWO_PANEL_SEQUENTIAL", "DIALOGUE-HEAVY PAGE TEST", p1_panels, p1_text),
        page(2, "MIXED_WIDE_NARROW", "MIXED-PANEL ACTION TEST", p2_panels, p2_text),
        page(3, "SINGLE_PANEL_IMMERSIVE", "FULL-PAGE IMMERSIVE TEST", p3_panels, p3_text),
        page(4, "REFLECTION_SOURCE_NOTE", "REFLECTION / SOURCE-NOTE TEST", p4_panels, p4_text),
    ]
    manifest = {
        "schema_version": "1.0", "book_id": "DM04-RENDERER-FIXTURE", "title": FIXTURE_LABEL,
        "fixture": True, "publication_eligible": False, "pages": pages,
        "provenance": "Deterministic synthetic geometry generated locally; no AI image service and no reference-page reproduction.",
    }
    manifest["fixture_manifest_hash"] = content_hash(manifest)
    atomic_json_write(FIXTURES / "demo-book.json", manifest)
    print(FIXTURES / "demo-book.json")


if __name__ == "__main__":
    main()
