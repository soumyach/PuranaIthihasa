"""Deterministic comic-page composition, lettering, validation and PDF export.

The JSON composition is the editable authority. Raster pages and PDFs are
derivatives.  This module deliberately has no image-generation capability.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

from .errors import BlockedError, ContractError
from .util import atomic_json_write, content_hash, load_json, sha256_bytes


ENGINE_VERSION = "0.8.2"
CANVAS = {"width": 1086, "height": 1448, "aspect_ratio": "3:4"}
SPREAD_CANVAS = {"width": 2172, "height": 1448, "aspect_ratio": "3:2"}
PALETTE = {
    "midnight_navy": "#071F35",
    "antique_gold": "#D8AC4E",
    "bright_gold": "#F0CF76",
    "parchment": "#F6E8C6",
    "speech_white": "#FFF9EF",
    "ink": "#251C18",
    "burgundy": "#692019",
}
CROP_MODES = ("COVER", "CONTAIN")
LAYOUT_TYPES = (
    "TWO_PANEL_SEQUENTIAL",
    "THREE_PANEL",
    "FOUR_PANEL_GRID",
    "MIXED_WIDE_NARROW",
    "CINEMATIC_HERO",
    "SINGLE_PANEL_IMMERSIVE",
    "QUIET_NEAR_SILENT",
    "COVER",
    "REFLECTION_SOURCE_NOTE",
    "TWO_PAGE_SPREAD",
)
TEXT_CHANNELS = ("NARRATION", "DIALOGUE", "THOUGHT", "INSET_EXPLANATION")
FIXTURE_LABEL = "KHATAKSHETRA BOOK FACTORY — NON-PRODUCTION RENDERER TEST"
PRIVATE_PREVIEW_LABEL = "INTERNAL PREVIEW — NOT APPROVED FOR PUBLICATION"
MIN_BODY_FONT_SIZE = 22
MIN_TITLE_FONT_SIZE = 28


def _imaging():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - exercised in dependency-free environments
        raise BlockedError(
            "page rendering requires the Pillow package",
            {"install": "python -m pip install 'Pillow>=10,<13'", "dependency": "Pillow"},
        ) from exc
    return Image, ImageDraw, ImageFont


def _pdf_libraries():
    try:
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise BlockedError(
            "PDF export requires reportlab and pypdf",
            {"install": "python -m pip install 'reportlab>=4,<5' 'pypdf>=5,<7'"},
        ) from exc
    return ImageReader, canvas, PdfReader


def _hex(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def _repository_asset_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ContractError("asset path escapes the repository", {"path": relative})
    return path


def _pixel_hash(path):
    Image, _, _ = _imaging()
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return sha256_bytes(rgb.tobytes())


def _normal_box(box, width, height):
    if not isinstance(box, dict) or any(key not in box for key in ("x", "y", "width", "height")):
        raise ContractError("geometry requires x, y, width and height")
    values = [box[key] for key in ("x", "y", "width", "height")]
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        raise ContractError("geometry values must be numeric")
    x, y, w, h = values
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
        raise ContractError("normalized geometry is out of bounds", {"geometry": box})
    return (
        int(round(x * width)), int(round(y * height)),
        int(round((x + w) * width)), int(round((y + h) * height)),
    )


def _intersects(a, b, padding=0):
    return not (
        a[2] + padding <= b[0] or b[2] + padding <= a[0]
        or a[3] + padding <= b[1] or b[3] + padding <= a[1]
    )


def _inside(inner, outer):
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _layout_boxes(layout_type):
    """Return normalized page-panel geometry, leaving masthead/footer margins."""
    x, y, w, h, g = 0.045, 0.105, 0.91, 0.82, 0.018
    half_w, half_h = (w - g) / 2, (h - g) / 2
    if layout_type == "TWO_PANEL_SEQUENTIAL":
        return [{"x": x, "y": y, "width": w, "height": half_h},
                {"x": x, "y": y + half_h + g, "width": w, "height": half_h}]
    if layout_type == "THREE_PANEL":
        top_h = h * 0.52
        return [{"x": x, "y": y, "width": w, "height": top_h},
                {"x": x, "y": y + top_h + g, "width": half_w, "height": h - top_h - g},
                {"x": x + half_w + g, "y": y + top_h + g, "width": half_w, "height": h - top_h - g}]
    if layout_type == "FOUR_PANEL_GRID":
        return [{"x": x + col * (half_w + g), "y": y + row * (half_h + g),
                 "width": half_w, "height": half_h} for row in range(2) for col in range(2)]
    if layout_type == "MIXED_WIDE_NARROW":
        wide_h = h * 0.44
        narrow_h = h - wide_h - g
        left_w = w * 0.58
        return [{"x": x, "y": y, "width": w, "height": wide_h},
                {"x": x, "y": y + wide_h + g, "width": left_w, "height": narrow_h},
                {"x": x + left_w + g, "y": y + wide_h + g, "width": w - left_w - g, "height": narrow_h}]
    if layout_type == "CINEMATIC_HERO":
        hero_w = w * 0.68
        return [{"x": x, "y": y, "width": hero_w, "height": h},
                {"x": x + hero_w + g, "y": y, "width": w - hero_w - g, "height": half_h},
                {"x": x + hero_w + g, "y": y + half_h + g, "width": w - hero_w - g, "height": half_h}]
    if layout_type in {"SINGLE_PANEL_IMMERSIVE", "QUIET_NEAR_SILENT", "COVER", "REFLECTION_SOURCE_NOTE"}:
        return [{"x": x, "y": y, "width": w, "height": h}]
    if layout_type == "TWO_PAGE_SPREAD":
        return [{"x": 0.023, "y": y, "width": 0.954, "height": h}]
    raise ContractError("unknown page layout", {"layout_type": layout_type})


def expected_panel_count(layout_type):
    return len(_layout_boxes(layout_type))


def lettering_source_hash(item):
    return content_hash({
        "lettering_id": item.get("lettering_id"),
        "text": item.get("text"),
        "speaker_id": item.get("speaker_id"),
        "panel_id": item.get("panel_id"),
        "channel": item.get("channel"),
        "reading_order": item.get("reading_order"),
    })


class FontResolver:
    """Resolve configured fonts without treating installation as license clearance."""

    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else None

    @staticmethod
    def _reportlab_font(name):
        try:
            import reportlab
        except ImportError:
            return None
        path = Path(reportlab.__file__).parent / "fonts" / name
        return path if path.is_file() else None

    def candidates(self):
        configured = load_json(self.config_path).get("candidates", []) if self.config_path and self.config_path.is_file() else []
        if configured:
            return configured
        return [
            {
                "family": "STIXGeneral",
                "classification": "serif",
                "regular": "/System/Library/Fonts/Supplemental/STIXGeneral.otf",
                "bold": "/System/Library/Fonts/Supplemental/STIXGeneralBol.otf",
                "license_status": "SYSTEM_FONT_LICENSE_REVIEWED_NOT_REDISTRIBUTED",
            },
            {
                "family": "Bitstream Vera",
                "classification": "sans-serif-fallback",
                "regular": "REPORTLAB:Vera.ttf",
                "bold": "REPORTLAB:VeraBd.ttf",
                "license_status": "REDISTRIBUTABLE_REPORTLAB_DEPENDENCY",
            },
        ]

    def _path(self, value):
        if value.startswith("REPORTLAB:"):
            return self._reportlab_font(value.split(":", 1)[1])
        path = Path(os.path.expandvars(value)).expanduser()
        return path if path.is_file() else None

    def resolve(self, requested_family=None):
        for candidate in self.candidates():
            if requested_family and candidate["family"] != requested_family:
                continue
            regular, bold = self._path(candidate["regular"]), self._path(candidate["bold"])
            if regular and bold:
                result = dict(candidate)
                result.update({
                    "regular": str(regular.resolve()), "bold": str(bold.resolve()),
                    "regular_sha256": _sha256_file(regular), "bold_sha256": _sha256_file(bold),
                    "font_binary_bundled_in_repository": False,
                })
                return result
        raise BlockedError(
            "no configured licensed font is available",
            {"requested_family": requested_family, "config": str(self.config_path) if self.config_path else None},
        )


def _add_finding(findings, code, reason, page_id=None, panel_id=None, element_id=None, severity="FIX"):
    findings.append({
        "severity": severity, "code": code, "page_id": page_id,
        "panel_id": panel_id, "element_id": element_id, "reason": reason,
    })


def validate_page_spec(spec, repository_root, fixture_mode=False, font_config=None, private_preview=False):
    findings = []
    page_id = spec.get("page_id")
    required = (
        "book_id", "book_version", "manuscript_hash", "storyboard_hash", "page_id",
        "page_number", "reading_order", "layout_type", "panels", "lettering",
        "required_lettering_ids", "series_standard", "approvals",
    )
    for field in required:
        if field not in spec:
            _add_finding(findings, "MISSING_FIELD", "required field is absent", page_id, element_id=field)
    layout_type = spec.get("layout_type")
    if layout_type not in LAYOUT_TYPES:
        _add_finding(findings, "UNSUPPORTED_LAYOUT", "layout type is not supported", page_id, element_id=layout_type)
        boxes = []
    else:
        boxes = _layout_boxes(layout_type)
    canvas = SPREAD_CANVAS if layout_type == "TWO_PAGE_SPREAD" else CANVAS
    if spec.get("canvas", canvas) != canvas:
        _add_finding(findings, "INCORRECT_CANVAS", "canvas must match the selected digital template", page_id)
    panels = spec.get("panels", [])
    if boxes and len(panels) != len(boxes):
        _add_finding(findings, "PANEL_COUNT", "panel count does not match layout template", page_id)
    panel_ids = [panel.get("panel_id") for panel in panels]
    if len(panel_ids) != len(set(panel_ids)) or any(not value for value in panel_ids):
        _add_finding(findings, "PANEL_ID_UNIQUENESS", "panel IDs must be present and unique", page_id)
    orders = [panel.get("reading_order") for panel in panels]
    if orders != list(range(1, len(panels) + 1)):
        _add_finding(findings, "PANEL_READING_ORDER", "panel reading order must be explicit and contiguous", page_id)
    root = Path(repository_root)
    for panel in panels:
        panel_id = panel.get("panel_id")
        assetless = panel.get("assetless")
        if assetless is not None:
            if (
                layout_type != "REFLECTION_SOURCE_NOTE"
                or not isinstance(assetless, dict)
                or assetless.get("kind") != "DETERMINISTIC_DECORATIVE_TEXT_BACKGROUND"
            ):
                _add_finding(
                    findings,
                    "ASSETLESS_PANEL_SCOPE",
                    "assetless panels are permitted only for deterministic reflection/source-note back matter",
                    page_id,
                    panel_id,
                )
            continue
        asset = panel.get("asset")
        if not isinstance(asset, dict):
            _add_finding(findings, "MISSING_IMAGE", "panel has no immutable image reference", page_id, panel_id)
            continue
        try:
            path = _repository_asset_path(root, asset.get("path", ""))
        except ContractError as exc:
            _add_finding(findings, "ASSET_PATH_BOUNDARY", str(exc), page_id, panel_id, asset.get("path"))
            continue
        if not path.is_file():
            _add_finding(findings, "MISSING_IMAGE", "referenced image does not exist", page_id, panel_id, asset.get("path"))
            continue
        digest = _sha256_file(path)
        if digest != asset.get("sha256"):
            _add_finding(findings, "ASSET_HASH_MISMATCH", "image bytes do not match the locked hash", page_id, panel_id, asset.get("path"))
        try:
            Image, _, _ = _imaging()
            with Image.open(path) as image:
                width, height = image.size
            if width < 256 or height < 256:
                _add_finding(findings, "IMAGE_RESOLUTION", "image is below the minimum technical fixture resolution", page_id, panel_id)
        except (OSError, BlockedError) as exc:
            _add_finding(findings, "UNREADABLE_IMAGE", str(exc), page_id, panel_id)
        crop = panel.get("crop", {})
        crop_mode = crop.get("mode", "COVER")
        if crop_mode not in CROP_MODES:
            _add_finding(findings, "CROP_MODE", "crop mode must be COVER or CONTAIN", page_id, panel_id)
        focal = crop.get("focal_point", {"x": 0.5, "y": 0.5})
        if not all(isinstance(focal.get(key), (int, float)) and 0 <= focal[key] <= 1 for key in ("x", "y")):
            _add_finding(findings, "CROP_BOUNDS", "focal point must stay inside the source image", page_id, panel_id)
        zoom = crop.get("zoom", 1.0)
        if not isinstance(zoom, (int, float)) or isinstance(zoom, bool) or not 1.0 <= zoom <= 3.0:
            _add_finding(findings, "CROP_ZOOM", "crop zoom must be a number from 1.0 through 3.0", page_id, panel_id)
        elif crop_mode == "CONTAIN" and zoom != 1.0:
            _add_finding(findings, "CROP_ZOOM", "CONTAIN mode requires zoom 1.0", page_id, panel_id)
        approval = asset.get("approval", {})
        if fixture_mode:
            if not spec.get("fixture", False) or asset.get("usage") != "SYNTHETIC_TEST_ONLY":
                _add_finding(findings, "FIXTURE_ISOLATION", "fixture mode accepts only explicitly synthetic test assets", page_id, panel_id)
        elif private_preview:
            if approval.get("status") not in {"FIX", "PRIVATE_PREVIEW_AUTHORIZED"} or approval.get("subject_hash") != digest:
                _add_finding(findings, "MISSING_PREVIEW_AUTHORITY", "private preview image requires an exact hash-bound FIX review or preview authorization", page_id, panel_id)
        elif approval.get("status") != "APPROVED" or approval.get("subject_hash") != digest:
            _add_finding(findings, "MISSING_APPROVAL", "production image requires an exact hash-bound approval", page_id, panel_id)
    lettering = spec.get("lettering", [])
    lettering_ids = [item.get("lettering_id") for item in lettering]
    if len(lettering_ids) != len(set(lettering_ids)) or any(not value for value in lettering_ids):
        _add_finding(findings, "LETTERING_ID_UNIQUENESS", "lettering IDs must be present and unique", page_id)
    required_lettering_ids = spec.get("required_lettering_ids", [])
    if required_lettering_ids != lettering_ids:
        _add_finding(findings, "REQUIRED_LETTERING", "required lettering IDs must exactly match the ordered lettering objects", page_id)
    narrative_badges = []
    resolved_boxes = []
    panel_by_id = {panel.get("panel_id"): panel for panel in panels}
    panel_geometry = {}
    for panel, default_box in zip(panels, boxes):
        try:
            panel_geometry[panel.get("panel_id")] = _normal_box(panel.get("box", default_box), canvas["width"], canvas["height"])
        except ContractError as exc:
            _add_finding(findings, "PANEL_OUT_OF_BOUNDS", str(exc), page_id, panel.get("panel_id"))
    for item in lettering:
        item_id, panel_id = item.get("lettering_id"), item.get("panel_id")
        if item.get("channel") not in TEXT_CHANNELS:
            _add_finding(findings, "TEXT_CHANNEL", "unsupported lettering channel", page_id, panel_id, item_id)
        if not item.get("text"):
            _add_finding(findings, "MISSING_TEXT", "lettering text is empty", page_id, panel_id, item_id)
        if item.get("source_script_hash") != lettering_source_hash(item):
            _add_finding(findings, "LETTERING_HASH", "lettering differs from its exact script hash", page_id, panel_id, item_id)
        padding = item.get("padding")
        if padding is not None and (
            not isinstance(padding, int)
            or isinstance(padding, bool)
            or not 8 <= padding <= 60
        ):
            _add_finding(
                findings,
                "LETTERING_PADDING",
                "optional lettering padding must be an integer from 8 through 60 pixels",
                page_id,
                panel_id,
                item_id,
            )
        tail_max_length = item.get("tail_max_length")
        if tail_max_length is not None and (
            item.get("channel") != "DIALOGUE"
            or not private_preview
            or not isinstance(tail_max_length, int)
            or isinstance(tail_max_length, bool)
            or not 20 <= tail_max_length <= 160
        ):
            _add_finding(
                findings,
                "DIALOGUE_TAIL_LENGTH",
                "optional shortened dialogue tails are limited to 20-160 pixels in private previews",
                page_id,
                panel_id,
                item_id,
            )
        if panel_id not in panel_by_id:
            _add_finding(findings, "LETTERING_PANEL", "lettering refers to a missing panel", page_id, panel_id, item_id)
        if item.get("channel") in {"DIALOGUE", "THOUGHT"}:
            speaker_id = item.get("speaker_id")
            anchors = panel_by_id.get(panel_id, {}).get("speaker_anchors", [])
            matches = [anchor for anchor in anchors if anchor.get("speaker_id") == speaker_id]
            if not speaker_id or len(matches) != 1:
                _add_finding(findings, "SPEAKER_TAIL_REFERENCE", "balloon requires exactly one supplied anchor for its speaker", page_id, panel_id, item_id)
            elif panel_id in panel_geometry:
                anchor = matches[0]
                try:
                    point = (int(anchor["x"] * canvas["width"]), int(anchor["y"] * canvas["height"]))
                    item_box = _normal_box(item.get("box"), canvas["width"], canvas["height"])
                    panel_box = panel_geometry[panel_id]
                    if not (panel_box[0] <= point[0] <= panel_box[2] and panel_box[1] <= point[1] <= panel_box[3]):
                        _add_finding(findings, "SPEAKER_ANCHOR_BOUNDS", "speaker anchor lies outside its panel", page_id, panel_id, item_id)
                    if item_box[0] <= point[0] <= item_box[2] and item_box[1] <= point[1] <= item_box[3]:
                        _add_finding(findings, "SPEAKER_ANCHOR_OCCLUDED", "speaker anchor lies inside its own balloon", page_id, panel_id, item_id)
                except (KeyError, TypeError, ValueError, ContractError):
                    _add_finding(findings, "SPEAKER_ANCHOR_BOUNDS", "speaker anchor coordinates must be normalized numbers", page_id, panel_id, item_id)
        if item.get("channel") == "NARRATION":
            narrative_badges.append(item.get("badge_number"))
        try:
            item_box = _normal_box(item.get("box"), canvas["width"], canvas["height"])
            resolved_boxes.append((item_id, item_box))
            page_band = item.get("placement_scope") == "PAGE_BAND"
            if page_band and (not private_preview or item.get("channel") not in {"NARRATION", "DIALOGUE"}):
                _add_finding(
                    findings,
                    "PAGE_BAND_SCOPE",
                    "page-level text bands are limited to private-preview narration or attributed dialogue",
                    page_id,
                    panel_id,
                    item_id,
                )
            if page_band and any(_intersects(item_box, box, 0) for box in panel_geometry.values()):
                _add_finding(
                    findings,
                    "PAGE_BAND_PANEL_COLLISION",
                    "a page-level narration band must remain outside every art panel",
                    page_id,
                    panel_id,
                    item_id,
                )
            if not page_band and panel_id in panel_geometry and not _inside(item_box, panel_geometry[panel_id]):
                _add_finding(findings, "LETTERING_PANEL_BOUNDARY", "lettering crosses its panel boundary", page_id, panel_id, item_id)
            safe_top, safe_bottom = int(0.095 * canvas["height"]), int(0.93 * canvas["height"])
            if item_box[1] < safe_top or item_box[3] > safe_bottom:
                _add_finding(findings, "LETTERING_RESERVED_REGION", "lettering enters the masthead or footer reserve", page_id, panel_id, item_id)
        except ContractError as exc:
            _add_finding(findings, "OUT_OF_BOUNDS", str(exc), page_id, panel_id, item_id)
    expected_badges = list(range(1, len(narrative_badges) + 1))
    if narrative_badges != expected_badges:
        _add_finding(findings, "NARRATION_SEQUENCE", "narration badges must be contiguous in lettering order", page_id)
    normalized_by_channel = {}
    for item in lettering:
        normalized = " ".join(item.get("text", "").casefold().split())
        normalized_by_channel.setdefault(normalized, set()).add(item.get("channel"))
    if any("NARRATION" in channels and "DIALOGUE" in channels for channels in normalized_by_channel.values()):
        _add_finding(findings, "CAPTION_DIALOGUE_DUPLICATION", "narration may not repeat dialogue verbatim", page_id)
    for index, (left_id, left) in enumerate(resolved_boxes):
        for right_id, right in resolved_boxes[index + 1:]:
            if _intersects(left, right, 4):
                _add_finding(findings, "LETTERING_COLLISION", "lettering objects overlap", page_id, element_id="%s/%s" % (left_id, right_id))
    try:
        FontResolver(font_config).resolve(spec.get("typography", {}).get("family"))
    except BlockedError as exc:
        _add_finding(findings, "MISSING_FONT", str(exc), page_id)
    if fixture_mode and private_preview:
        _add_finding(findings, "PREVIEW_ISOLATION", "private preview mode and fixture mode are mutually exclusive", page_id)
    if fixture_mode and spec.get("publication_eligible") is not False:
        _add_finding(findings, "FIXTURE_PROMOTION", "fixture compositions must be explicitly publication-ineligible", page_id)
    if private_preview:
        if spec.get("private_preview") is not True:
            _add_finding(findings, "PREVIEW_ISOLATION", "private preview mode requires private_preview=true", page_id)
        if spec.get("publication_eligible") is not False:
            _add_finding(findings, "PREVIEW_PROMOTION", "private previews must be explicitly publication-ineligible", page_id)
        if spec.get("non_production_label") != PRIVATE_PREVIEW_LABEL:
            _add_finding(findings, "PREVIEW_LABEL", "private preview requires the exact visible non-production label", page_id)
    if not fixture_mode:
        approval_subjects = {
            "manuscript": spec.get("manuscript_hash"),
            "storyboard": spec.get("storyboard_hash"),
            "series_standard": content_hash(spec.get("series_standard")),
        }
        for gate in ("manuscript", "storyboard", "series_standard"):
            approval = spec.get("approvals", {}).get(gate, {})
            expected_status = "LOCKED_FOR_PRIVATE_PREVIEW" if private_preview else "APPROVED"
            if approval.get("status") != expected_status or approval.get("subject_hash") != approval_subjects[gate]:
                code = "MISSING_PREVIEW_AUTHORITY" if private_preview else "MISSING_APPROVAL"
                _add_finding(findings, code, "%s gate %s lacks an exact hash-bound %s record" % (
                    "private preview" if private_preview else "production", gate, expected_status,
                ), page_id, element_id=gate)
    result = "FIX" if any(item["severity"] == "FIX" for item in findings) else "PASS"
    return {
        "schema_version": "1.0", "engine_version": ENGINE_VERSION,
        "page_id": page_id, "result": result, "findings": findings,
        "semantic_visual_review": {
            "result": "NOT_APPLICABLE_SYNTHETIC_FIXTURE" if fixture_mode else "ESCALATE",
            "reason": "semantic crop, iconography, action, culture, character consistency and image artifacts require genuine pixel review",
        },
    }


def _wrap(draw, text, font, max_width):
    paragraphs = text.split("\n")
    lines = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = line + " " + word
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _fit_text(draw, text, font_path, requested_size, min_size, box, padding):
    _, _, ImageFont = _imaging()
    width, height = box[2] - box[0] - 2 * padding, box[3] - box[1] - 2 * padding
    for size in range(int(requested_size), int(min_size) - 1, -1):
        font = ImageFont.truetype(font_path, size=size)
        lines = _wrap(draw, text, font, width)
        spacing = max(4, size // 5)
        measured = draw.multiline_textbbox((0, 0), "\n".join(lines), font=font, spacing=spacing)
        if measured[2] - measured[0] <= width and measured[3] - measured[1] <= height:
            return font, lines, size, measured, spacing
    font = ImageFont.truetype(font_path, size=int(min_size))
    lines = _wrap(draw, text, font, width)
    measured = draw.multiline_textbbox((0, 0), "\n".join(lines), font=font, spacing=max(4, min_size // 5))
    return font, lines, int(min_size), measured, max(4, min_size // 5)


def _cover_crop(source_size, target_size, focal, zoom=1.0):
    source_w, source_h = source_size
    target_w, target_h = target_size
    scale = max(target_w / source_w, target_h / source_h)
    crop_w, crop_h = target_w / scale / zoom, target_h / scale / zoom
    center_x, center_y = focal["x"] * source_w, focal["y"] * source_h
    left = min(max(0, center_x - crop_w / 2), source_w - crop_w)
    top = min(max(0, center_y - crop_h / 2), source_h - crop_h)
    return (int(round(left)), int(round(top)), int(round(left + crop_w)), int(round(top + crop_h)))


def _draw_lotus(draw, x, y, sx, sy):
    gold = _hex(PALETTE["antique_gold"])
    points = [(x, y), (x + sx * 25, y + sy * 15), (x + sx * 48, y), (x + sx * 25, y + sy * 28)]
    draw.line(points + [points[0]], fill=gold, width=3, joint="curve")
    draw.arc((min(x, x + sx * 50), min(y, y + sy * 32), max(x, x + sx * 50), max(y, y + sy * 32)), 180, 360, fill=gold, width=2)


def _dialogue_tail(box, point, max_length=None):
    """Attach a dialogue tail to the nearest balloon edge without crossing its text field."""
    left, top, right, bottom = box
    distances = {
        "left": abs(point[0] - left), "right": abs(point[0] - right),
        "top": abs(point[1] - top), "bottom": abs(point[1] - bottom),
    }
    edge = min(distances, key=distances.get)
    if edge in {"top", "bottom"}:
        x = max(left + 25, min(point[0], right - 25))
        y = top if edge == "top" else bottom
        base = ((x - 10, y), (x + 10, y))
    else:
        x = left if edge == "left" else right
        y = max(top + 25, min(point[1], bottom - 25))
        base = ((x, y - 10), (x, y + 10))
    if max_length is not None:
        center = ((base[0][0] + base[1][0]) / 2, (base[0][1] + base[1][1]) / 2)
        delta_x, delta_y = point[0] - center[0], point[1] - center[1]
        distance = (delta_x ** 2 + delta_y ** 2) ** 0.5
        if distance > max_length:
            scale = max_length / distance
            point = (int(round(center[0] + delta_x * scale)), int(round(center[1] + delta_y * scale)))
    return base + (point,)


def compose_page(spec, repository_root, output_dir, fixture_mode=False, font_config=None, private_preview=False):
    report = validate_page_spec(spec, repository_root, fixture_mode, font_config, private_preview)
    if report["result"] != "PASS":
        raise ContractError("page specification failed deterministic validation", {"findings": report["findings"]})
    if fixture_mode is not bool(spec.get("fixture")):
        raise ContractError("fixture mode and page specification isolation flag must agree")
    Image, ImageDraw, _ = _imaging()
    root, output = Path(repository_root), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    layout_type = spec["layout_type"]
    canvas = SPREAD_CANVAS if layout_type == "TWO_PAGE_SPREAD" else CANVAS
    width, height = canvas["width"], canvas["height"]
    resolved_font = FontResolver(font_config).resolve(spec.get("typography", {}).get("family"))
    page = Image.new("RGB", (width, height), _hex(PALETTE["midnight_navy"]))
    draw = ImageDraw.Draw(page)
    draw.rounded_rectangle((18, 18, width - 19, height - 19), radius=18, outline=_hex(PALETTE["antique_gold"]), width=5)
    draw.rounded_rectangle((29, 29, width - 30, height - 30), radius=14, outline=_hex(PALETTE["bright_gold"]), width=1)
    _draw_lotus(draw, 42, 42, 1, 1)
    _draw_lotus(draw, width - 42, 42, -1, 1)
    _draw_lotus(draw, 42, height - 42, 1, -1)
    _draw_lotus(draw, width - 42, height - 42, -1, -1)
    # Masthead and footer remain outside the panel field.
    if spec.get("chapter_masthead"):
        _, _, ImageFont = _imaging()
        masthead_font = ImageFont.truetype(resolved_font["regular"], 18)
        draw.text((112, 36), str(spec["chapter_masthead"]).upper(), fill=_hex(PALETTE["parchment"]), font=masthead_font, anchor="la")
    title_font, title_lines, _, _, title_spacing = _fit_text(
        draw, spec.get("page_title", "KHATAKSHETRA"), resolved_font["bold"],
        spec.get("typography", {}).get("title_size", 34), MIN_TITLE_FONT_SIZE,
        (80, 52, width - 80, 126), 6,
    )
    draw.multiline_text((80, 60), "\n".join(title_lines), fill=_hex(PALETTE["bright_gold"]), font=title_font, spacing=title_spacing, anchor="la", align="left")
    panel_boxes = _layout_boxes(layout_type)
    panel_metadata = []
    for panel, normalized in zip(spec["panels"], panel_boxes):
        box = _normal_box(panel.get("box", normalized), width, height)
        draw.rounded_rectangle(box, radius=7, fill=_hex(PALETTE["ink"]), outline=_hex(PALETTE["antique_gold"]), width=5)
        inner = (box[0] + 5, box[1] + 5, box[2] - 5, box[3] - 5)
        if panel.get("assetless", {}).get("kind") == "DETERMINISTIC_DECORATIVE_TEXT_BACKGROUND":
            draw.rounded_rectangle(inner, radius=5, fill=_hex(PALETTE["midnight_navy"]))
            inset = 18
            draw.rounded_rectangle(
                (inner[0] + inset, inner[1] + inset, inner[2] - inset, inner[3] - inset),
                radius=12,
                outline=_hex(PALETTE["antique_gold"]),
                width=2,
            )
            _draw_lotus(draw, inner[0] + 30, inner[1] + 30, 0.7, 0.7)
            _draw_lotus(draw, inner[2] - 30, inner[3] - 30, -0.7, -0.7)
            panel_metadata.append({
                "panel_id": panel["panel_id"], "box": list(box), "asset_path": None,
                "asset_sha256": None, "source_dimensions": None, "source_crop": None,
                "scale_mode": "DETERMINISTIC_DECORATIVE_TEXT_BACKGROUND",
                "rendered_size": [inner[2] - inner[0], inner[3] - inner[1]],
                "paste_at": list(inner[:2]), "focal_point": None, "zoom": None,
                "semantic_crop_review": "NOT_APPLICABLE_ASSETLESS_BACK_MATTER",
            })
            continue
        path = _repository_asset_path(root, panel["asset"]["path"])
        with Image.open(path) as source:
            source = source.convert("RGB")
            crop_spec = panel.get("crop", {})
            mode = crop_spec.get("mode", "COVER")
            focal = crop_spec.get("focal_point", {"x": 0.5, "y": 0.5})
            zoom = crop_spec.get("zoom", 1.0)
            target_w, target_h = inner[2] - inner[0], inner[3] - inner[1]
            if mode == "CONTAIN":
                scale = min(target_w / source.width, target_h / source.height)
                rendered_size = (
                    max(1, int(round(source.width * scale))),
                    max(1, int(round(source.height * scale))),
                )
                rendered = source.resize(rendered_size, Image.Resampling.LANCZOS)
                paste_at = (
                    inner[0] + (target_w - rendered_size[0]) // 2,
                    inner[1] + (target_h - rendered_size[1]) // 2,
                )
                page.paste(rendered, paste_at)
                crop = (0, 0, source.width, source.height)
                scale_mode = "ASPECT_PRESERVING_CONTAIN"
            else:
                crop = _cover_crop(source.size, (target_w, target_h), focal, zoom)
                cropped = source.crop(crop)
                rendered = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
                page.paste(rendered, inner[:2])
                rendered_size = (target_w, target_h)
                paste_at = inner[:2]
                scale_mode = "ASPECT_PRESERVING_COVER"
            panel_metadata.append({
                "panel_id": panel["panel_id"], "box": list(box), "asset_path": panel["asset"]["path"],
                "asset_sha256": panel["asset"]["sha256"], "source_dimensions": list(source.size),
                "source_crop": list(crop), "scale_mode": scale_mode,
                "rendered_size": list(rendered_size), "paste_at": list(paste_at),
                "focal_point": focal, "zoom": zoom,
                "semantic_crop_review": "NOT_APPLICABLE_SYNTHETIC_FIXTURE" if fixture_mode else "PENDING_IMAGE_CAPABLE_REVIEW",
            })
    lettering_metadata = []
    overflow_findings = []
    for item in sorted(spec["lettering"], key=lambda value: value["reading_order"]):
        box = _normal_box(item["box"], width, height)
        channel = item["channel"]
        if channel == "NARRATION":
            draw.rounded_rectangle(box, radius=18, fill=_hex(PALETTE["parchment"]), outline=_hex(PALETTE["antique_gold"]), width=4)
            badge_r = 25
            badge_center = (box[0] + 24, box[1] + 24)
            draw.ellipse((badge_center[0] - badge_r, badge_center[1] - badge_r, badge_center[0] + badge_r, badge_center[1] + badge_r), fill=_hex(PALETTE["burgundy"]), outline=_hex(PALETTE["bright_gold"]), width=3)
            padding = int(item.get("padding", 28))
            text_box = (box[0] + 34, box[1], box[2], box[3])
        elif channel == "DIALOGUE":
            draw.rounded_rectangle(box, radius=32, fill=_hex(PALETTE["speech_white"]), outline=_hex(PALETTE["ink"]), width=3)
            panel = next(value for value in spec["panels"] if value["panel_id"] == item["panel_id"])
            anchor = next(value for value in panel["speaker_anchors"] if value["speaker_id"] == item["speaker_id"])
            point = (int(anchor["x"] * width), int(anchor["y"] * height))
            draw.polygon(
                _dialogue_tail(box, point, item.get("tail_max_length")),
                fill=_hex(PALETTE["speech_white"]),
                outline=_hex(PALETTE["ink"]),
            )
            padding, text_box = int(item.get("padding", 22)), box
        elif channel == "THOUGHT":
            draw.ellipse(box, fill=_hex(PALETTE["speech_white"]), outline=_hex(PALETTE["ink"]), width=3)
            panel = next(value for value in spec["panels"] if value["panel_id"] == item["panel_id"])
            anchor = next(value for value in panel["speaker_anchors"] if value["speaker_id"] == item["speaker_id"])
            point = (int(anchor["x"] * width), int(anchor["y"] * height))
            for step, radius in ((0.35, 9), (0.65, 6), (0.85, 4)):
                cx = int(box[0] + (point[0] - box[0]) * step)
                cy = int(box[3] + (point[1] - box[3]) * step)
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_hex(PALETTE["speech_white"]), outline=_hex(PALETTE["ink"]), width=2)
            padding, text_box = int(item.get("padding", 28)), box
        else:
            draw.rounded_rectangle(box, radius=10, fill=_hex(PALETTE["parchment"]), outline=_hex(PALETTE["bright_gold"]), width=4)
            draw.line((box[0] + 14, box[1] + 12, box[0] + 14, box[3] - 12), fill=_hex(PALETTE["burgundy"]), width=5)
            padding, text_box = int(item.get("padding", 30)), (box[0] + 12, box[1], box[2], box[3])
        requested = item.get("font", {}).get("size", spec.get("typography", {}).get("body_size", 28))
        minimum = item.get("font", {}).get("minimum_size", MIN_BODY_FONT_SIZE)
        font_path = resolved_font["bold"] if item.get("font", {}).get("weight") == "bold" else resolved_font["regular"]
        font, lines, actual_size, measured, spacing = _fit_text(draw, item["text"], font_path, requested, minimum, text_box, padding)
        available_w = text_box[2] - text_box[0] - 2 * padding
        available_h = text_box[3] - text_box[1] - 2 * padding
        measured_w, measured_h = measured[2] - measured[0], measured[3] - measured[1]
        overflow = measured_w > available_w or measured_h > available_h
        if overflow:
            _add_finding(overflow_findings, "TEXT_OVERFLOW", "exact text does not fit at the minimum readable size; revise layout or add a panel/page", spec["page_id"], item["panel_id"], item["lettering_id"])
        draw.multiline_text((text_box[0] + padding, text_box[1] + padding), "\n".join(lines), fill=_hex(PALETTE["ink"]), font=font, spacing=spacing)
        if channel == "NARRATION":
            _, _, badge_font = _imaging()
            number_font = badge_font.truetype(resolved_font["bold"], 25)
            draw.text((badge_center[0], badge_center[1]), str(item["badge_number"]), fill=_hex(PALETTE["speech_white"]), font=number_font, anchor="mm")
        lettering_metadata.append({
            "lettering_id": item["lettering_id"], "source_script_hash": item["source_script_hash"],
            "box": list(box), "requested_font_size": requested, "rendered_font_size": actual_size,
            "minimum_font_size": minimum, "padding": padding, "font_sha256": _sha256_file(font_path),
            "text_sha256": content_hash(item["text"]), "overflow": overflow,
        })
    _, _, footer_font = _imaging()
    footer = footer_font.truetype(resolved_font["bold"], 24)
    if fixture_mode or private_preview:
        draw.rectangle((40, height - 91, width - 40, height - 50), fill=_hex(PALETTE["burgundy"]), outline=_hex(PALETTE["antique_gold"]), width=2)
        label = "NON-PRODUCTION RENDERER TEST" if fixture_mode else PRIVATE_PREVIEW_LABEL
        label_font = footer_font.truetype(resolved_font["bold"], 20 if private_preview else 24)
        draw.text((width // 2, height - 70), label, font=label_font, fill=_hex(PALETTE["speech_white"]), anchor="mm")
    draw.text((width - 62, height - 37), str(spec["page_number"]), font=footer, fill=_hex(PALETTE["bright_gold"]), anchor="rm")
    if overflow_findings:
        raise ContractError("page lettering overflowed at the minimum readable size", {"findings": overflow_findings})
    stem = "%04d-%s" % (spec["page_number"], spec["page_id"])
    png_path = output / (stem + ".png")
    source_path = output / (stem + ".composition.json")
    metadata_path = output / (stem + ".render.json")
    validation_path = output / (stem + ".validation.json")
    composition = deepcopy(spec)
    for derived in (
        "composition_hash", "resolved_panels", "resolved_lettering", "resolved_font",
        "renderer_source_sha256", "font_config_sha256", "engine_version", "fixture_mode",
    ):
        composition.pop(derived, None)
    composition.update({
        "schema_version": "1.0", "engine_version": ENGINE_VERSION, "canvas": canvas,
        "renderer_source_sha256": _sha256_file(Path(__file__)),
        "resolved_panels": panel_metadata, "resolved_lettering": lettering_metadata,
        "resolved_font": resolved_font, "fixture_mode": fixture_mode,
        "font_config_sha256": _sha256_file(font_config) if font_config and Path(font_config).is_file() else None,
        "publication_eligible": False if (fixture_mode or private_preview) else spec.get("publication_eligible", False),
        "private_preview": private_preview,
        "non_production_label": FIXTURE_LABEL if fixture_mode else (PRIVATE_PREVIEW_LABEL if private_preview else None),
    })
    composition["composition_hash"] = content_hash(composition)
    atomic_json_write(source_path, composition)
    page.save(png_path, format="PNG", optimize=False, compress_level=9)
    png_hash = _sha256_file(png_path)
    metadata = {
        "schema_version": "1.0", "engine_version": ENGINE_VERSION, "book_id": spec["book_id"],
        "renderer_source_sha256": _sha256_file(Path(__file__)),
        "page_id": spec["page_id"], "page_number": spec["page_number"], "reading_order": spec["reading_order"],
        "composition_path": str(source_path), "composition_hash": composition["composition_hash"],
        "rendered_png_path": str(png_path), "rendered_png_sha256": png_hash,
        "rendered_pixel_sha256": _pixel_hash(png_path), "dimensions": [width, height],
        "fixture_mode": fixture_mode, "private_preview": private_preview,
        "publication_eligible": False if (fixture_mode or private_preview) else spec.get("publication_eligible", False),
    }
    metadata["metadata_hash"] = content_hash(metadata)
    atomic_json_write(metadata_path, metadata)
    final_report = validate_rendered_page(composition, metadata, repository_root, fixture_mode, private_preview)
    atomic_json_write(validation_path, final_report)
    if final_report["result"] != "PASS":
        raise ContractError("rendered page failed deterministic validation", {"findings": final_report["findings"]})
    return {
        "status": "PASS", "page_id": spec["page_id"], "composition": str(source_path),
        "rendered_png": str(png_path), "metadata": str(metadata_path), "validation": str(validation_path),
        "composition_hash": composition["composition_hash"], "rendered_png_sha256": png_hash,
        "semantic_visual_review": final_report["semantic_visual_review"],
        "publication_eligible": False if (fixture_mode or private_preview) else spec.get("publication_eligible", False),
    }


def validate_rendered_page(composition, metadata, repository_root, fixture_mode=False, private_preview=False):
    report = validate_page_spec(composition, repository_root, fixture_mode, None, private_preview)
    findings = list(report["findings"])
    unsigned_composition = {key: value for key, value in composition.items() if key != "composition_hash"}
    if composition.get("composition_hash") != content_hash(unsigned_composition):
        _add_finding(findings, "COMPOSITION_HASH_MISMATCH", "editable composition hash is invalid", composition.get("page_id"))
    unsigned_metadata = {key: value for key, value in metadata.items() if key != "metadata_hash"}
    if metadata.get("metadata_hash") != content_hash(unsigned_metadata):
        _add_finding(findings, "METADATA_HASH_MISMATCH", "render metadata hash is invalid", composition.get("page_id"))
    png_path = Path(metadata.get("rendered_png_path", ""))
    if not png_path.is_file():
        _add_finding(findings, "MISSING_RENDER", "rendered page PNG is missing", composition.get("page_id"))
    else:
        if _sha256_file(png_path) != metadata.get("rendered_png_sha256"):
            _add_finding(findings, "ARTIFACT_HASH_MISMATCH", "rendered page hash does not match metadata", composition.get("page_id"))
        Image, _, _ = _imaging()
        with Image.open(png_path) as image:
            expected = SPREAD_CANVAS if composition.get("layout_type") == "TWO_PAGE_SPREAD" else CANVAS
            if image.size != (expected["width"], expected["height"]):
                _add_finding(findings, "PAGE_DIMENSIONS", "rendered page dimensions are incorrect", composition.get("page_id"))
    for item in composition.get("resolved_lettering", []):
        if item.get("overflow"):
            _add_finding(findings, "TEXT_OVERFLOW", "rendered exact lettering overflowed", composition.get("page_id"), element_id=item.get("lettering_id"))
        if item.get("rendered_font_size", 0) < item.get("minimum_font_size", MIN_BODY_FONT_SIZE):
            _add_finding(findings, "MINIMUM_FONT_SIZE", "rendered text is below the configured minimum", composition.get("page_id"), element_id=item.get("lettering_id"))
    result = "FIX" if findings else "PASS"
    return {
        "schema_version": "1.0", "engine_version": ENGINE_VERSION,
        "page_id": composition.get("page_id"), "result": result, "findings": findings,
        "semantic_visual_review": report["semantic_visual_review"],
    }


def validate_composition_file(path, repository_root, fixture_mode=False, private_preview=False):
    composition = load_json(Path(path))
    metadata_path = Path(path).with_name(Path(path).name.replace(".composition.json", ".render.json"))
    if metadata_path.is_file():
        return validate_rendered_page(composition, load_json(metadata_path), repository_root, fixture_mode, private_preview)
    return validate_page_spec(composition, repository_root, fixture_mode, private_preview=private_preview)


def compose_book(manifest, repository_root, output_dir, fixture_mode=False, font_config=None):
    if fixture_mode is not bool(manifest.get("fixture")):
        raise ContractError("fixture mode and book manifest isolation flag must agree")
    page_specs = manifest.get("pages", [])
    if not page_specs:
        raise ContractError("composition manifest contains no pages")
    page_ids = [page.get("page_id") for page in page_specs]
    orders = [page.get("reading_order") for page in page_specs]
    numbers = [page.get("page_number") for page in page_specs]
    if len(page_ids) != len(set(page_ids)):
        raise ContractError("book manifest contains duplicate page IDs")
    expected = list(range(1, len(page_specs) + 1))
    if orders != expected or numbers != expected:
        raise ContractError("book pages must be explicitly ordered and numbered contiguously")
    results = [compose_page(page, repository_root, output_dir, fixture_mode, font_config) for page in page_specs]
    rendered_hashes = [item["rendered_png_sha256"] for item in results]
    if len(rendered_hashes) != len(set(rendered_hashes)):
        raise ContractError("book contains exact duplicate rendered pages")
    ordered = {
        "schema_version": "1.0", "engine_version": ENGINE_VERSION,
        "book_id": manifest.get("book_id"), "title": manifest.get("title"),
        "fixture": fixture_mode, "publication_eligible": False if fixture_mode else manifest.get("publication_eligible", False),
        "label": FIXTURE_LABEL if fixture_mode else manifest.get("title"),
        "pages": [{
            "page_id": item["page_id"], "page_number": index, "reading_order": index,
            "png_path": item["rendered_png"], "png_sha256": item["rendered_png_sha256"],
            "composition_path": item["composition"], "validation_path": item["validation"],
        } for index, item in enumerate(results, 1)],
    }
    ordered["manifest_hash"] = content_hash(ordered)
    path = Path(output_dir) / "composed-book-manifest.json"
    atomic_json_write(path, ordered)
    return {"status": "PASS", "manifest": str(path), "pages": results, "page_count": len(results), "publication_eligible": ordered["publication_eligible"]}


def export_pdf(manifest, output_path, fixture_mode=False):
    if fixture_mode is not bool(manifest.get("fixture")):
        raise ContractError("fixture mode and composed-book manifest isolation flag must agree")
    if fixture_mode and manifest.get("publication_eligible") is not False:
        raise ContractError("fixture PDF cannot be publication-eligible")
    supplied_manifest_hash = manifest.get("manifest_hash")
    if supplied_manifest_hash:
        unsigned_manifest = {key: value for key, value in manifest.items() if key != "manifest_hash"}
        if supplied_manifest_hash != content_hash(unsigned_manifest):
            raise ContractError("composed-book manifest hash is invalid")
    pages = manifest.get("pages", [])
    if [page.get("reading_order") for page in pages] != list(range(1, len(pages) + 1)):
        raise ContractError("PDF pages must have contiguous explicit order")
    hashes = []
    for page in pages:
        path = Path(page["png_path"])
        if not path.is_file() or _sha256_file(path) != page.get("png_sha256"):
            raise ContractError("PDF input page hash mismatch", {"page_id": page.get("page_id")})
        Image, _, _ = _imaging()
        with Image.open(path) as image:
            if image.size != (CANVAS["width"], CANVAS["height"]):
                raise ContractError(
                    "portrait digital-reader export cannot scale or distort a spread; supply an approved split or uniform landscape profile",
                    {"page_id": page.get("page_id"), "dimensions": list(image.size)},
                )
        validation = load_json(Path(page["validation_path"]))
        if validation.get("result") != "PASS":
            raise ContractError("PDF input page has not passed deterministic QA", {"page_id": page.get("page_id")})
        hashes.append(page["png_sha256"])
    if len(hashes) != len(set(hashes)):
        raise ContractError("PDF input contains duplicate pages")
    ImageReader, canvas, _ = _pdf_libraries()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=(CANVAS["width"], CANVAS["height"]), pageCompression=1, invariant=1)
    pdf.setTitle(FIXTURE_LABEL if fixture_mode else manifest.get("title", manifest.get("book_id", "Khatakshetra Book")))
    pdf.setAuthor("Khatakshetra Autonomous Book Factory")
    pdf.setSubject(
        "Technical renderer fixture; not a finished mythology book" if fixture_mode else
        "Private diagnostic proof; not approved for publication" if manifest.get("private_preview") else
        "Digital reader edition"
    )
    pdf.setCreator("Khatakshetra Book Factory page engine %s" % ENGINE_VERSION)
    for page in pages:
        pdf.setPageSize((CANVAS["width"], CANVAS["height"]))
        pdf.drawImage(ImageReader(page["png_path"]), 0, 0, width=CANVAS["width"], height=CANVAS["height"], preserveAspectRatio=False, mask=None)
        pdf.showPage()
    pdf.save()
    inspection = inspect_pdf(output, manifest)
    if inspection["result"] != "PASS":
        raise ContractError("exported PDF failed inspection", {"findings": inspection["findings"]})
    inspection_path = output.with_suffix(".inspection.json")
    atomic_json_write(inspection_path, inspection)
    return {
        "status": "PASS", "pdf_path": str(output), "pdf_sha256": inspection["pdf_sha256"],
        "inspection_path": str(inspection_path), "page_count": len(pages),
        "publication_eligible": False if fixture_mode else manifest.get("publication_eligible", False),
    }


def inspect_pdf(pdf_path, manifest=None):
    _, _, PdfReader = _pdf_libraries()
    path = Path(pdf_path)
    if not path.is_file():
        raise ContractError("PDF does not exist", {"path": str(path)})
    reader = PdfReader(str(path))
    findings, pages = [], []
    expected_pages = manifest.get("pages", []) if manifest else []
    if manifest and len(reader.pages) != len(expected_pages):
        _add_finding(findings, "PDF_PAGE_COUNT", "PDF page count differs from its ordered manifest")
    for index, page in enumerate(reader.pages, 1):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        if round(width) != CANVAS["width"] or round(height) != CANVAS["height"] or width >= height:
            _add_finding(findings, "PDF_PAGE_DIMENSIONS", "PDF page must be portrait 1086 x 1448", element_id=str(index))
        images = list(page.images)
        if len(images) != 1:
            _add_finding(findings, "PDF_IMAGE_COUNT", "each PDF page must contain exactly one full-page raster", element_id=str(index))
        image_info = []
        for embedded in images:
            try:
                image = embedded.image.convert("RGB")
                image_info.append({"name": embedded.name, "dimensions": list(image.size), "pixel_sha256": sha256_bytes(image.tobytes())})
                if image.size != (CANVAS["width"], CANVAS["height"]):
                    _add_finding(findings, "PDF_EMBEDDED_IMAGE_DIMENSIONS", "embedded page raster dimensions changed", element_id=str(index))
                if manifest and image_info[-1]["pixel_sha256"] != _pixel_hash(expected_pages[index - 1]["png_path"]):
                    _add_finding(findings, "PDF_PIXEL_MISMATCH", "embedded raster pixels differ from the composed PNG", element_id=str(index))
            except Exception as exc:  # pypdf exposes decoder failures as varied exception types
                _add_finding(findings, "PDF_IMAGE_DECODE", str(exc), element_id=str(index))
        pages.append({"page_number": index, "width": width, "height": height, "orientation": "PORTRAIT" if width < height else "LANDSCAPE", "images": image_info})
    return {
        "schema_version": "1.0", "engine_version": ENGINE_VERSION, "result": "FIX" if findings else "PASS",
        "findings": findings, "pdf_path": str(path), "pdf_sha256": _sha256_file(path),
        "page_count": len(reader.pages), "pages": pages,
        "page_order": [page.get("page_id") for page in expected_pages] if manifest else "NOT_PROVIDED",
        "digital_reader_profile": "ONE_NATIVE_1086_X_1448_RASTER_PER_PAGE_NO_PRINT_CLAIM",
    }


def repair_page(composition, changes, failure_causes=None, allowed_fields=None):
    """Create a bounded page-local revision without touching locked narrative hashes."""
    allowed = set(allowed_fields or {"panels", "lettering", "layout_type"})
    forbidden = set(changes) - allowed
    if forbidden:
        raise ContractError("page repair attempted to change locked content", {"forbidden_fields": sorted(forbidden)})
    repaired = deepcopy(composition)
    locked = {key: composition.get(key) for key in ("book_id", "book_version", "manuscript_hash", "storyboard_hash", "page_id", "page_number", "reading_order")}
    for key, value in changes.items():
        repaired[key] = deepcopy(value)
    if any(repaired.get(key) != value for key, value in locked.items()):
        raise ContractError("page-local repair changed a locked narrative identity")
    repaired["parent_composition_hash"] = composition.get("composition_hash") or content_hash(composition)
    repaired["repair_history"] = list(composition.get("repair_history", [])) + [{
        "parent_composition_hash": repaired["parent_composition_hash"],
        "changed_fields": sorted(changes),
        "failure_causes": list(failure_causes or []),
        "retry_number": len(composition.get("repair_history", [])) + 1,
    }]
    for key in ("resolved_panels", "resolved_lettering", "resolved_font"):
        repaired.pop(key, None)
    repaired.pop("composition_hash", None)
    repaired["composition_hash"] = content_hash(repaired)
    return repaired
