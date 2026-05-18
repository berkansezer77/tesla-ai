"""PNG renderer for POM Tesla Report."""

from __future__ import annotations

from pathlib import Path
import re
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
    ]

    for font_path in fallback_candidates:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def safe_text(value: Any, default: str = "-") -> str:
    """Return safe printable text."""
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    return text


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
    draw.text((x - width, y), text, font=font, fill=fill)


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
    draw.text((x + (width - text_width) / 2, y), text, font=font, fill=fill)


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


def compact_duration_text(value: Any, default: str = "-") -> str:
    """Compact verbose duration text so PNG rows stay visually balanced."""
    text = safe_text(value, default)
    lowered = text.lower()

    if any(phrase in lowered for phrase in ["dakikadan az", "1 dakikadan az", "0 dakika", "0 dk"]):
        return "<1 dk"

    compact = text
    compact = re.sub(r"\b(saat)\b", "sa", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\bdakika\b", "dk", compact, flags=re.IGNORECASE)
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

    draw.text((x + 36, y + 39), label, font=label_font, fill=COLOR_MUTED_DARK)

    value = safe_text(value)
    unit = safe_text(unit, "")
    value_font = choose_value_font(value)

    value_width, _ = text_size(draw, value, value_font)
    unit_width, _ = text_size(draw, unit, unit_font) if unit else (0, 0)

    total_width = value_width + (8 if unit else 0) + unit_width
    right_x = x + width - 36
    start_x = right_x - total_width

    draw.text((start_x, y + 25), value, font=value_font, fill=value_color)

    if unit:
        draw.text(
            (start_x + value_width + 8, y + 51),
            unit,
            font=unit_font,
            fill=COLOR_MUTED,
        )

    return y + height


def collect_main_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    """Collect rows dynamically so hidden/missing fields don't leave broken layout."""
    rows: list[dict[str, str]] = []

    if should_show(data, "show_distance") and is_meaningful(data.get("trip_km")):
        rows.append(
            {
                "label": "Mesafe",
                "value": f"{safe_float(data.get('trip_km')):.2f}",
                "unit": "km",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_duration") and is_meaningful(data.get("duration_text")):
        rows.append(
            {
                "label": "Süre",
                "value": compact_duration_text(data.get("duration_text")),
                "unit": "",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_traffic") and is_meaningful(data.get("traffic_text")):
        rows.append(
            {
                "label": "Trafik",
                "value": compact_duration_text(data.get("traffic_text")),
                "unit": "",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_average_speed") and is_meaningful(data.get("average_speed")):
        rows.append(
            {
                "label": "Ort. hız",
                "value": f"{safe_float(data.get('average_speed')):.1f}",
                "unit": "km/sa",
                "color": COLOR_TEXT,
            }
        )

    if should_show(data, "show_energy") and is_meaningful(data.get("used_kwh")):
        rows.append(
            {
                "label": "Enerji",
                "value": f"{safe_float(data.get('used_kwh')):.2f}",
                "unit": "kWh",
                "color": COLOR_RED,
            }
        )

    if should_show(data, "show_consumption") and is_meaningful(data.get("consumption_kwh_100km")):
        rows.append(
            {
                "label": "Tüketim",
                "value": f"{safe_float(data.get('consumption_kwh_100km')):.2f}",
                "unit": "kWh/100",
                "color": COLOR_TEXT,
            }
        )

    return rows


def collect_bottom_info(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Collect bottom info lines dynamically."""
    items: list[tuple[str, str]] = []

    climate_text = safe_text(data.get("climate_text"), "")
    if should_show(data, "show_climate") and is_meaningful(climate_text):
        items.append(("Klima", climate_text))

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
            f"{safe_float(elevation_range):.0f} m fark"
        )
        items.append(("Rakım", elevation_text))

    return items


def calculate_bottom_section_height(
    draw: ImageDraw.ImageDraw,
    info_items: list[tuple[str, str]],
    content_width: int,
) -> int:
    """Calculate bottom section height dynamically."""
    if not info_items:
        return 0

    info_font = load_font(22, bold=True)

    total_height = 28  # top padding
    label_x_width = 110
    available_width = content_width - label_x_width

    for _, value in info_items:
        wrapped = wrap_text(draw, value, info_font, available_width)
        line_count = max(1, len(wrapped))
        block_height = max(32, line_count * 28)
        total_height += block_height + 12

    total_height += 18  # bottom padding

    return total_height


def has_battery_data(data: dict[str, Any]) -> bool:
    """Return whether battery section has useful data."""
    return is_meaningful(data.get("start_battery")) or is_meaningful(data.get("end_battery"))


def has_cost_data(data: dict[str, Any]) -> bool:
    """Return whether cost section has useful data."""
    return (
        is_meaningful(data.get("zes_trip_cost"))
        or is_meaningful(data.get("supercharger_trip_cost"))
        or is_meaningful(data.get("astor_trip_cost"))
    )


def render_trip_report_png(
    data: dict[str, Any],
    output_path: str = DEFAULT_OUTPUT_PATH,
) -> str:
    """Render trip report PNG without Chromium."""
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

    main_rows = collect_main_rows(data)
    bottom_info = collect_bottom_info(data)

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
    title = "TEST Sürüş Raporu" if data.get("test_mode") else "Sürüş Raporu"

    draw.text(
        (card_x + 36, card_y + 30),
        report_date,
        font=date_font,
        fill=COLOR_MUTED_DARK,
    )

    draw.text(
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
            badge_text = "Rota Haritası"
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
            draw.text((badge_x + 10, badge_y + 5), badge_text, font=badge_font_small, fill=COLOR_TEXT)
        else:
            draw.rounded_rectangle(
                (map_inner_x, map_inner_y, map_inner_x + map_inner_w, map_inner_y + map_inner_h),
                radius=14,
                fill="#111214",
            )
            empty_font = load_font(22, bold=True)
            empty_text = "Harita görseli yüklenemedi"
            empty_w, _ = text_size(draw, empty_text, empty_font)
            draw.text(
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

        draw.text(
            (card_x + 36, y + 28),
            "Batarya",
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

        draw.text(
            (card_x + 36, y + 20),
            "MALİYET",
            font=section_font,
            fill=COLOR_MUTED_DARK,
        )

        cost_items = [
            {
                "name": "ZES",
                "price": safe_float(data.get("zes_kwh_price")),
                "cost": safe_float(data.get("zes_trip_cost")),
                "color": COLOR_GREEN,
                "bg": "#0e241f",
            },
            {
                "name": "Supercharger",
                "price": safe_float(data.get("supercharger_kwh_price")),
                "cost": safe_float(data.get("supercharger_trip_cost")),
                "color": COLOR_RED,
                "bg": "#271719",
            },
            {
                "name": "Astor",
                "price": safe_float(data.get("astor_kwh_price")),
                "cost": safe_float(data.get("astor_trip_cost")),
                "color": COLOR_YELLOW,
                "bg": "#2a210f",
            },
        ]

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

            price_text = f"{item['price']:.2f} TL/kWh"
            cost_text = f"{item['cost']:.2f} TL"

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

        info_label_font = load_font(20, bold=True)
        info_font = load_font(22, bold=True)

        bottom_x = card_x + 36
        bottom_y = y + 28

        label_x_width = 110
        text_max_width = (card_w - 72) - label_x_width

        for label, value in bottom_info:
            wrapped = wrap_text(draw, value, info_font, text_max_width)
            wrapped = wrapped or ["-"]

            draw.text(
                (bottom_x, bottom_y),
                label,
                font=info_label_font,
                fill=COLOR_MUTED_DARK,
            )

            text_y = bottom_y
            for line in wrapped:
                draw.text(
                    (bottom_x + label_x_width, text_y),
                    line,
                    font=info_font,
                    fill=COLOR_MUTED,
                )
                text_y += 28

            block_height = max(32, len(wrapped) * 28)
            bottom_y += block_height + 12

    image.save(output, format="PNG", optimize=True)

    return str(output)
