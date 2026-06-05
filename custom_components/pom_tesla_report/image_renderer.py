"""PNG renderer for POM Tesla Report."""

from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_OUTPUT_PATH = "/config/www/pom_tesla_report/test_trip_report.png"

COLOR_BG = "#20211f"
COLOR_CARD = "#0d0d0e"
COLOR_HEADER = "#101011"
COLOR_SECTION = "#111112"
COLOR_LINE = "#3a3d45"
COLOR_TEXT = "#ffffff"
COLOR_MUTED = "#8a8d93"
COLOR_MUTED_DARK = "#555961"
COLOR_RED = "#ef4e52"
COLOR_GREEN = "#23c995"
COLOR_YELLOW = "#ffb020"

BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "fonts"
REGULAR_FONT_PATH = FONT_DIR / "DejaVuSans.ttf"
BOLD_FONT_PATH = FONT_DIR / "DejaVuSans-Bold.ttf"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load bundled font first, then fallback."""
    primary = BOLD_FONT_PATH if bold else REGULAR_FONT_PATH
    secondary = REGULAR_FONT_PATH

    for path in [primary, secondary]:
        try:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue

    fallback_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/ttf-dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/local/share/fonts/DejaVuSans-Bold.ttf" if bold else "/usr/local/share/fonts/DejaVuSans.ttf",
        "/config/fonts/DejaVuSans-Bold.ttf" if bold else "/config/fonts/DejaVuSans.ttf",
        "/config/www/fonts/DejaVuSans-Bold.ttf" if bold else "/config/www/fonts/DejaVuSans.ttf",
    ]

    for font_path in fallback_candidates:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            continue

    
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def safe_text(value: Any, default: str = "-") -> str:
    """Return safe printable text."""
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    return text




def _glyph_bytes(font: ImageFont.ImageFont, ch: str) -> bytes:
    try:
        return bytes(font.getmask(ch))
    except Exception:
        return b""


def _font_supports_text(font: ImageFont.ImageFont, text: str) -> bool:
    """Best-effort check for whether a PIL font can render Turkish text.

    Some PIL bitmap fallbacks draw every unsupported Turkish glyph as the same
    square replacement glyph. We detect that pattern and transliterate only in
    that case.
    """
    try:
        mask = font.getmask(text)
        if not (mask and mask.getbbox()):
            return False
    except Exception:
        return False
    replacement = _glyph_bytes(font, "□")
    for ch in text:
        if ord(ch) < 128:
            continue
        glyph = _glyph_bytes(font, ch)
        if replacement and glyph == replacement:
            return False
    return True


def display_text(text: Any, font: ImageFont.ImageFont | None = None, default: str = "-") -> str:
    """Return text safe for the currently available font.

    Some minimal Home Assistant containers do not include a Unicode TrueType
    font. When PIL falls back to its tiny bitmap font, Turkish glyphs render as
    square boxes. In that situation we degrade to ASCII so reports stay readable
    instead of showing replacement boxes. If a Turkish-capable font is present,
    the original text is kept.
    """
    text_value = safe_text(text, default)
    if font is None or all(ord(ch) < 128 for ch in text_value):
        return text_value
    if _font_supports_text(font, text_value):
        return text_value
    table = str.maketrans({
        "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
    })
    normalized = text_value.translate(table)
    return unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode("ascii") or default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Return safe float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any, default: bool = True) -> bool:
    """Convert Home Assistant option values to bool safely."""
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "on", "yes", "1"}:
            return True
        if text in {"false", "off", "no", "0"}:
            return False

    return default


def should_show(data: dict[str, Any], key: str, default: bool = True) -> bool:
    """Return whether a report section should be shown."""
    return as_bool(data.get(key), default)


def is_meaningful(value: Any) -> bool:
    """Check whether a value should be rendered."""
    if value is None:
        return False

    if isinstance(value, str):
        text = value.strip().lower()
        return text not in {"", "-", "none", "unknown", "unavailable"}

    return True


def text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
) -> tuple[int, int]:
    """Return text size."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def load_and_prepare_map_image(
    image_path: Any,
    target_width: int,
    target_height: int,
) -> Image.Image | None:
    """Load a map image and crop/resize it to cover the target area."""
    try:
        path = Path(str(image_path))
        if not path.exists():
            return None
        image = Image.open(path).convert("RGB")
    except Exception:
        return None

    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0:
        return None

    target_ratio = target_width / target_height
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_h = src_h
        new_w = int(new_h * target_ratio)
        left = max(0, (src_w - new_w) // 2)
        image = image.crop((left, 0, left + new_w, src_h))
    else:
        new_w = src_w
        new_h = int(new_w / target_ratio)
        top = max(0, (src_h - new_h) // 2)
        image = image.crop((0, top, src_w, top + new_h))

    return image.resize((target_width, target_height), Image.LANCZOS)




def currency_label_from_data(data: dict[str, Any]) -> str:
    """Return report currency label."""
    label = str(data.get("currency_label") or data.get("report_currency") or "TL").strip()
    return label or "TL"


def money_text(value: Any, currency: str, decimals: int = 2) -> str:
    """Format a money value with the selected currency label."""
    return f"{safe_float(value):.{decimals}f} {currency}"


def unit_price_text(value: Any, currency: str) -> str:
    """Format a per-kWh price with the selected currency label."""
    return f"{safe_float(value):.2f} {currency}/kWh"




def draw_safe_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int] | tuple[float, float], text: Any, font: ImageFont.ImageFont, fill: str, **kwargs: Any) -> None:
    """Draw text, transliterating Turkish only when current font lacks glyphs."""
    draw.text(xy, display_text(text, font), font=font, fill=fill, **kwargs)

def draw_right_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
) -> None:
    """Draw right-aligned text."""
    width, _ = text_size(draw, text, font)
    draw_safe_text(draw, (x - width, y), text, font=font, fill=fill)


def draw_center_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
) -> None:
    """Draw centered text in a given width."""
    text_width, _ = text_size(draw, text, font)
    draw_safe_text(draw, (x + (width - text_width) / 2, y), text, font=font, fill=fill)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Simple text wrap."""
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        test_width, _ = text_size(draw, test, font)

        if test_width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def report_lang(value: Any) -> str:
    """Normalize report language."""
    return "en" if str(value or "").strip().lower().startswith("en") else "tr"


def trip_t(lang: str) -> dict[str, str]:
    """Static translations for trip visuals."""
    lang = report_lang(lang)
    if lang == "en":
        return {
            "distance": "Distance",
            "duration": "Duration",
            "traffic": "Traffic",
            "driving_score": "Driving score",
            "traffic_model": "Slowdown analysis",
            "traffic_breakdown": "Low-speed details",
            "grade_report": "Grade analysis",
            "avg_speed": "Avg. speed",
            "overall_avg_speed": "Overall avg.",
            "energy": "Energy",
            "consumption": "Consumption",
            "battery": "Battery",
            "cost": "COST",
            "climate": "Climate",
            "elevation": "Elevation",
            "route_map": "Route Map",
            "map_load_failed": "Map image could not be loaded",
            "report_title": "Trip Report",
            "test_report_title": "TEST Trip Report",
            "km_per_h": "km/h",
            "elevation_diff": "m diff",
            "climate_on_for": "Climate was active for about {duration} during the trip.",
            "climate_unused": "Climate was not used during the trip.",
        }
    return {
        "distance": "Mesafe",
        "duration": "Süre",
        "traffic": "Trafik",
        "driving_score": "Sürüş skoru",
        "traffic_model": "Yavaşlama analizi",
        "traffic_breakdown": "Düşük hız detayı",
        "grade_report": "Eğim analizi",
        "avg_speed": "Ort. hız",
        "overall_avg_speed": "Genel ort.",
        "energy": "Enerji",
        "consumption": "Tüketim",
        "battery": "Batarya",
        "cost": "MALİYET",
        "climate": "Klima",
        "elevation": "Rakım",
        "route_map": "Rota Haritası",
        "map_load_failed": "Harita görseli yüklenemedi",
        "report_title": "Sürüş Raporu",
        "test_report_title": "TEST Sürüş Raporu",
        "km_per_h": "km/sa",
        "elevation_diff": "m fark",
        "climate_on_for": "Klima yolculuk boyunca yaklaşık {duration} açıktı.",
        "climate_unused": "Klima yolculuk boyunca kullanılmadı.",
    }


def compact_duration_text(value: Any, default: str = "-", lang: str = "tr") -> str:
    """Compact verbose duration text so PNG rows stay visually balanced and localized."""
    text = safe_text(value, default)
    lowered = text.lower()
    is_en = report_lang(lang) == "en"

    if any(phrase in lowered for phrase in ["dakikadan az", "1 dakikadan az", "0 dakika", "0 dk", "less than a minute", "0 minutes", "0 min"]):
        return "<1 min" if is_en else "<1 dk"

    compact = text
    if is_en:
        compact = re.sub(r"\b(saat|sa)\b\.?", "hr", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\b(dakika|dk)\b\.?", "min", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\b(hours?)\b", "hr", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\b(minutes?)\b", "min", compact, flags=re.IGNORECASE)
    else:
        compact = re.sub(r"\b(saat)\b", "sa", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\bdakika\b", "dk", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\b(hours?|hr)\b", "sa", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\b(minutes?|min)\b", "dk", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\s+", " ", compact).strip()

    return compact


def choose_value_font(value: str) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Choose a slightly smaller font for longer row values."""
    length = len(value)

    if length <= 8:
        return load_font(54, bold=True)
    if length <= 12:
        return load_font(46, bold=True)
    return load_font(38, bold=True)


def draw_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    value: str,
    unit: str = "",
    value_color: str = COLOR_TEXT,
) -> int:
    """Draw one report row."""
    label_font = load_font(24, bold=True)
    unit_font = load_font(22, bold=True)

    draw.rectangle((x, y, x + width, y + height), fill=COLOR_CARD)

    line_y = y + height
    draw.line((x + 24, line_y, x + width - 24, line_y), fill=COLOR_LINE, width=2)

    draw_safe_text(draw, (x + 36, y + 39), label, font=label_font, fill=COLOR_MUTED_DARK)

    value = safe_text(value)
    unit = safe_text(unit, "")
    value_font = choose_value_font(value)

    value_width, _ = text_size(draw, value, value_font)
    unit_width, _ = text_size(draw, unit, unit_font) if unit else (0, 0)

    total_width = value_width + (8 if unit else 0) + unit_width
    right_x = x + width - 36
    start_x = right_x - total_width

    draw_safe_text(draw, (start_x, y + 25), value, font=value_font, fill=value_color)

    if unit:
        draw_safe_text(draw, 
            (start_x + value_width + 8, y + 51),
            unit,
            font=unit_font,
            fill=COLOR_MUTED,
        )

    return y + height



def duration_text_to_minutes_for_image(value: Any) -> float:
    text = str(value or "").strip().lower().replace(",", ".")
    if not text:
        return 0.0
    total = 0.0
    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*(?:sa|saat|hour|hours|hr|h)\b", text):
        total += safe_float(match.group(1), 0.0) * 60.0
    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*(?:dk|dakika|minute|minutes|min|m)\b", text):
        total += safe_float(match.group(1), 0.0)
    if total > 0:
        return total
    nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", text)
    return safe_float(nums[0], 0.0) if nums else 0.0


def overall_speed_for_image(data: dict[str, Any]) -> float:
    direct = safe_float(data.get("average_overall_speed"), 0.0)
    if direct > 0:
        return direct
    distance = safe_float(data.get("trip_km"), 0.0)
    minutes = duration_text_to_minutes_for_image(data.get("duration_text"))
    if distance > 0 and minutes > 0:
        return distance / (minutes / 60.0)
    return 0.0


def collect_main_rows(data: dict[str, Any], lang: str = "tr") -> list[dict[str, str]]:
    """Collect rows dynamically so hidden/missing fields don't leave broken layout."""
    rows: list[dict[str, str]] = []
    tr = trip_t(lang)

    if should_show(data, "show_distance") and is_meaningful(data.get("trip_km")):
        rows.append(
            {
                "label": tr["distance"],
                "value": f"{safe_float(data.get('trip_km')):.2f}",
                "unit": "km",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_duration") and is_meaningful(data.get("duration_text")):
        rows.append(
            {
                "label": tr["duration"],
                "value": compact_duration_text(data.get("duration_text"), lang=lang),
                "unit": "",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_traffic") and is_meaningful(data.get("traffic_text")):
        rows.append(
            {
                "label": tr["traffic"],
                "value": compact_duration_text(data.get("traffic_text"), lang=lang),
                "unit": "",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_average_speed") and is_meaningful(data.get("average_speed")):
        rows.append(
            {
                "label": tr["avg_speed"],
                "value": f"{safe_float(data.get('average_speed')):.1f}",
                "unit": tr["km_per_h"],
                "color": COLOR_TEXT,
            }
        )

    # alpha227: keep Tessie-style moving average as the main "Ort. hız",
    # and always compute/show total-duration overall average when possible.
    overall_speed = overall_speed_for_image(data)
    if should_show(data, "show_average_speed") and overall_speed > 0:
        rows.append(
            {
                "label": tr["overall_avg_speed"],
                "value": f"{overall_speed:.1f}",
                "unit": tr["km_per_h"],
                "color": COLOR_MUTED,
            }
        )

    if should_show(data, "show_energy") and is_meaningful(data.get("used_kwh")):
        rows.append(
            {
                "label": tr["energy"],
                "value": f"{safe_float(data.get('used_kwh')):.2f}",
                "unit": "kWh",
                "color": COLOR_RED,
            }
        )

    if should_show(data, "show_consumption") and is_meaningful(data.get("consumption_kwh_100km")):
        rows.append(
            {
                "label": tr["consumption"],
                "value": f"{safe_float(data.get('consumption_kwh_100km')):.2f}",
                "unit": "kWh/100",
                "color": COLOR_TEXT,
            }
        )

    return rows


def collect_bottom_info(data: dict[str, Any], lang: str = "tr") -> list[tuple[str, str]]:
    """Collect bottom info lines dynamically."""
    items: list[tuple[str, str]] = []
    tr = trip_t(lang)

    score = safe_float(data.get("driving_score"), 0.0)
    if score > 0:
        score_label = safe_text(data.get("driving_score_label"), "")
        score_text = safe_text(data.get("driving_score_text"), "")
        if score_text not in {"", "-"}:
            value = score_text
            if score_label not in {"", "-"} and score_label not in value:
                value = f"{score_label} · {value}"
        else:
            value = f"{score:.0f}/100" + (f" · {score_label}" if score_label not in {"", "-"} else "")
        items.append((tr["driving_score"], value))

    climate_minutes = safe_float(data.get("climate_duration_minutes"), -1.0)
    climate_text = safe_text(data.get("climate_text"), "")
    if should_show(data, "show_climate") and (is_meaningful(climate_text) or climate_minutes >= 0):
        if climate_minutes >= 0:
            compact = compact_duration_text(data.get("climate_duration_text") or data.get("climate_text") or "", lang=lang)
            if compact in {"-", ""}:
                hours = int(climate_minutes // 60)
                mins = int(round(climate_minutes % 60))
                compact = f"{hours} hr {mins} min" if lang == "en" and hours and mins else (f"{hours} hr" if lang == "en" and hours else (f"{mins} min" if lang == "en" else (f"{hours} sa {mins} dk" if hours and mins else (f"{hours} sa" if hours else f"{mins} dk"))))
            climate_text = tr["climate_on_for"].format(duration=compact) if climate_minutes > 0 else tr["climate_unused"]
        items.append((tr["climate"], climate_text))

    traffic_delay_seconds = safe_float(data.get("traffic_delay_seconds"), 0.0)
    effective_delay_seconds = safe_float(data.get("effective_traffic_delay_seconds"), traffic_delay_seconds)
    raw_low_speed_percent = safe_float(data.get("raw_low_speed_percent"), safe_float(data.get("traffic_ratio_moving_percent"), 0.0))
    congestion_percent = safe_float(data.get("traffic_congestion_percent"), 0.0)
    reference_speed = safe_float(data.get("traffic_reference_speed_kmh"), 0.0)
    traffic_type = safe_text(data.get("traffic_reference_trip_type_label"), "")
    traffic_impact = safe_text(data.get("traffic_effective_impact_label") or data.get("effective_traffic_impact") or data.get("traffic_impact_label"), "")
    reason_label = safe_text(data.get("slowdown_reason_label"), "")
    free_flow_text = safe_text(data.get("traffic_free_flow_text"), "")
    delay_text = safe_text(data.get("effective_traffic_delay_text") or data.get("traffic_delay_text"), "")

    if traffic_delay_seconds > 0 or effective_delay_seconds > 0 or raw_low_speed_percent > 0 or reference_speed > 0:
        if lang == "en":
            model_text = (
                f"Impact {traffic_impact or '-'} · effective delay {delay_text}"
                + (f" · reason {reason_label}" if reason_label not in {'', '-'} else "")
                + (f" · raw low-speed {raw_low_speed_percent:.0f}%" if raw_low_speed_percent > 0 else "")
                + (f" · ref {reference_speed:.0f} km/h" if reference_speed > 0 else "")
                + (f" · {traffic_type}" if traffic_type not in {'', '-'} else "")
                + (f" · free {free_flow_text}" if free_flow_text not in {'', '-'} else "")
            )
        else:
            model_text = (
                f"Etki {traffic_impact or '-'} · etkin gecikme {delay_text}"
                + (f" · neden {reason_label}" if reason_label not in {'', '-'} else "")
                + (f" · ham düşük hız %{raw_low_speed_percent:.0f}" if raw_low_speed_percent > 0 else "")
                + (f" · ref {reference_speed:.0f} km/sa" if reference_speed > 0 else "")
                + (f" · {traffic_type}" if traffic_type not in {'', '-'} else "")
                + (f" · serbest {free_flow_text}" if free_flow_text not in {'', '-'} else "")
            )
        items.append((tr["traffic_model"], model_text))

    stopped_text = safe_text(data.get("stopped_in_drive_text"), "")
    slow_text = safe_text(data.get("slow_traffic_text"), "")
    normal_text = safe_text(data.get("normal_drive_text"), "")
    if any(text not in {"", "-"} for text in (stopped_text, slow_text, normal_text)):
        if lang == "en":
            breakdown = f"Stop-go {stopped_text} · Low-speed {slow_text} · Normal {normal_text}"
        else:
            breakdown = f"Dur-kalk {stopped_text} · Düşük hız {slow_text} · Normal {normal_text}"
        items.append((tr["traffic_breakdown"], breakdown))

    min_elevation = data.get("min_elevation")
    max_elevation = data.get("max_elevation")
    elevation_range = data.get("elevation_range")

    has_elevation = (
        is_meaningful(min_elevation)
        or is_meaningful(max_elevation)
        or is_meaningful(elevation_range)
    )

    if should_show(data, "show_elevation") and has_elevation:
        elevation_text = (
            f"{safe_float(min_elevation):.0f}–"
            f"{safe_float(max_elevation):.0f} m · "
            f"{safe_float(elevation_range):.0f} {tr['elevation_diff']}"
        )
        gain = safe_float(data.get("elevation_gain"), 0.0)
        loss = safe_float(data.get("elevation_loss"), 0.0)
        sample_count = int(safe_float(data.get("elevation_sample_count"), 0.0))
        if gain > 0 or loss > 0:
            elevation_text += f" · +{gain:.0f}/-{loss:.0f} m"
        if sample_count > 0:
            elevation_text += f" · {sample_count} sample"
        items.append((tr["elevation"], elevation_text))

    grade_text = safe_text(data.get("elevation_grade_text"), "")
    if should_show(data, "show_elevation") and grade_text not in {"", "-"}:
        climb_energy = safe_float(data.get("estimated_climb_energy_kwh"), 0.0)
        regen_energy = safe_float(data.get("estimated_regen_potential_kwh"), 0.0)
        if climb_energy > 0 or regen_energy > 0:
            if lang == "en":
                grade_text += f" · climb ~{climb_energy:.2f} kWh · regen ~{regen_energy:.2f} kWh"
            else:
                grade_text += f" · tırmanış ~{climb_energy:.2f} kWh · regen ~{regen_energy:.2f} kWh"
        items.append((tr["grade_report"], grade_text))

    return items


def calculate_bottom_section_height(
    draw: ImageDraw.ImageDraw,
    info_items: list[tuple[str, str]],
    content_width: int,
) -> int:
    """Calculate bottom section height dynamically.

    alpha238: bottom report lines are rendered label-above-value so long
    traffic/elevation text cannot collide with labels.
    """
    if not info_items:
        return 0

    info_font = load_font(21, bold=True)
    available_width = content_width

    total_height = 24  # top padding
    for _label, value in info_items:
        wrapped = wrap_text(draw, value, info_font, available_width)
        line_count = max(1, len(wrapped))
        # label line + value lines + separator/margins
        total_height += 28 + (line_count * 27) + 14

    total_height += 16  # bottom padding
    return total_height


def has_battery_data(data: dict[str, Any]) -> bool:
    """Return whether battery section has useful data."""
    return is_meaningful(data.get("start_battery")) or is_meaningful(data.get("end_battery"))


def cost_presets_from_data(data: dict[str, Any], currency: str) -> list[dict[str, Any]]:
    """Return up to three station presets for the visual cost cards."""
    colors = [
        (COLOR_GREEN, "#0e241f"),
        (COLOR_RED, "#271719"),
        (COLOR_YELLOW, "#2a210f"),
    ]
    raw = data.get("cost_presets") or data.get("provider_presets") or []
    result: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for index, item in enumerate(raw[:3]):
            if not isinstance(item, dict):
                continue
            name = safe_text(item.get("name"), "-")
            price = safe_float(item.get("unit_price", item.get("price")), 0.0)
            cost = safe_float(item.get("cost", item.get("trip_cost")), safe_float(data.get("used_kwh"), 0.0) * price)
            item_currency = safe_text(item.get("currency") or item.get("currency_label"), currency)
            color, bg = colors[index % len(colors)]
            if name != "-" and price > 0:
                result.append({"name": name, "price": price, "cost": cost, "currency": item_currency, "color": color, "bg": bg})
    if result:
        return result
    return [
        {"name": "ZES", "price": safe_float(data.get("zes_kwh_price")), "cost": safe_float(data.get("zes_trip_cost")), "currency": currency, "color": COLOR_GREEN, "bg": "#0e241f"},
        {"name": "Supercharger", "price": safe_float(data.get("supercharger_kwh_price")), "cost": safe_float(data.get("supercharger_trip_cost")), "currency": currency, "color": COLOR_RED, "bg": "#271719"},
        {"name": "Astor", "price": safe_float(data.get("astor_kwh_price")), "cost": safe_float(data.get("astor_trip_cost")), "currency": currency, "color": COLOR_YELLOW, "bg": "#2a210f"},
    ]


def has_cost_data(data: dict[str, Any]) -> bool:
    """Return whether cost section has useful data."""
    return bool(cost_presets_from_data(data, currency_label_from_data(data)))


def render_trip_report_png(
    data: dict[str, Any],
    output_path: str = DEFAULT_OUTPUT_PATH,
    lang: str = "tr",
) -> str:
    """Render trip report PNG without Chromium."""
    lang = report_lang(lang or data.get("report_language"))
    tr = trip_t(lang)
    currency = currency_label_from_data(data)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Temporary canvas for text measurements
    temp_image = Image.new("RGB", (760, 1400), COLOR_BG)
    temp_draw = ImageDraw.Draw(temp_image)

    card_x = 20
    card_y = 20
    card_w = 720

    header_h = 132
    row_h = 104
    battery_h = 116 if should_show(data, "show_battery") and has_battery_data(data) else 0
    cost_h = 192 if should_show(data, "show_cost") and has_cost_data(data) else 0

    embedded_map_path = data.get("embedded_map_path")
    has_embedded_map = bool(embedded_map_path and Path(str(embedded_map_path)).exists())
    map_section_h = 352 if has_embedded_map else 0

    main_rows = collect_main_rows(data, lang)
    bottom_info = collect_bottom_info(data, lang)

    bottom_section_h = calculate_bottom_section_height(
        temp_draw,
        bottom_info,
        card_w - 72,
    )

    content_height = (
        header_h
        + map_section_h
        + (len(main_rows) * row_h)
        + battery_h
        + cost_h
        + bottom_section_h
    )

    card_h = content_height
    image_width = 760
    image_height = card_y + card_h + 20

    image = Image.new("RGB", (image_width, image_height), COLOR_BG)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_w, card_y + card_h),
        radius=26,
        fill=COLOR_CARD,
        outline="#2c2d31",
        width=1,
    )

    # Header
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_w, card_y + header_h),
        radius=26,
        fill=COLOR_HEADER,
    )

    draw.rectangle(
        (card_x, card_y + header_h - 26, card_x + card_w, card_y + header_h),
        fill=COLOR_HEADER,
    )

    draw.line(
        (card_x + 24, card_y + header_h, card_x + card_w - 24, card_y + header_h),
        fill=COLOR_LINE,
        width=2,
    )

    date_font = load_font(18, bold=True)
    title_font = load_font(40, bold=True)
    badge_font = load_font(20, bold=True)

    report_date = safe_text(data.get("report_date"))
    title = tr["test_report_title"] if data.get("test_mode") else tr["report_title"]

    draw_safe_text(draw, 
        (card_x + 36, card_y + 30),
        report_date,
        font=date_font,
        fill=COLOR_MUTED_DARK,
    )

    draw_safe_text(draw, 
        (card_x + 36, card_y + 62),
        title,
        font=title_font,
        fill=COLOR_TEXT,
    )

    badge_size = 66
    badge_x = card_x + card_w - 36 - badge_size
    badge_y = card_y + 32

    draw.ellipse(
        (badge_x, badge_y, badge_x + badge_size, badge_y + badge_size),
        fill=COLOR_RED,
    )

    draw_center_text(
        draw,
        badge_x,
        badge_y + 22,
        badge_size,
        "POM",
        badge_font,
        COLOR_TEXT,
    )

    y = card_y + header_h

    if has_embedded_map:
        draw.rectangle(
            (card_x, y, card_x + card_w, y + map_section_h),
            fill=COLOR_SECTION,
        )

        draw.line(
            (card_x + 24, y + map_section_h, card_x + card_w - 24, y + map_section_h),
            fill=COLOR_LINE,
            width=2,
        )

        map_outer_x = card_x + 24
        map_outer_y = y + 16
        map_outer_w = card_w - 48
        map_outer_h = map_section_h - 30

        draw.rounded_rectangle(
            (map_outer_x, map_outer_y, map_outer_x + map_outer_w, map_outer_y + map_outer_h),
            radius=18,
            fill="#17181a",
            outline="#2b2e34",
            width=1,
        )

        map_inner_x = map_outer_x + 8
        map_inner_y = map_outer_y + 8
        map_inner_w = map_outer_w - 16
        map_inner_h = map_outer_h - 16

        prepared_map = load_and_prepare_map_image(embedded_map_path, map_inner_w, map_inner_h)
        if prepared_map is not None:
            mask = Image.new("L", (map_inner_w, map_inner_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, map_inner_w, map_inner_h), radius=14, fill=255)
            image.paste(prepared_map, (map_inner_x, map_inner_y), mask)

            badge_font_small = load_font(18, bold=True)
            badge_text = tr["route_map"]
            badge_w, badge_h = text_size(draw, badge_text, badge_font_small)
            badge_x = map_outer_x + 16
            badge_y = map_outer_y + 14
            draw.rounded_rectangle(
                (badge_x, badge_y, badge_x + badge_w + 18, badge_y + badge_h + 10),
                radius=13,
                fill=(10, 10, 11),
                outline="#ffffff",
                width=1,
            )
            draw_safe_text(draw, (badge_x + 10, badge_y + 5), badge_text, font=badge_font_small, fill=COLOR_TEXT)
        else:
            draw.rounded_rectangle(
                (map_inner_x, map_inner_y, map_inner_x + map_inner_w, map_inner_y + map_inner_h),
                radius=14,
                fill="#111214",
            )
            empty_font = load_font(22, bold=True)
            empty_text = tr["map_load_failed"]
            empty_w, _ = text_size(draw, empty_text, empty_font)
            draw_safe_text(draw, 
                (map_inner_x + (map_inner_w - empty_w) / 2, map_inner_y + map_inner_h / 2 - 12),
                empty_text,
                font=empty_font,
                fill=COLOR_MUTED,
            )

        y += map_section_h

    # Dynamic main rows
    for row in main_rows:
        y = draw_row(
            draw,
            card_x,
            y,
            card_w,
            row_h,
            row["label"],
            row["value"],
            row["unit"],
            row["color"],
        )

    # Battery section
    if battery_h:
        draw.rectangle(
            (card_x, y, card_x + card_w, y + battery_h),
            fill=COLOR_SECTION,
        )

        draw.line(
            (card_x + 24, y, card_x + card_w - 24, y),
            fill=COLOR_LINE,
            width=2,
        )

        draw.line(
            (card_x + 24, y + battery_h, card_x + card_w - 24, y + battery_h),
            fill=COLOR_LINE,
            width=2,
        )

        label_font = load_font(23, bold=True)
        battery_font = load_font(23, bold=True)

        start_battery = safe_float(data.get("start_battery"))
        end_battery = safe_float(data.get("end_battery"))

        battery_text = f"{start_battery:.1f}%  ->  {end_battery:.1f}%"

        draw_safe_text(draw, 
            (card_x + 36, y + 28),
            tr["battery"],
            font=label_font,
            fill=COLOR_MUTED_DARK,
        )

        draw_right_text(
            draw,
            card_x + card_w - 36,
            y + 28,
            battery_text,
            battery_font,
            COLOR_GREEN,
        )

        bar_x = card_x + 36
        bar_y = y + 76
        bar_w = card_w - 72
        bar_h = 9

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
            radius=5,
            fill="#2b2c31",
        )

        fill_ratio = max(4.0, min(100.0, end_battery)) / 100.0
        fill_w = int(bar_w * fill_ratio)

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
            radius=5,
            fill=COLOR_GREEN,
        )

        y += battery_h

    # Cost section
    if cost_h:
        draw.rectangle(
            (card_x, y, card_x + card_w, y + cost_h),
            fill=COLOR_SECTION,
        )

        draw.line(
            (card_x + 24, y, card_x + card_w - 24, y),
            fill=COLOR_LINE,
            width=2,
        )

        draw.line(
            (card_x + 24, y + cost_h, card_x + card_w - 24, y + cost_h),
            fill=COLOR_LINE,
            width=2,
        )

        section_font = load_font(22, bold=True)
        cost_name_font = load_font(20, bold=True)
        cost_price_font = load_font(15, bold=True)
        cost_value_font = load_font(30, bold=True)

        draw_safe_text(draw, 
            (card_x + 36, y + 20),
            tr["cost"],
            font=section_font,
            fill=COLOR_MUTED_DARK,
        )

        cost_items = cost_presets_from_data(data, currency)[:3]

        gap = 12
        small_w = int((card_w - 72 - gap * 2) / 3)
        small_h = 102
        small_y = y + 72

        for index, item in enumerate(cost_items):
            small_x = card_x + 36 + index * (small_w + gap)

            draw.rounded_rectangle(
                (small_x, small_y, small_x + small_w, small_y + small_h),
                radius=16,
                fill=item["bg"],
                outline=item["color"],
                width=1,
            )

            item_currency = safe_text(item.get("currency"), currency)
            price_text = unit_price_text(item["price"], item_currency)
            cost_text = money_text(item["cost"], item_currency)

            draw_center_text(
                draw,
                small_x,
                small_y + 11,
                small_w,
                item["name"],
                cost_name_font,
                COLOR_TEXT,
            )

            draw_center_text(
                draw,
                small_x,
                small_y + 42,
                small_w,
                price_text,
                cost_price_font,
                COLOR_MUTED,
            )

            draw_center_text(
                draw,
                small_x,
                small_y + 68,
                small_w,
                cost_text,
                cost_value_font,
                item["color"],
            )

        y += cost_h

    # Bottom info section only if needed
    if bottom_info:
        draw.rectangle(
            (card_x, y, card_x + card_w, y + bottom_section_h),
            fill=COLOR_HEADER,
        )

        draw.line(
            (card_x + 24, y, card_x + card_w - 24, y),
            fill=COLOR_LINE,
            width=2,
        )

        info_label_font = load_font(19, bold=True)
        info_font = load_font(21, bold=True)

        bottom_x = card_x + 36
        bottom_y = y + 24
        text_max_width = card_w - 72

        for index, (label, value) in enumerate(bottom_info):
            wrapped = wrap_text(draw, value, info_font, text_max_width)
            wrapped = wrapped or ["-"]

            draw_safe_text(
                draw,
                (bottom_x, bottom_y),
                label,
                font=info_label_font,
                fill=COLOR_MUTED_DARK,
            )

            text_y = bottom_y + 27
            for line in wrapped:
                draw_safe_text(
                    draw,
                    (bottom_x, text_y),
                    line,
                    font=info_font,
                    fill=COLOR_MUTED,
                )
                text_y += 27

            bottom_y = text_y + 12
            if index < len(bottom_info) - 1:
                draw.line(
                    (bottom_x, bottom_y - 3, card_x + card_w - 36, bottom_y - 3),
                    fill="#25262b",
                    width=1,
                )

    image.save(output, format="PNG", optimize=True)

    return str(output)
