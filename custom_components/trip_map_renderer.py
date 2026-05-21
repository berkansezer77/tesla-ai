"""Trip map PNG renderer for POM Tesla Report with OpenStreetMap background."""

from __future__ import annotations

import math
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1400
HEIGHT = 1000
BG = "#f5f7fb"
CARD = "#ffffff"
TEXT = "#0f172a"
MUTED = "#64748b"
LINE = "#1d4ed8"
LINE_GLOW = "#93c5fd"
START = "#16a34a"
END = "#dc2626"
GRID = "#e2e8f0"
MAP_BG = "#eef2f7"
TILE_SIZE = 256
USER_AGENT = "POMTeslaReport/0.8 (Home Assistant custom integration)"
HTTP_TIMEOUT_SECONDS = 3.0


def _font(size: int, bold: bool = False):
    font_dir = Path(__file__).parent / "fonts"
    path = font_dir / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _normalize_points(points_raw: list[Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for item in points_raw:
        try:
            lat = float(item[0])
            lon = float(item[1])
            points.append((_clip(lat, -85.05112878, 85.05112878), _clip(lon, -180.0, 180.0)))
        except Exception:
            continue
    return points


def _latlon_to_world_pixels(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    lat_rad = math.radians(_clip(lat, -85.05112878, 85.05112878))
    n = 2**zoom
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n * TILE_SIZE
    return x, y


def _zoom_for_bbox(points: list[tuple[float, float]], width: int, height: int) -> int:
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_span = max(max_lat - min_lat, 0.003)
    lon_span = max(max_lon - min_lon, 0.003)
    pad = 1.25
    lat_span *= pad
    lon_span *= pad

    best = 14
    for zoom in range(18, 1, -1):
        _, top = _latlon_to_world_pixels(max_lat + lat_span * 0.15, min_lon, zoom)
        _, bottom = _latlon_to_world_pixels(min_lat - lat_span * 0.15, min_lon, zoom)
        left, _ = _latlon_to_world_pixels(min_lat, min_lon - lon_span * 0.15, zoom)
        right, _ = _latlon_to_world_pixels(min_lat, max_lon + lon_span * 0.15, zoom)
        pixel_w = abs(right - left)
        pixel_h = abs(bottom - top)
        if pixel_w <= width * 0.82 and pixel_h <= height * 0.82:
            best = zoom
            break
    return best


def _tile_cache_path(cache_dir: Path, zoom: int, x: int, y: int) -> Path:
    return cache_dir / str(zoom) / str(x) / f"{y}.png"


def _fetch_tile(cache_dir: Path, zoom: int, x: int, y: int) -> Image.Image:
    tiles_per_axis = 2**zoom
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
    return Image.open(BytesIO(raw)).convert("RGB")


def _render_osm_background(points: list[tuple[float, float]], width: int, height: int, cache_dir: Path) -> tuple[Image.Image, list[tuple[float, float]]]:
    if not points:
        background = Image.new("RGB", (width, height), MAP_BG)
        return background, []

    if len(points) == 1:
        points = [points[0], points[0]]

    zoom = _zoom_for_bbox(points, width, height)
    world_pixels = [_latlon_to_world_pixels(lat, lon, zoom) for lat, lon in points]
    xs = [p[0] for p in world_pixels]
    ys = [p[1] for p in world_pixels]
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2

    viewport_left = center_x - width / 2
    viewport_top = center_y - height / 2
    viewport_right = center_x + width / 2
    viewport_bottom = center_y + height / 2

    tile_x_start = int(math.floor(viewport_left / TILE_SIZE))
    tile_y_start = int(math.floor(viewport_top / TILE_SIZE))
    tile_x_end = int(math.floor(viewport_right / TILE_SIZE))
    tile_y_end = int(math.floor(viewport_bottom / TILE_SIZE))

    canvas = Image.new("RGB", ((tile_x_end - tile_x_start + 1) * TILE_SIZE, (tile_y_end - tile_y_start + 1) * TILE_SIZE), MAP_BG)

    network_failed = False

    for ty in range(tile_y_start, tile_y_end + 1):
        for tx in range(tile_x_start, tile_x_end + 1):
            if network_failed:
                tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), "#e5e7eb")
                td = ImageDraw.Draw(tile)
                td.line((0, 0, TILE_SIZE, TILE_SIZE), fill="#cbd5e1", width=2)
                td.line((TILE_SIZE, 0, 0, TILE_SIZE), fill="#cbd5e1", width=2)
            else:
                try:
                    tile = _fetch_tile(cache_dir, zoom, tx, ty)
                except Exception:
                    network_failed = True
                    tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), "#e5e7eb")
                    td = ImageDraw.Draw(tile)
                    td.line((0, 0, TILE_SIZE, TILE_SIZE), fill="#cbd5e1", width=2)
                    td.line((TILE_SIZE, 0, 0, TILE_SIZE), fill="#cbd5e1", width=2)
            px = (tx - tile_x_start) * TILE_SIZE
            py = (ty - tile_y_start) * TILE_SIZE
            canvas.paste(tile, (px, py))

    crop_left = int(viewport_left - tile_x_start * TILE_SIZE)
    crop_top = int(viewport_top - tile_y_start * TILE_SIZE)
    cropped = canvas.crop((crop_left, crop_top, crop_left + width, crop_top + height))

    projected = [(x - viewport_left, y - viewport_top) for x, y in world_pixels]
    return cropped, projected


def _draw_marker(draw: ImageDraw.ImageDraw, x: float, y: float, color: str, label: str) -> None:
    draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=color, outline="#ffffff", width=4)
    font = _font(20, bold=True)
    bbox = draw.textbbox((0, 0), label, font=font)
    label_w = bbox[2] - bbox[0]
    label_h = bbox[3] - bbox[1]
    rect_left = x + 18
    rect_top = y - label_h - 8
    rect_right = rect_left + label_w + 16
    rect_bottom = rect_top + label_h + 8
    draw.rounded_rectangle((rect_left, rect_top, rect_right, rect_bottom), radius=10, fill="#ffffff", outline=color, width=2)
    draw.text((rect_left + 8, rect_top + 4), label, font=font, fill=color)


def _draw_route_map(draw: ImageDraw.ImageDraw, map_img: Image.Image, projected_points: list[tuple[float, float]]) -> None:
    if not projected_points:
        return
    if len(projected_points) >= 2:
        draw.line(projected_points, fill=LINE_GLOW, width=16, joint="curve")
        draw.line(projected_points, fill=LINE, width=7, joint="curve")
    sx, sy = projected_points[0]
    ex, ey = projected_points[-1]
    _draw_marker(draw, sx, sy, START, "START")
    _draw_marker(draw, ex, ey, END, "FINISH")


def render_trip_map_png(data: dict[str, Any], output_path: str) -> str:
    """Render a route map png with OpenStreetMap background and return output path."""
    points = _normalize_points(data.get("points") or [])

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=34, fill=CARD)
    title_font = _font(44, bold=True)
    sub_font = _font(24)
    draw.text((60, 52), data.get("title", "POM Tesla Report - Sürüş Haritası"), font=title_font, fill=TEXT)

    subtitle_parts = []
    if data.get("trip_km") is not None:
        subtitle_parts.append(f"Mesafe: {data.get('trip_km')} km")
    if data.get("duration_text"):
        subtitle_parts.append(f"Süre: {data.get('duration_text')}")
    subtitle_parts.append(f"Nokta: {len(points)}")
    draw.text((60, 108), "  •  ".join(subtitle_parts), font=sub_font, fill=MUTED)

    map_left, map_top, map_right, map_bottom = 50, 170, WIDTH - 50, HEIGHT - 90
    map_w = map_right - map_left
    map_h = map_bottom - map_top
    draw.rounded_rectangle((map_left, map_top, map_right, map_bottom), radius=24, fill="#f8fafc", outline=GRID, width=2)

    inner_left, inner_top, inner_right, inner_bottom = map_left + 18, map_top + 18, map_right - 18, map_bottom - 18
    inner_w = inner_right - inner_left
    inner_h = inner_bottom - inner_top

    cache_dir = Path(output_path).parent / ".tile_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    projected: list[tuple[float, float]] = []
    try:
        bg_map, projected = _render_osm_background(points, inner_w, inner_h, cache_dir)
    except Exception:
        bg_map = Image.new("RGB", (inner_w, inner_h), MAP_BG)
        gd = ImageDraw.Draw(bg_map)
        for i in range(6):
            x = (inner_w) * i / 5
            gd.line((x, 0, x, inner_h), fill=GRID, width=1)
        for i in range(5):
            y = (inner_h) * i / 4
            gd.line((0, y, inner_w, y), fill=GRID, width=1)
        # fallback projection on blank plane
        if points:
            lats = [p[0] for p in points]
            lons = [p[1] for p in points]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            lat_span = max(max_lat - min_lat, 0.002)
            lon_span = max(max_lon - min_lon, 0.002)
            projected = []
            for lat, lon in points:
                x = ((lon - min_lon) / lon_span) * (inner_w - 80) + 40
                y = (1 - ((lat - min_lat) / lat_span)) * (inner_h - 80) + 40
                projected.append((x, y))

    mask = Image.new("L", (inner_w, inner_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, inner_w, inner_h), radius=20, fill=255)
    image.paste(bg_map, (inner_left, inner_top), mask)

    route_layer = Image.new("RGBA", (inner_w, inner_h), (255, 255, 255, 0))
    route_draw = ImageDraw.Draw(route_layer)
    if len(projected) >= 1:
        _draw_route_map(route_draw, bg_map, projected)
    image.alpha_composite(route_layer, (inner_left, inner_top)) if image.mode == "RGBA" else image.paste(route_layer, (inner_left, inner_top), route_layer)

    if not points:
        msg = "Harita üretmek için yeterli rota noktası toplanamadı."
        bbox = draw.textbbox((0, 0), msg, font=_font(28, bold=True))
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) / 2, map_top + 220), msg, font=_font(28, bold=True), fill=MUTED)

    attribution = "Harita: © OpenStreetMap contributors"
    bbox = draw.textbbox((0, 0), attribution, font=_font(18))
    attr_w = bbox[2] - bbox[0]
    draw.rounded_rectangle((inner_right - attr_w - 26, inner_bottom - 34, inner_right - 10, inner_bottom - 8), radius=10, fill=(255, 255, 255))
    draw.text((inner_right - attr_w - 18, inner_bottom - 30), attribution, font=_font(18), fill=MUTED)

    footer = data.get("footer") or "Tesla konum verilerinden oluşturuldu"
    draw.text((60, HEIGHT - 60), footer, font=_font(20), fill=MUTED)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, format="PNG")
    return str(out)
