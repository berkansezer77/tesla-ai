"""Light vehicle location map renderer for POM Tesla Report."""

from __future__ import annotations

import math
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

WIDTH = 1280
HEIGHT = 780
TILE_SIZE = 256
USER_AGENT = "POMTeslaReport/1.2 (Home Assistant custom integration)"
HTTP_TIMEOUT_SECONDS = 3.0

BG = "#f4f7fb"
CARD = "#ffffff"
TEXT = "#0f172a"
MUTED = "#64748b"
BLUE = "#2563eb"
RED = "#ef4444"
GRID = "#d8e0ea"


def _font(size: int, bold: bool = False):
    font_dir = Path(__file__).parent / "fonts"
    path = font_dir / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _latlon_to_world_pixels(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    lat = _clip(lat, -85.05112878, 85.05112878)
    lon = _clip(lon, -180.0, 180.0)
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n * TILE_SIZE
    return x, y


def _tile_cache_path(cache_dir: Path, zoom: int, x: int, y: int) -> Path:
    return cache_dir / "osm_light" / str(zoom) / str(x) / f"{y}.png"


def _fetch_light_tile(cache_dir: Path, zoom: int, x: int, y: int) -> Image.Image:
    tiles_per_axis = 2 ** zoom
    x = x % tiles_per_axis
    y = int(_clip(y, 0, tiles_per_axis - 1))
    cache_path = _tile_cache_path(cache_dir, zoom, x, y)
    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGB")
        except Exception:
            pass

    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
        raw = response.read()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(raw)

    tile = Image.open(BytesIO(raw)).convert("RGB")
    # Keep it day/light but improve label-road contrast very slightly.
    tile = ImageEnhance.Color(tile).enhance(0.95)
    tile = ImageEnhance.Contrast(tile).enhance(1.06)
    return tile


def _fallback_light_tile() -> Image.Image:
    tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), "#eef2f7")
    d = ImageDraw.Draw(tile)
    for x in range(0, TILE_SIZE, 32):
        d.line((x, 0, x, TILE_SIZE), fill="#d7dee8", width=1)
    for y in range(0, TILE_SIZE, 32):
        d.line((0, y, TILE_SIZE, y), fill="#d7dee8", width=1)
    d.line((0, 0, TILE_SIZE, TILE_SIZE), fill="#cbd5e1", width=2)
    d.line((TILE_SIZE, 0, 0, TILE_SIZE), fill="#cbd5e1", width=2)
    return tile


def _render_light_map(lat: float, lon: float, width: int, height: int, cache_dir: Path, zoom: int = 16) -> Image.Image:
    center_x, center_y = _latlon_to_world_pixels(lat, lon, zoom)
    viewport_left = center_x - width / 2
    viewport_top = center_y - height / 2
    viewport_right = center_x + width / 2
    viewport_bottom = center_y + height / 2

    tile_x_start = int(math.floor(viewport_left / TILE_SIZE))
    tile_y_start = int(math.floor(viewport_top / TILE_SIZE))
    tile_x_end = int(math.floor(viewport_right / TILE_SIZE))
    tile_y_end = int(math.floor(viewport_bottom / TILE_SIZE))

    canvas = Image.new(
        "RGB",
        ((tile_x_end - tile_x_start + 1) * TILE_SIZE, (tile_y_end - tile_y_start + 1) * TILE_SIZE),
        "#eef2f7",
    )

    network_failed = False
    for ty in range(tile_y_start, tile_y_end + 1):
        for tx in range(tile_x_start, tile_x_end + 1):
            if network_failed:
                tile = _fallback_light_tile()
            else:
                try:
                    tile = _fetch_light_tile(cache_dir, zoom, tx, ty)
                except Exception:
                    network_failed = True
                    tile = _fallback_light_tile()
            px = (tx - tile_x_start) * TILE_SIZE
            py = (ty - tile_y_start) * TILE_SIZE
            canvas.paste(tile, (px, py))

    crop_left = int(viewport_left - tile_x_start * TILE_SIZE)
    crop_top = int(viewport_top - tile_y_start * TILE_SIZE)
    cropped = canvas.crop((crop_left, crop_top, crop_left + width, crop_top + height))

    # Day mode: preserve readable streets/labels.
    cropped = ImageEnhance.Brightness(cropped).enhance(1.02)
    cropped = ImageEnhance.Contrast(cropped).enhance(1.04)
    return cropped


def _draw_marker(draw: ImageDraw.ImageDraw, x: float, y: float) -> None:
    # Blue glow
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius, alpha in [(70, 35), (52, 55), (34, 85)]:
        gd.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(56, 189, 248, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    # Caller composites glow separately by using alpha_composite when possible.
    draw.bitmap((0, 0), glow.split()[-1], fill=(56, 189, 248, 55))

    # Pin body
    draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=RED, outline="#ffffff", width=5)
    draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill="#ffffff")
    draw.polygon([(x, y + 42), (x - 14, y + 16), (x + 14, y + 16)], fill=RED)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 2) -> list[str]:
    words = str(text or "").split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
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
    if len(lines) == max_lines:
        while lines[-1] and draw.textbbox((0, 0), lines[-1] + "…", font=font)[2] > max_width:
            lines[-1] = lines[-1][:-1].rstrip()
        if lines[-1]:
            lines[-1] += "…"
    return lines


def render_vehicle_location_map_png(data: dict[str, Any], output_path: str) -> str:
    """Render a light/day-mode single-point vehicle location map."""
    lat = float(data["lat"])
    lon = float(data["lon"])
    address = str(data.get("address") or "").strip()
    title = str(data.get("title") or "Vehicle Location").strip()
    subtitle = str(data.get("subtitle") or f"{lat:.5f}, {lon:.5f}").strip()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cache_dir = out.parent / ".tile_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=38, fill=CARD, outline="#d6dee8", width=2)

    map_left, map_top, map_right, map_bottom = 46, 46, WIDTH - 46, HEIGHT - 170
    map_w = map_right - map_left
    map_h = map_bottom - map_top

    try:
        bg_map = _render_light_map(lat, lon, map_w, map_h, cache_dir)
    except Exception:
        bg_map = Image.new("RGB", (map_w, map_h), "#eef2f7")
        gd = ImageDraw.Draw(bg_map)
        for x in range(0, map_w, 64):
            gd.line((x, 0, x, map_h), fill=GRID, width=1)
        for y in range(0, map_h, 64):
            gd.line((0, y, map_w, y), fill=GRID, width=1)

    mask = Image.new("L", (map_w, map_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, map_w, map_h), radius=28, fill=255)
    image.paste(bg_map, (map_left, map_top), mask)

    # Vignette overlay
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((map_left, map_top, map_right, map_bottom), fill=(255, 255, 255, 0))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    marker_x = (map_left + map_right) / 2
    marker_y = (map_top + map_bottom) / 2 - 8
    _draw_marker(draw, marker_x, marker_y)

    panel_top = HEIGHT - 150
    draw.rounded_rectangle((46, panel_top, WIDTH - 46, HEIGHT - 44), radius=26, fill="#ffffff", outline="#d6dee8", width=2)
    draw.text((76, panel_top + 22), title, font=_font(34, bold=True), fill=TEXT)
    draw.text((76, panel_top + 62), subtitle, font=_font(20), fill=MUTED)

    if address:
        addr_font = _font(22, bold=True)
        lines = _wrap_text(draw, address, addr_font, WIDTH - 520, max_lines=2)
        y = panel_top + 22
        for line in lines:
            draw.text((430, y), line, font=addr_font, fill=TEXT)
            y += 29

    attr = "© OpenStreetMap contributors"
    attr_font = _font(16)
    bbox = draw.textbbox((0, 0), attr, font=attr_font)
    draw.rounded_rectangle((WIDTH - 46 - (bbox[2] - bbox[0]) - 24, map_bottom - 32, WIDTH - 56, map_bottom - 8), radius=10, fill=(255, 255, 255))
    draw.text((WIDTH - 46 - (bbox[2] - bbox[0]) - 14, map_bottom - 29), attr, font=attr_font, fill="#475569")

    image.save(out, format="PNG", optimize=True)
    return str(out)
