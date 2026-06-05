"""PNG renderer for POM Tesla charging session reports."""

from __future__ import annotations

from pathlib import Path
import re
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
    candidates = [
        base / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/ttf-dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf"),
        Path("/config/fonts/DejaVuSans-Bold.ttf" if bold else "/config/fonts/DejaVuSans.ttf"),
        Path("/config/www/fonts/DejaVuSans-Bold.ttf" if bold else "/config/www/fonts/DejaVuSans.ttf"),
    ]
    for path in candidates:
        try:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    x, y = xy
    w, h = _text_size(draw, text, font)
    draw.text((x - w / 2, y - h / 2), text, font=font, fill=fill)


def _fmt_float(value: Any, decimals: int = 1, default: str = "-") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if abs(number) < 0.005:
        number = 0.0
    return f"{number:.{decimals}f}"


def _fmt_int(value: Any, default: str = "-") -> str:
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Return a float value, tolerating commas and decorated numeric strings."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    text = text.replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match:
        text = match.group(0)
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _report_lang(value: Any) -> str:
    return "en" if str(value or "").strip().lower().startswith("en") else "tr"


def _charge_t(lang: str) -> dict[str, str]:
    """Static translations for charging visuals."""
    if _report_lang(lang) == "en":
        return {
            "report_header_small": "POM · TESLA · CHARGING REPORT",
            "report_header_big": "Charging Completed.",
            "success": "Success",
            "location_unknown": "Location unavailable",
            "energy_added": "ENERGY ADDED",
            "charged_in": "charged in {duration}",
            "range": "RANGE",
            "estimated": "ESTIMATE",
            "peak_power": "PEAK POWER",
            "curve_title": "Charging Curve",
            "curve_subtitle": "Power output by minute",
            "minutes": "Minutes",
            "no_samples": "No charging power samples",
            "cost_compare": "Cost Comparison",
            "actual_charge": "Actual Charge",
            "note": "Note: Costs are estimated from the added energy and the saved tariff values.",
            "monthly_title": "POM · TESLA · MONTHLY CHARGING SUMMARY",
            "monthly_subtitle": "This visual contains the active month's records.",
            "page": "Page {page}/{page_count}",
            "page_footer": "Page {page}",
            "total_cost": "Total cost",
            "total_energy": "Total energy",
            "session_count": "Charging sessions",
            "avg_energy": "Average energy",
            "avg_cost": "Average cost",
            "avg_unit_price": "Average unit price",
            "sessions": "sessions",
            "charge_records": "Charging records",
            "other": "Other",
            "month_fallback": "Monthly Charging Summary",
        }
    return {
        "report_header_small": "POM · TESLA · ŞARJ RAPORU",
        "report_header_big": "Şarj Tamamlandı.",
        "success": "Başarılı",
        "location_unknown": "Konum yok",
        "energy_added": "EKLENEN ENERJİ",
        "charged_in": "{duration} içinde şarj edildi",
        "range": "MENZİL",
        "estimated": "TAHMİNİ",
        "peak_power": "TEPE GÜÇ",
        "curve_title": "Şarj Eğrisi",
        "curve_subtitle": "Güç çıkışı dakikaya göre",
        "minutes": "Dakika",
        "no_samples": "Şarj gücü örneği yok",
        "cost_compare": "Maliyet Karşılaştırması",
        "actual_charge": "Gerçek Şarj",
        "note": "Not: Maliyetler eklenen enerji ve kayıtlı tarife değerleriyle tahmini hesaplanır.",
        "monthly_title": "POM · TESLA · AYLIK ŞARJ ÖZETİ",
        "monthly_subtitle": "Bu görsel aktif ayın kayıtlarını içerir.",
        "page": "Sayfa {page}/{page_count}",
        "page_footer": "{page}. sayfa",
        "total_cost": "Toplam maliyet",
        "total_energy": "Toplam enerji",
        "session_count": "Şarj sayısı",
        "avg_energy": "Ortalama enerji",
        "avg_cost": "Ortalama maliyet",
        "avg_unit_price": "Ortalama birim fiyat",
        "sessions": "seans",
        "charge_records": "Şarj kayıtları",
        "other": "Diğer",
        "month_fallback": "Aylık Şarj Özeti",
    }




def _currency_label(data: dict[str, Any] | None = None) -> str:
    label = str((data or {}).get("currency_label") or (data or {}).get("report_currency") or "TL").strip()
    return label or "TL"


def _money_text(value: Any, currency: str, decimals: int = 2) -> str:
    return f"{safe_float(value):.{decimals}f} {currency}"


def _unit_price_text(value: Any, currency: str) -> str:
    return f"{safe_float(value):.2f} {currency}/kWh"


def _duration_text(minutes: Any, lang: str = "tr") -> str:
    try:
        total = max(0, int(round(float(minutes))))
    except (TypeError, ValueError):
        total = 0
    if total <= 0:
        return "-"
    hours = total // 60
    mins = total % 60
    if _report_lang(lang) == "en":
        if hours and mins:
            return f"{hours} hr {mins} min"
        if hours:
            return f"{hours} hr"
        return f"{mins} min"
    if hours and mins:
        return f"{hours} sa {mins} dk"
    if hours:
        return f"{hours} sa"
    return f"{mins} dk"


def _draw_header(draw: ImageDraw.ImageDraw, data: dict[str, Any], lang: str = "tr") -> None:
    tr = _charge_t(lang)
    x = PADDING + 16
    y = PADDING + 20
    draw.text((x, y), tr["report_header_small"], font=_font(17, True), fill=(146, 166, 194))
    draw.text((x, y + 46), tr["report_header_big"], font=_font(48, True), fill=TEXT)
    meta = str(data.get("meta") or data.get("finished_at") or "")
    if meta:
        draw.text((x, y + 106), meta, font=_font(21), fill=MUTED)
    location_label = str(data.get("location_label") or data.get("short_location") or "").strip() or tr["location_unknown"]
    pill_w = min(520, max(160, _text_size(draw, location_label, _font(19, True))[0] + 34))
    _rounded_rect(draw, (x, y + 150, x + pill_w, y + 190), 12, (17, 62, 44), (53, 164, 91), 1)
    draw.text((x + 18, y + 158), location_label, font=_font(19, True), fill=(191, 255, 207))

    for i in range(9):
        draw.line((720 + i * 18, 85 + i * 4, 1080, 42 + i * 8), fill=(20, 83, 170, 20 + i * 12), width=3)
    draw.text((1038, 52), "⚡", font=_font(42, True), fill=BLUE)


def _draw_energy_panel(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int, lang: str = "tr") -> int:
    tr = _charge_t(lang)
    box = (PADDING, top, WIDTH - PADDING, top + 360)
    _rounded_rect(draw, box, 22, PANEL, BORDER, 1)
    cx = WIDTH // 2
    label = tr["energy_added"]
    label_font = _font(18, True)
    label_w, _ = _text_size(draw, label, label_font)
    draw.text((cx - label_w / 2, top + 38), label, font=label_font, fill=BLUE)

    added = _fmt_float(data.get("added_kwh"), 1)
    main_font = _font(92, True)
    unit_font = _font(38, False)
    main_w, _ = _text_size(draw, added, main_font)
    draw.text((cx - main_w / 2 - 34, top + 76), added, font=main_font, fill=TEXT)
    draw.text((cx + main_w / 2 - 18, top + 127), "kWh", font=unit_font, fill=(180, 194, 219))

    duration = _duration_text(data.get("duration_minutes"), lang)
    duration_text = tr["charged_in"].format(duration=duration)
    duration_font = _font(22)
    duration_w, _ = _text_size(draw, duration_text, duration_font)
    draw.text((cx - duration_w / 2, top + 200), duration_text, font=duration_font, fill=MUTED)

    sep_y = top + 240
    draw.line((PADDING, sep_y, WIDTH - PADDING, sep_y), fill=(28, 40, 57), width=1)
    col_w = (WIDTH - PADDING * 2) // 3
    labels = [
        (tr["range"], _fmt_int(data.get("battery_range_km")), "km", BLUE),
        (tr["estimated"], _fmt_int(data.get("battery_range_estimate_km")), "km", BLUE),
        (tr["peak_power"], _fmt_float(data.get("peak_power_kw"), 0), "kW", ORANGE),
    ]
    for i, (label, val, unit, color) in enumerate(labels):
        x0 = PADDING + i * col_w
        x1 = x0 + col_w
        col_center_x = (x0 + x1) / 2
        if i:
            draw.line((x0, sep_y + 16, x0, top + 344), fill=(28, 40, 57), width=1)

        metric_label_font = _font(18, True)
        label_w, _ = _text_size(draw, label, metric_label_font)
        draw.text((col_center_x - label_w / 2, sep_y + 22), label, font=metric_label_font, fill=color)

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


def _draw_curve(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int, lang: str = "tr") -> int:
    tr = _charge_t(lang)
    box = (PADDING, top, WIDTH - PADDING, top + 400)
    _rounded_rect(draw, box, 22, (5, 5, 7), BORDER, 1)
    draw.text((PADDING + 34, top + 26), tr["curve_title"], font=_font(31, True), fill=TEXT)
    draw.text((PADDING + 34, top + 66), tr["curve_subtitle"], font=_font(18), fill=MUTED)
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
    minute_label = tr["minutes"]
    minute_w, _ = _text_size(draw, minute_label, _font(21))
    draw.text(((px0 + px1) // 2 - minute_w / 2, py1 + 44), minute_label, font=_font(21), fill=(170, 184, 206))

    if len(parsed) >= 2:
        points = []
        for minute, power in parsed:
            x = px0 + (px1 - px0) * (minute / max_minute)
            y = py1 - (py1 - py0) * (min(power, y_max) / y_max)
            points.append((x, y))
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        gdraw.line(points, fill=(48, 142, 255, 125), width=12, joint="curve")
        gdraw.line(points, fill=(48, 142, 255, 180), width=6, joint="curve")
        _ = glow.filter(ImageFilter.GaussianBlur(5))
        draw.line(points, fill=(35, 118, 225), width=8, joint="curve")
        draw.line(points, fill=(74, 169, 255), width=4, joint="curve")
        last_x, last_y = points[-1]
        draw.ellipse((last_x - 6, last_y - 6, last_x + 6, last_y + 6), fill=(78, 177, 255))
    else:
        _draw_centered(draw, ((px0 + px1) // 2, (py0 + py1) // 2), tr["no_samples"], _font(24, True), MUTED)

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


def _draw_costs(draw: ImageDraw.ImageDraw, data: dict[str, Any], top: int, lang: str = "tr") -> int:
    tr = _charge_t(lang)
    currency = _currency_label(data)
    actual_currency = str(data.get("actual_currency") or data.get("currency_label") or currency).strip() or currency
    actual_provider = str(data.get("actual_provider") or "").strip()
    has_actual = bool(actual_provider)
    box_h = 350 if has_actual else 292
    box = (PADDING, top, WIDTH - PADDING, top + box_h)
    _rounded_rect(draw, box, 22, PANEL, BORDER, 1)
    draw.text((PADDING + 34, top + 24), tr["cost_compare"], font=_font(28, True), fill=TEXT)
    added = float(data.get("added_kwh") or 0.0)

    y = top + 70
    if has_actual:
        actual_price = float(data.get("actual_price_per_kwh") or 0.0)
        actual_total = float(data.get("actual_total_cost") or (added * actual_price if actual_price > 0 else 0.0))
        sub = f"{actual_provider} · {_unit_price_text(actual_price, actual_currency)} · {added:.2f} kWh" if actual_price > 0 else f"{actual_provider} · {added:.2f} kWh"
        _draw_cost_row(
            draw,
            (PADDING + 28, y, WIDTH - PADDING - 28, y + 56),
            tr["actual_charge"],
            sub,
            _money_text(actual_total, actual_currency, decimals=0),
            BLUE,
            highlighted=True,
        )
        y += 64

    preset_rows = []
    raw_presets = data.get("provider_presets") or data.get("cost_presets") or []
    colors = [GREEN, RED, ORANGE]
    if isinstance(raw_presets, list):
        for idx, item in enumerate(raw_presets[:3]):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            price = float(item.get("unit_price") or item.get("price") or 0.0)
            if name and price > 0:
                item_currency = str(item.get("currency") or item.get("currency_label") or currency).strip() or currency
                preset_rows.append((name, price, item_currency, colors[idx % len(colors)]))
    rows = preset_rows or [
        ("ZES", float(data.get("zes_price") or data.get("zes_kwh_price") or 0.0), currency, GREEN),
        ("Supercharger", float(data.get("supercharger_price") or data.get("supercharger_kwh_price") or 0.0), currency, RED),
        ("Astor", float(data.get("astor_price") or data.get("astor_kwh_price") or 0.0), currency, ORANGE),
    ]
    row_h = 50 if has_actual else 58
    gap = 56 if has_actual else 70
    for name, price, row_currency, color in rows:
        row = (PADDING + 28, y, WIDTH - PADDING - 28, y + row_h)
        cost = added * price
        _draw_cost_row(draw, row, name, _unit_price_text(price, row_currency), _money_text(cost, row_currency, decimals=0), color)
        y += gap
    return box[3] + 16


def render_charging_report_png(data: dict[str, Any], output_path: str, lang: str = "tr") -> str:
    """Render a dark POM charging report PNG."""
    lang = _report_lang(lang or data.get("report_language"))
    tr = _charge_t(lang)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(520, 40, -10):
        alpha = max(0, int(38 * (r / 520)))
        od.ellipse((WIDTH - 560 - r, -220 - r, WIDTH - 560 + r, -220 + r), fill=(18, 78, 168, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    outer = (18, 18, WIDTH - 18, HEIGHT - 18)
    _rounded_rect(draw, outer, 30, (3, 3, 4), (33, 45, 64), 1)

    _draw_header(draw, data, lang)
    y = 270
    y = _draw_energy_panel(draw, data, y, lang)
    y = _draw_curve(draw, data, y, lang)
    y = _draw_costs(draw, data, y, lang)

    note_y = min(HEIGHT - 34, y + 6)
    _draw_centered(draw, (WIDTH // 2, note_y), tr["note"], _font(17), MUTED)

    image.save(output, format="PNG", optimize=True)
    return str(output)


def _month_label_from_key(month_key: str, lang: str = "tr") -> str:
    months = {
        "tr": {"01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan", "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos", "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"},
        "en": {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"},
    }[_report_lang(lang)]
    raw = str(month_key or "").strip()
    if len(raw) == 7 and raw[4] == "-":
        year = raw[:4]
        month = raw[5:]
        return f"{months.get(month, month)} {year}"
    return raw or _charge_t(lang)["month_fallback"]


def _fmt_currency(value: Any, currency: str = "TL") -> str:
    return f"{_fmt_float(value, 2)} {currency}"


def _fmt_kwh(value: Any) -> str:
    return f"{_fmt_float(value, 1)} kWh"


def _draw_monthly_header(
    draw: ImageDraw.ImageDraw,
    payload: dict[str, Any],
    *,
    page_index: int,
    page_count: int,
    lang: str = "tr",
) -> int:
    tr = _charge_t(lang)
    month_label = _month_label_from_key(str(payload.get("month_key") or ""), lang)
    x = PADDING + 16
    y = PADDING + 24
    draw.text((x, y), tr["monthly_title"], font=_font(17, True), fill=(146, 166, 194))
    draw.text((x, y + 40), month_label, font=_font(46, True), fill=TEXT)
    draw.text((x, y + 94), tr["monthly_subtitle"], font=_font(20), fill=MUTED)
    pill = (WIDTH - PADDING - 180, y + 34, WIDTH - PADDING - 18, y + 82)
    _rounded_rect(draw, pill, 14, (18, 31, 50), (45, 70, 103), 1)
    page_text = tr["page"].format(page=page_index, page_count=page_count)
    _draw_centered(draw, ((pill[0] + pill[2]) // 2, (pill[1] + pill[3]) // 2), page_text, _font(22, True), BLUE)
    return y + 140


def _draw_monthly_summary(draw: ImageDraw.ImageDraw, payload: dict[str, Any], top: int, lang: str = "tr") -> int:
    tr = _charge_t(lang)
    currency = _currency_label(payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total_cost = safe_float(summary.get("total_cost"), 0.0)
    total_kwh = safe_float(summary.get("total_kwh"), 0.0)
    count = int(safe_float(summary.get("count"), 0.0))
    avg_kwh = total_kwh / count if count > 0 else 0.0
    avg_cost = total_cost / count if count > 0 else 0.0
    avg_unit = total_cost / total_kwh if total_kwh > 0 else 0.0

    row_gap = 18
    card_h = 132
    card_w = (WIDTH - PADDING * 2 - row_gap * 2) // 3
    cards = [
        (tr["total_cost"], _fmt_currency(total_cost, currency), ""),
        (tr["total_energy"], _fmt_kwh(total_kwh), ""),
        (tr["session_count"], str(count), tr["sessions"]),
        (tr["avg_energy"], _fmt_kwh(avg_kwh), ""),
        (tr["avg_cost"], _fmt_currency(avg_cost, currency), ""),
        (tr["avg_unit_price"], _unit_price_text(avg_unit, currency), ""),
    ]
    y = top
    for row in range(2):
        for col in range(3):
            idx = row * 3 + col
            x0 = PADDING + col * (card_w + row_gap)
            x1 = x0 + card_w
            y0 = y + row * (card_h + row_gap)
            y1 = y0 + card_h
            _rounded_rect(draw, (x0, y0, x1, y1), 20, PANEL, BORDER, 1)
            label, value, suffix = cards[idx]
            draw.text((x0 + 24, y0 + 22), label, font=_font(22, True), fill=MUTED)
            draw.text((x0 + 24, y0 + 58), value, font=_font(38, True), fill=TEXT)
            if suffix:
                draw.text((x0 + 24 + _text_size(draw, value, _font(38, True))[0] + 8, y0 + 70), suffix, font=_font(24, True), fill=MUTED)
    return top + card_h * 2 + row_gap + 26


def _record_location_label(record: dict[str, Any]) -> str:
    return str(record.get("location_label") or "").strip()


def _draw_monthly_record_row(
    draw: ImageDraw.ImageDraw,
    record: dict[str, Any],
    row: tuple[int, int, int, int],
    *,
    index_label: str,
    lang: str = "tr",
) -> None:
    tr = _charge_t(lang)
    x0, y0, x1, y1 = row
    _rounded_rect(draw, row, 18, PANEL_2, BORDER, 1)
    badge = (x0 + 18, y0 + 20, x0 + 58, y0 + 60)
    _rounded_rect(draw, badge, 20, (61, 25, 25), (102, 45, 45), 1)
    _draw_centered(draw, ((badge[0] + badge[2]) // 2, (badge[1] + badge[3]) // 2), index_label, _font(20, True), (255, 165, 165))

    provider = str(record.get("provider") or tr["other"])
    display_at = str(record.get("display_at") or record.get("created_at") or "-")
    added_kwh = safe_float(record.get("added_kwh"), 0.0)
    total_cost = safe_float(record.get("total_cost"), 0.0)
    unit_price = safe_float(record.get("price_per_kwh"), 0.0)
    currency = _currency_label(record)
    location = _record_location_label(record)

    draw.text((x0 + 78, y0 + 18), provider, font=_font(28, True), fill=TEXT)
    meta_parts = [display_at]
    if location:
        meta_parts.append(location)
    meta_parts.append(f"{added_kwh:.1f} kWh")
    draw.text((x0 + 78, y0 + 58), "  •  ".join(meta_parts), font=_font(18), fill=MUTED)

    total_text = _money_text(total_cost, currency)
    total_font = _font(34, True)
    total_w, _ = _text_size(draw, total_text, total_font)
    draw.text((x1 - total_w - 26, y0 + 18), total_text, font=total_font, fill=TEXT)
    unit_text = _unit_price_text(unit_price, currency) if unit_price > 0 else "-"
    unit_w, _ = _text_size(draw, unit_text, _font(18))
    draw.text((x1 - unit_w - 26, y0 + 62), unit_text, font=_font(18), fill=MUTED)


def _draw_monthly_records_block(
    draw: ImageDraw.ImageDraw,
    records: list[dict[str, Any]],
    top: int,
    *,
    page_index: int,
    start_number: int,
    lang: str = "tr",
) -> int:
    tr = _charge_t(lang)
    draw.text((PADDING + 4, top), tr["charge_records"], font=_font(29, True), fill=TEXT)
    y = top + 42
    row_h = 106
    gap = 14
    for offset, record in enumerate(records):
        row = (PADDING, y, WIDTH - PADDING, y + row_h)
        _draw_monthly_record_row(draw, record, row, index_label=str(start_number + offset), lang=lang)
        y += row_h + gap
    footer_text = tr["page_footer"].format(page=page_index)
    draw.text((PADDING + 6, HEIGHT - 58), footer_text, font=_font(18), fill=MUTED)
    return y


def render_monthly_charge_cost_report_pngs(payload: dict[str, Any], output_base_path: str, lang: str = "tr") -> list[str]:
    """Render one or more PNG pages for the active month's charging cost summary."""
    lang = _report_lang(lang or payload.get("report_language"))
    currency = _currency_label(payload)
    records = []
    for item in list(payload.get("records") or []):
        if isinstance(item, dict):
            copied = dict(item)
            if not str(copied.get("currency_label") or "").strip():
                copied["currency_label"] = currency
            records.append(copied)
    if not records:
        return []

    first_page_count = 6
    later_page_count = 9
    pages: list[list[dict[str, Any]]] = []
    pages.append(records[:first_page_count])
    remaining = records[first_page_count:]
    for idx in range(0, len(remaining), later_page_count):
        pages.append(remaining[idx:idx + later_page_count])

    base = Path(output_base_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []

    running_index = 1
    for page_no, page_records in enumerate(pages, start=1):
        image = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)

        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for r in range(520, 40, -10):
            alpha = max(0, int(34 * (r / 520)))
            od.ellipse((WIDTH - 560 - r, -220 - r, WIDTH - 560 + r, -220 + r), fill=(18, 78, 168, alpha))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(image)

        _rounded_rect(draw, (18, 18, WIDTH - 18, HEIGHT - 18), 30, (3, 3, 4), (33, 45, 64), 1)
        y = _draw_monthly_header(draw, payload, page_index=page_no, page_count=len(pages), lang=lang)
        if page_no == 1:
            y = _draw_monthly_summary(draw, payload, y, lang)
            y += 20
        _draw_monthly_records_block(draw, page_records, y, page_index=page_no, start_number=running_index, lang=lang)
        running_index += len(page_records)

        page_path = base.with_name(f"{base.stem}_{page_no}{base.suffix}")
        image.save(page_path, format="PNG", optimize=True)
        outputs.append(str(page_path))

    return outputs
