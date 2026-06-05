"""Monthly trip summary PNG renderer for POM Tesla Report."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

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
GREEN = (102, 224, 132)
RED = (255, 92, 92)
ORANGE = (255, 170, 66)
GRID = (40, 52, 70)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    base = Path(__file__).resolve().parent / "fonts"
    path = base / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(str(path), size=size)
    except Exception:
        pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
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


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match:
        text = match.group(0)
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _report_lang(value: Any) -> str:
    return "en" if str(value or "").strip().lower().startswith("en") else "tr"


def _t(lang: str) -> dict[str, str]:
    if _report_lang(lang) == "en":
        return {
            "title": "POM · TESLA · MONTHLY TRIP SUMMARY",
            "subtitle": "This visual contains the selected period's stored trip records.",
            "page": "Page {page}/{page_count}",
            "month_fallback": "Monthly Trip Summary",
            "total_distance": "Total distance",
            "total_drives": "Total drives",
            "total_energy": "Total energy",
            "total_cost": "Road cost",
            "total_duration": "Total duration",
            "avg_consumption": "Avg. consumption",
            "records": "Trip records",
            "from": "From",
            "to": "To",
            "distance": "Distance",
            "duration": "Duration",
            "energy": "Energy",
            "consumption": "Consumption",
            "cost": "Cost",
            "speed": "Speed M/O",
            "drives": "drives",
            "minutes": "min",
        }
    return {
        "title": "POM · TESLA · AYLIK SÜRÜŞ ÖZETİ",
        "subtitle": "Bu görsel seçili dönemin kaydedilen sürüş kayıtlarını içerir.",
        "page": "Sayfa {page}/{page_count}",
        "month_fallback": "Aylık Sürüş Özeti",
        "total_distance": "Toplam km",
        "total_drives": "Toplam sürüş",
        "total_energy": "Toplam enerji",
        "total_cost": "Yol maliyeti",
        "total_duration": "Toplam süre",
        "avg_consumption": "Ort. tüketim",
        "records": "Sürüş kayıtları",
        "from": "Başlangıç",
        "to": "Bitiş",
        "distance": "Mesafe",
        "duration": "Süre",
        "energy": "Enerji",
        "consumption": "Tüketim",
        "cost": "Maliyet",
        "speed": "Hız H/G",
        "drives": "sürüş",
        "minutes": "dk",
    }


def _month_label(month_key: str, lang: str = "tr") -> str:
    months = {
        "tr": {"01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan", "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos", "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"},
        "en": {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"},
    }[_report_lang(lang)]
    raw = str(month_key or "").strip()
    if len(raw) == 7 and raw[4] == "-":
        year = raw[:4]
        month = raw[5:]
        return f"{months.get(month, month)} {year}"
    return raw or _t(lang)["month_fallback"]


def _currency_label(payload: dict[str, Any] | None = None) -> str:
    label = str((payload or {}).get("currency_label") or (payload or {}).get("report_currency") or "TL").strip()
    return label or "TL"


def _fmt_currency(value: Any, currency: str = "TL") -> str:
    return f"{safe_float(value, 2):.2f} {currency}"


def _fmt_kwh(value: Any) -> str:
    return f"{safe_float(value):.1f} kWh"


def _duration_text(minutes: Any, lang: str = "tr") -> str:
    total = max(0, int(round(safe_float(minutes, 0.0))))
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


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 2) -> list[str]:
    words = str(text or "-").split()
    if not words:
        return ["-"]
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if _text_size(draw, test, font)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and words:
        tail = lines[-1]
        while _text_size(draw, tail + "…", font)[0] > max_width and tail:
            tail = tail[:-1].rstrip()
        lines[-1] = (tail + "…") if tail else "…"
    return lines


def _truncate(draw: ImageDraw.ImageDraw, text: Any, font: ImageFont.ImageFont, max_width: int) -> str:
    """Return a single-line string that always fits into max_width."""
    value = " ".join(str(text or "-").split()) or "-"
    if _text_size(draw, value, font)[0] <= max_width:
        return value
    suffix = "…"
    while value and _text_size(draw, value + suffix, font)[0] > max_width:
        value = value[:-1].rstrip()
    return (value + suffix) if value else suffix


def _draw_header(draw: ImageDraw.ImageDraw, payload: dict[str, Any], *, page_index: int, page_count: int, lang: str) -> int:
    tr = _t(lang)
    month_label = _month_label(str(payload.get("month_key") or ""), lang)
    x = PADDING + 16
    y = PADDING + 24
    draw.text((x, y), tr["title"], font=_font(17, True), fill=(146, 166, 194))
    draw.text((x, y + 40), month_label, font=_font(46, True), fill=TEXT)
    draw.text((x, y + 94), tr["subtitle"], font=_font(20), fill=MUTED)
    pill = (WIDTH - PADDING - 180, y + 34, WIDTH - PADDING - 18, y + 82)
    _rounded_rect(draw, pill, 14, (18, 31, 50), (45, 70, 103), 1)
    _draw_centered(draw, ((pill[0] + pill[2]) // 2, (pill[1] + pill[3]) // 2), tr["page"].format(page=page_index, page_count=page_count), _font(22, True), BLUE)
    return y + 140


def _draw_summary(draw: ImageDraw.ImageDraw, payload: dict[str, Any], top: int, lang: str) -> int:
    tr = _t(lang)
    currency = _currency_label(payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total_distance = safe_float(summary.get("total_distance_km"), 0.0)
    count = int(safe_float(summary.get("count"), 0.0))
    total_energy = safe_float(summary.get("total_energy_kwh"), 0.0)
    total_cost = safe_float(summary.get("total_cost"), 0.0)
    total_minutes = safe_float(summary.get("total_duration_minutes"), 0.0)
    avg_consumption = safe_float(summary.get("average_consumption_kwh_100km"), 0.0)

    row_gap = 18
    card_h = 132
    card_w = (WIDTH - PADDING * 2 - row_gap * 2) // 3
    cards = [
        (tr["total_distance"], f"{total_distance:.1f} km", ""),
        (tr["total_drives"], str(count), tr["drives"]),
        (tr["total_energy"], _fmt_kwh(total_energy), ""),
        (tr["total_cost"], _fmt_currency(total_cost, currency), ""),
        (tr["total_duration"], _duration_text(total_minutes, lang), ""),
        (tr["avg_consumption"], f"{avg_consumption:.2f} kWh/100", ""),
    ]
    for row in range(2):
        for col in range(3):
            idx = row * 3 + col
            x0 = PADDING + col * (card_w + row_gap)
            x1 = x0 + card_w
            y0 = top + row * (card_h + row_gap)
            y1 = y0 + card_h
            _rounded_rect(draw, (x0, y0, x1, y1), 20, PANEL, BORDER, 1)
            label, value, suffix = cards[idx]
            draw.text((x0 + 24, y0 + 22), label, font=_font(22, True), fill=MUTED)
            draw.text((x0 + 24, y0 + 58), value, font=_font(38, True), fill=TEXT)
            if suffix:
                draw.text((x0 + 24 + _text_size(draw, value, _font(38, True))[0] + 8, y0 + 70), suffix, font=_font(24, True), fill=MUTED)
    return top + card_h * 2 + row_gap + 26


def _draw_record(draw: ImageDraw.ImageDraw, record: dict[str, Any], row: tuple[int, int, int, int], *, index_label: str, lang: str) -> None:
    tr = _t(lang)
    x0, y0, x1, y1 = row
    _rounded_rect(draw, row, 18, PANEL_2, BORDER, 1)

    badge = (x0 + 18, y0 + 18, x0 + 62, y0 + 62)
    _rounded_rect(draw, badge, 22, (21, 41, 66), (45, 70, 103), 1)
    _draw_centered(draw, ((badge[0] + badge[2]) // 2, (badge[1] + badge[3]) // 2), index_label, _font(20, True), TEXT)

    display_at = str(record.get("display_at") or record.get("report_date") or "-")
    start_address = str(record.get("start_address") or "-")
    end_address = str(record.get("end_address") or "-")
    trip_km = safe_float(record.get("trip_km"), 0.0)
    used_kwh = safe_float(record.get("used_kwh"), 0.0)
    consumption = safe_float(record.get("consumption_kwh_100km"), 0.0)
    total_cost = safe_float(record.get("total_cost"), 0.0)
    moving_speed = safe_float(record.get("average_moving_speed") or record.get("average_speed"), 0.0)
    overall_speed = safe_float(record.get("average_overall_speed"), 0.0)
    currency = _currency_label(record)
    duration_text = str(record.get("duration_text") or _duration_text(record.get("duration_minutes"), lang) or "-")

    date_font = _font(23, True)
    label_font = _font(16, True)
    addr_font = _font(17)
    metric_label_font = _font(15, True)
    metric_value_font = _font(16, True)

    content_x = x0 + 82
    draw.text((content_x, y0 + 16), display_at, font=date_font, fill=TEXT)

    # Address area is deliberately single-line and clipped. This prevents long
    # Turkish street/neighbourhood names from colliding with the metric grid.
    addr_label_x = content_x
    addr_text_x = content_x + 78
    addr_max_w = max(220, x1 - addr_text_x - 24)
    draw.text((addr_label_x, y0 + 54), tr["from"], font=label_font, fill=MUTED)
    draw.text((addr_text_x, y0 + 54), _truncate(draw, start_address, addr_font, addr_max_w), font=addr_font, fill=TEXT)
    draw.text((addr_label_x, y0 + 80), tr["to"], font=label_font, fill=MUTED)
    draw.text((addr_text_x, y0 + 80), _truncate(draw, end_address, addr_font, addr_max_w), font=addr_font, fill=TEXT)

    # Metric grid: fixed columns, smaller value font and wider gutters so long
    # consumption/speed values never overlap on Telegram-compressed PNGs.
    metrics_y = y0 + 118
    metrics = [
        (tr["distance"], f"{trip_km:.2f} km", BLUE),
        (tr["duration"], duration_text, TEXT),
        (tr["energy"], f"{used_kwh:.2f} kWh", RED),
        (tr["consumption"], f"{consumption:.2f} kWh/100", ORANGE),
        (tr["speed"], f"{moving_speed:.0f}/{overall_speed:.0f} km/sa", BLUE),
        (tr["cost"], _fmt_currency(total_cost, currency), GREEN),
    ]
    left = content_x
    right = x1 - 18
    col_gap = 8
    col_w = (right - left - col_gap * 5) // 6
    for idx, (label, value, color) in enumerate(metrics):
        mx = left + idx * (col_w + col_gap)
        draw.text((mx, metrics_y), _truncate(draw, label, metric_label_font, col_w), font=metric_label_font, fill=MUTED)
        draw.text((mx, metrics_y + 25), _truncate(draw, value, metric_value_font, col_w), font=metric_value_font, fill=color)


def _draw_records_block(draw: ImageDraw.ImageDraw, records: list[dict[str, Any]], top: int, *, page_index: int, start_number: int, lang: str) -> int:
    tr = _t(lang)
    draw.text((PADDING + 4, top), tr["records"], font=_font(29, True), fill=TEXT)
    y = top + 42
    row_h = 174
    gap = 12
    for offset, record in enumerate(records):
        row = (PADDING, y, WIDTH - PADDING, y + row_h)
        _draw_record(draw, record, row, index_label=str(start_number + offset), lang=lang)
        y += row_h + gap
    draw.text((PADDING + 6, HEIGHT - 58), f"{page_index}.", font=_font(18), fill=MUTED)
    return y


def render_monthly_trip_report_pngs(payload: dict[str, Any], output_base_path: str, lang: str = "tr") -> list[str]:
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

    first_page_count = 4
    later_page_count = 6
    pages: list[list[dict[str, Any]]] = [records[:first_page_count]]
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
        y = _draw_header(draw, payload, page_index=page_no, page_count=len(pages), lang=lang)
        if page_no == 1:
            y = _draw_summary(draw, payload, y, lang)
            y += 20
        _draw_records_block(draw, page_records, y, page_index=page_no, start_number=running_index, lang=lang)
        running_index += len(page_records)

        page_path = base.with_name(f"{base.stem}_{page_no}{base.suffix}")
        image.save(page_path, format="PNG", optimize=True)
        outputs.append(str(page_path))

    return outputs
