"""PNG renderer for POM Tesla charging session reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1120
HEIGHT = 1420
PADDING = 34

BG = (0, 0, 0)
PANEL = (6, 6, 8)
PANEL_2 = (10, 10, 12)
BORDER = (32, 48, 72)
TEXT = (248, 250, 255)
MUTED = (155, 166, 186)
BLUE = (69, 163, 255)
BLUE_SOFT = (26, 88, 155)
GREEN = (102, 224, 132)
RED = (255, 92, 92)
ORANGE = (255, 170, 66)
YELLOW = (242, 194, 88)
GRID = (40, 52, 70)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load bundled DejaVu fonts with a safe fallback."""
    base = Path(__file__).resolve().parent / "fonts"
    path = base / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(str(path), size=size)
    except Exception:
        return ImageFont.load_default()


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int]) -> None:
    x, y = xy
    w, h = _text_size(draw, text, font)
    draw.text((x - w / 2, y - h / 2), text, font=font, fill=fill)


def _fmt_float(value: Any, decimals: int = 1, default: str = "—") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if abs(number) < 0.005:
        number = 0.0
    return f"{number:.{decimals}f}"


def _fmt_int(value: Any, default: str = "—") -> str:
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return default


def _duration_text(minutes: Any) -> str:
    try:
        total = max(0, int(round(float(minutes))))
    except (TypeError, ValueError):
        total = 0
    if total <= 0:
        return "—"
    hours = total // 60
    mins = total % 60
    if hours and mins:
        return f"{hours} sa {mins} dk"
    if hours:
        return f"{hours} sa"
    return f"{mins} dk"


def _draw_header(draw: ImageDraw.ImageDraw, data: dict[str, Any]) -> None:
    x = PADDING + 16
    y = PADDING + 20
    draw.text((x, y), "POM · TESLA · ŞARJ RAPORU", font=_font(17, True), fill=(146, 166, 194))
    draw.text((x, y + 46), "Şarj Tamamlandı.", font=_font(48, True), fill=TEXT)
    meta = str(data.get("meta") or data.get("finished_at") or "")
    if meta:
        draw.text((x, y + 106), meta, font=_font(21), fill=MUTED)
    _rounded_rect(draw, (x, y + 150, x + 145, y + 190), 12, (17, 62, 44), (53, 164, 91), 1)
    draw.text((x + 18, y + 158), "✓ Başarılı", font=_font(19, True), fill=(191, 255, 207))

    # soft electric streak
    for i in range(9):
        draw.line((720 + i * 18, 85 + i * 4, 1080, 42 + i * 8), fill=(20, 83, 170, 20 + i * 12), width=3)
    draw.text((1038, 52), "⚡", font=_font(42, True), fill=BLUE)


def _draw_energy_panel(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int) -> int:
    box = (PADDING, top, WIDTH - PADDING, top + 360)
    _rounded_rect(draw, box, 22, PANEL, BORDER, 1)
    cx = WIDTH // 2
    draw.text((cx - 118, top + 38), "E K L E N E N   E N E R J İ", font=_font(18, True), fill=BLUE)

    added = _fmt_float(data.get("added_kwh"), 1)
    main_font = _font(92, True)
    unit_font = _font(38, False)
    main_w, _ = _text_size(draw, added, main_font)
    draw.text((cx - main_w / 2 - 34, top + 76), added, font=main_font, fill=TEXT)
    draw.text((cx + main_w / 2 - 18, top + 127), "kWh", font=unit_font, fill=(180, 194, 219))

    duration = _duration_text(data.get("duration_minutes"))
    draw.text((cx - 148, top + 200), f"{duration} içinde şarj edildi", font=_font(22), fill=MUTED)

    # bottom metrics
    sep_y = top + 240
    draw.line((PADDING, sep_y, WIDTH - PADDING, sep_y), fill=(28, 40, 57), width=1)
    col_w = (WIDTH - PADDING * 2) // 3
    labels = [
        ("MENZİL", _fmt_int(data.get("battery_range_km")), "km", BLUE),
        ("TAHMİNİ", _fmt_int(data.get("battery_range_estimate_km")), "km", BLUE),
        ("TEPE GÜÇ", _fmt_float(data.get("peak_power_kw"), 0), "kW", ORANGE),
    ]
    for i, (label, val, unit, color) in enumerate(labels):
        x0 = PADDING + i * col_w
        x1 = x0 + col_w
        col_center_x = (x0 + x1) / 2
        if i:
            draw.line((x0, sep_y + 16, x0, top + 344), fill=(28, 40, 57), width=1)

        # center the label inside each metric box
        label_font = _font(18, True)
        label_w, _ = _text_size(draw, label, label_font)
        draw.text((col_center_x - label_w / 2, sep_y + 22), label, font=label_font, fill=color)

        # center the value+unit group inside each metric box
        value_font = _font(40, True)
        unit_font = _font(22)
        value_w, value_h = _text_size(draw, val, value_font)
        unit_w, unit_h = _text_size(draw, unit, unit_font)
        gap = 8
        group_w = value_w + gap + unit_w
        start_x = col_center_x - group_w / 2
        value_y = sep_y + 54
        unit_y = value_y + max(0, value_h - unit_h - 2)
        draw.text((start_x, value_y), val, font=value_font, fill=TEXT if i < 2 else color)
        draw.text((start_x + value_w + gap, unit_y), unit, font=unit_font, fill=(184, 197, 218))
    return box[3] + 18


def _nice_ymax(max_power: float) -> int:
    if max_power <= 0:
        return 50
    for candidate in [25, 50, 75, 100, 125, 150, 200, 250, 300, 350, 400]:
        if max_power <= candidate:
            return candidate
    return int(((max_power + 49) // 50) * 50)


def _draw_curve(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int) -> int:
    box = (PADDING, top, WIDTH - PADDING, top + 400)
    _rounded_rect(draw, box, 22, (5, 5, 7), BORDER, 1)
    draw.text((PADDING + 34, top + 26), "Şarj Eğrisi", font=_font(31, True), fill=TEXT)
    draw.text((PADDING + 34, top + 66), "Güç çıkışı dakikaya göre", font=_font(18), fill=MUTED)
    _rounded_rect(draw, (WIDTH - PADDING - 86, top + 30, WIDTH - PADDING - 34, top + 68), 10, (18, 31, 50), (45, 70, 103), 1)
    draw.text((WIDTH - PADDING - 70, top + 38), "kW", font=_font(16, True), fill=MUTED)

    plot = (PADDING + 72, top + 118, WIDTH - PADDING - 58, top + 340)
    px0, py0, px1, py1 = plot
    samples = data.get("power_samples") or []
    parsed: list[tuple[float, float]] = []
    for item in samples:
        try:
            minute = float(item.get("minute")) if isinstance(item, dict) else float(item[0])
            power = float(item.get("power_kw")) if isinstance(item, dict) else float(item[1])
        except Exception:
            continue
        if minute >= 0 and power >= 0:
            parsed.append((minute, power))
    parsed.sort(key=lambda p: p[0])

    max_minute = max(float(data.get("duration_minutes") or 0), parsed[-1][0] if parsed else 0, 10.0)
    max_power = max([p for _, p in parsed], default=float(data.get("peak_power_kw") or 0))
    y_max = _nice_ymax(max_power)

    # grid
    for i in range(6):
        y = py1 - (py1 - py0) * i / 5
        draw.line((px0, y, px1, y), fill=GRID, width=1)
        val = int(y_max * i / 5)
        draw.text((px0 - 54, y - 11), str(val), font=_font(17), fill=(170, 184, 206))
    for i in range(0, 10):
        x = px0 + (px1 - px0) * i / 9
        draw.line((x, py0, x, py1), fill=(24, 35, 51), width=1)
        minute_label = int(round(max_minute * i / 9))
        draw.text((x - 10, py1 + 12), str(minute_label), font=_font(17), fill=(170, 184, 206))

    draw.line((px0, py0, px0, py1), fill=(124, 142, 165), width=2)
    draw.line((px0, py1, px1, py1), fill=(124, 142, 165), width=2)
    draw.text((px0 - 38, py0 - 30), "kW", font=_font(18), fill=(170, 184, 206))
    draw.text(((px0 + px1) // 2 - 34, py1 + 44), "Dakika", font=_font(21), fill=(170, 184, 206))

    if len(parsed) >= 2:
        points = []
        for minute, power in parsed:
            x = px0 + (px1 - px0) * (minute / max_minute)
            y = py1 - (py1 - py0) * (min(power, y_max) / y_max)
            points.append((x, y))
        # glow layer
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        gdraw.line(points, fill=(48, 142, 255, 125), width=12, joint="curve")
        gdraw.line(points, fill=(48, 142, 255, 180), width=6, joint="curve")
        blurred = glow.filter(ImageFilter.GaussianBlur(5))
        # caller draws on base; paste will be handled by composite impossible here with draw only.
        # Use regular line plus translucent fill instead.
        draw.line(points, fill=(35, 118, 225), width=8, joint="curve")
        draw.line(points, fill=(74, 169, 255), width=4, joint="curve")
        last_x, last_y = points[-1]
        draw.ellipse((last_x - 6, last_y - 6, last_x + 6, last_y + 6), fill=(78, 177, 255))
    else:
        _draw_centered(draw, ((px0 + px1) // 2, (py0 + py1) // 2), "Şarj gücü örneği yok", _font(24, True), MUTED)

    return box[3] + 18


def _draw_cost_row(
    draw: ImageDraw.ImageDraw,
    row: tuple[int, int, int, int],
    name: str,
    sub_text: str,
    cost_text: str,
    color: tuple[int, int, int],
    *,
    highlighted: bool = False,
) -> None:
    x0, y0, x1, y1 = row
    fill = (8, 12, 18) if highlighted else (4, 4, 6)
    outline = color if highlighted else (28, 42, 62)
    _rounded_rect(draw, row, 14, fill, outline, 1)
    draw.text((x0 + 24, y0 + 10), name, font=_font(22, True), fill=TEXT)
    draw.text((x0 + 24, y0 + 36), sub_text, font=_font(15), fill=MUTED)
    cost_font = _font(31, True) if highlighted else _font(30, True)
    tw, _ = _text_size(draw, cost_text, cost_font)
    draw.text((x1 - tw - 22, y0 + 11), cost_text, font=cost_font, fill=color)


def _draw_costs(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int) -> int:
    actual_provider = str(data.get("actual_provider") or "").strip()
    has_actual = bool(actual_provider)
    box_h = 350 if has_actual else 292
    box = (PADDING, top, WIDTH - PADDING, top + box_h)
    _rounded_rect(draw, box, 22, PANEL, BORDER, 1)
    draw.text((PADDING + 34, top + 24), "Maliyet Karşılaştırması", font=_font(28, True), fill=TEXT)
    added = float(data.get("added_kwh") or 0.0)

    y = top + 70
    if has_actual:
        actual_price = float(data.get("actual_price_per_kwh") or 0.0)
        actual_total = float(data.get("actual_total_cost") or (added * actual_price if actual_price > 0 else 0.0))
        sub = f"{actual_provider} · {actual_price:.2f} TL/kWh · {added:.2f} kWh" if actual_price > 0 else f"{actual_provider} · {added:.2f} kWh"
        _draw_cost_row(
            draw,
            (PADDING + 28, y, WIDTH - PADDING - 28, y + 56),
            "Gerçek Şarj",
            sub,
            f"{actual_total:.0f} TL",
            BLUE,
            highlighted=True,
        )
        y += 64

    rows = [
        ("ZES", float(data.get("zes_price") or 0.0), GREEN),
        ("Supercharger", float(data.get("supercharger_price") or 0.0), RED),
        ("Astor", float(data.get("astor_price") or 0.0), ORANGE),
    ]
    row_h = 50 if has_actual else 58
    gap = 56 if has_actual else 70
    for name, price, color in rows:
        row = (PADDING + 28, y, WIDTH - PADDING - 28, y + row_h)
        cost = added * price
        _draw_cost_row(
            draw,
            row,
            name,
            f"{price:.2f} TL/kWh",
            f"{cost:.0f} TL",
            color,
        )
        y += gap
    return box[3] + 16


def render_charging_report_png(data: dict[str, Any], output_path: str) -> str:
    """Render a dark POM charging report PNG."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # subtle background gradient
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(520, 40, -10):
        alpha = max(0, int(38 * (r / 520)))
        od.ellipse((WIDTH - 560 - r, -220 - r, WIDTH - 560 + r, -220 + r), fill=(18, 78, 168, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    outer = (18, 18, WIDTH - 18, HEIGHT - 18)
    _rounded_rect(draw, outer, 30, (3, 3, 4), (33, 45, 64), 1)

    _draw_header(draw, data)
    y = 270
    y = _draw_energy_panel(draw, data, y)
    y = _draw_curve(draw, data, y)
    y = _draw_costs(draw, data, y)

    note = "Not: Maliyetler eklenen enerji ve kayıtlı tarife değerleriyle tahmini hesaplanır."
    note_y = min(HEIGHT - 34, y + 6)
    _draw_centered(draw, (WIDTH // 2, note_y), note, _font(17), MUTED)

    image.save(output, format="PNG", optimize=True)
    return str(output)
