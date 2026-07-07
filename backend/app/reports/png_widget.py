"""Generate widget PNG images in multiple formats (business card, wide, vertical)."""

import io
from typing import Literal

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Standard business card dimensions (ISO/IEC 7810 ID-1, same as credit card)
DPI = 300

FORMATS = {
    "business_card": {"width_mm": 85.6, "height_mm": 53.98, "label": "Business Card"},
    "wide": {"width_mm": 190, "height_mm": 65, "label": "Wide"},
    "vertical": {"width_mm": 80, "height_mm": 130, "label": "Vertical"},
}

# Font paths — DejaVu Sans available in Docker container
FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def mm_to_px(mm: float) -> int:
    """Convert millimeters to pixels at 300 DPI."""
    return int(mm * DPI / 25.4)


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font with fallback to default."""
    try:
        return ImageFont.truetype(f"{FONT_DIR}/{name}", size)
    except OSError:
        return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color (#RRGGBB) to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color to HSL (h: 0-360, s: 0-100, l: 0-100)."""
    r, g, b = hex_to_rgb(hex_color)
    r /= 255
    g /= 255
    b /= 255
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    lightness = (max_c + min_c) / 2
    if max_c == min_c:
        h = 0.0
        s = 0.0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if lightness > 0.5 else d / (max_c + min_c)
        if max_c == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6
        elif max_c == g:
            h = ((b - r) / d + 2) / 6
        else:
            h = ((r - g) / d + 4) / 6
    return (h * 360, s * 100, lightness * 100)


def hsl_to_rgb(h: float, s: float, lightness: float) -> tuple[int, int, int]:
    """Convert HSL to RGB tuple."""
    h = ((h % 360) + 360) % 360
    s /= 100
    lightness /= 100
    c = (1 - abs(2 * lightness - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = lightness - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255),
    )


def generate_gradient(
    width: int,
    height: int,
    start_hex: str,
    end_hex: str,
) -> Image.Image:
    """Generate a 135-degree diagonal gradient image."""
    start_rgb = hex_to_rgb(start_hex)
    end_rgb = hex_to_rgb(end_hex)

    img = Image.new("RGB", (width, height))
    pixels = img.load()

    # Diagonal gradient: interpolation based on position along the diagonal
    max_dist = width + height
    for y in range(height):
        for x in range(width):
            t = (x + (height - 1 - y)) / max_dist if max_dist > 0 else 0
            t = max(0.0, min(1.0, t))
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
            pixels[x, y] = (r, g, b)

    return img


def _draw_text_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    line_spacing: int = 4,
) -> int:
    """Draw text with word wrapping. Returns the Y position after the last line."""
    if not text:
        return y

    words = text.split()
    lines: list[str] = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width or not current_line:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

    return y


def _generate_qr_image(address: str, size: int) -> Image.Image:
    """Generate a QR code image for a Monero address."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(f"monero:{address}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    img = img.convert("RGBA")
    # Resize to exact target size
    return img.resize((size, size), Image.Resampling.LANCZOS)


def generate_widget_png(
    label: str,
    description: str | None,
    public_website: str | None,
    deposit_address: str,
    target_amount_xmr: str | None,
    total_received_xmr: str,
    base_color: str,
    text_color: str,
    format_type: Literal["business_card", "wide", "vertical"],
) -> bytes:
    """Generate a widget PNG image in the specified format.

    Returns PNG image bytes.
    """
    fmt = FORMATS.get(format_type)
    if not fmt:
        raise ValueError(f"Unknown format: {format_type}")

    width = mm_to_px(fmt["width_mm"])
    height = mm_to_px(fmt["height_mm"])

    # Gradient colors (same logic as JS widget: +40 hue shift)
    h, s, lightness = hex_to_hsl(base_color)
    end_color_hex = "#{:02x}{:02x}{:02x}".format(*hsl_to_rgb(h + 40, s, lightness))
    text_rgb = hex_to_rgb(text_color)

    # Padding
    pad = mm_to_px(4)

    # Create gradient background
    img = generate_gradient(width, height, base_color, end_color_hex)
    draw = ImageDraw.Draw(img)

    # Enable alpha blending for overlay elements
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Fonts
    if format_type == "business_card":
        font_label = _load_font("DejaVuSans-Bold.ttf", 28)
        font_website = _load_font("DejaVuSans.ttf", 16)
        font_desc = _load_font("DejaVuSans.ttf", 16)
        font_amount = _load_font("DejaVuSans-Bold.ttf", 20)
        font_addr = _load_font("DejaVuSansMono.ttf", 13)
        font_powered = _load_font("DejaVuSans.ttf", 11)
        qr_size = mm_to_px(30)
    elif format_type == "wide":
        font_label = _load_font("DejaVuSans-Bold.ttf", 32)
        font_website = _load_font("DejaVuSans.ttf", 18)
        font_desc = _load_font("DejaVuSans.ttf", 18)
        font_amount = _load_font("DejaVuSans-Bold.ttf", 24)
        font_addr = _load_font("DejaVuSansMono.ttf", 15)
        font_powered = _load_font("DejaVuSans.ttf", 13)
        qr_size = mm_to_px(40)
    else:  # vertical
        font_label = _load_font("DejaVuSans-Bold.ttf", 30)
        font_website = _load_font("DejaVuSans.ttf", 17)
        font_desc = _load_font("DejaVuSans.ttf", 17)
        font_amount = _load_font("DejaVuSans-Bold.ttf", 22)
        font_addr = _load_font("DejaVuSansMono.ttf", 14)
        font_powered = _load_font("DejaVuSans.ttf", 12)
        qr_size = mm_to_px(42)

    if format_type in ("business_card", "wide"):
        _draw_horizontal_layout(
            img=img,
            draw=draw,
            overlay_draw=overlay_draw,
            overlay=overlay,
            width=width,
            height=height,
            pad=pad,
            label=label,
            description=description,
            public_website=public_website,
            deposit_address=deposit_address,
            target_amount_xmr=target_amount_xmr,
            total_received_xmr=total_received_xmr,
            text_rgb=text_rgb,
            font_label=font_label,
            font_website=font_website,
            font_desc=font_desc,
            font_amount=font_amount,
            font_addr=font_addr,
            font_powered=font_powered,
            qr_size=qr_size,
        )
    else:  # vertical
        _draw_vertical_layout(
            img=img,
            draw=draw,
            overlay_draw=overlay_draw,
            overlay=overlay,
            width=width,
            height=height,
            pad=pad,
            label=label,
            description=description,
            public_website=public_website,
            deposit_address=deposit_address,
            target_amount_xmr=target_amount_xmr,
            total_received_xmr=total_received_xmr,
            text_rgb=text_rgb,
            font_label=font_label,
            font_website=font_website,
            font_desc=font_desc,
            font_amount=font_amount,
            font_addr=font_addr,
            font_powered=font_powered,
            qr_size=qr_size,
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(DPI, DPI))
    return buf.getvalue()


def _draw_horizontal_layout(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    overlay_draw: ImageDraw.ImageDraw,
    overlay: Image.Image,
    width: int,
    height: int,
    pad: int,
    label: str,
    description: str | None,
    public_website: str | None,
    deposit_address: str,
    target_amount_xmr: str | None,
    total_received_xmr: str,
    text_rgb: tuple[int, int, int],
    font_label: ImageFont.FreeTypeFont,
    font_website: ImageFont.FreeTypeFont,
    font_desc: ImageFont.FreeTypeFont,
    font_amount: ImageFont.FreeTypeFont,
    font_addr: ImageFont.FreeTypeFont,
    font_powered: ImageFont.FreeTypeFont,
    qr_size: int,
) -> None:
    """Draw business card and wide (horizontal) layouts."""
    content_width = width - 2 * pad
    left_width = content_width - qr_size - mm_to_px(4)
    y = pad

    # === Left side: label, website, description, amounts ===
    draw.text((pad, y), label, font=font_label, fill=text_rgb)
    bbox = font_label.getbbox(label)
    y += bbox[3] - bbox[1] + mm_to_px(1)

    if public_website:
        draw.text((pad, y), public_website, font=font_website, fill=(*text_rgb[:3],))
        # Slightly dimmer
        dimmed = tuple(max(0, int(c * 0.7 + 255 * 0.3)) for c in text_rgb)
        draw.text((pad, y), public_website, font=font_website, fill=dimmed)
        bbox = font_website.getbbox(public_website)
        y += bbox[3] - bbox[1] + mm_to_px(1.5)

    if description:
        y = _draw_text_wrapped(
            draw, description, pad, y, left_width - mm_to_px(1), font_desc, text_rgb
        )
        y += mm_to_px(1)

    # Received amount
    received_text = f"{total_received_xmr} XMR"
    draw.text((pad, y), received_text, font=font_amount, fill=text_rgb)
    bbox = font_amount.getbbox(received_text)
    y += bbox[3] - bbox[1] + mm_to_px(1)

    if target_amount_xmr:
        target_text = f"Target: {target_amount_xmr} XMR"
        draw.text((pad, y), target_text, font=font_desc, fill=text_rgb)
        y += font_desc.getbbox(target_text)[3] - font_desc.getbbox(target_text)[1]

    # === Right side: QR code ===
    qr_img = _generate_qr_image(deposit_address, qr_size)
    qr_x = width - pad - qr_size
    qr_y = pad
    img.paste(qr_img, (qr_x, qr_y), qr_img.convert("RGBA"))

    # === Deposit address bar ===
    addr_bar_y = max(qr_y + qr_size, y + mm_to_px(2))
    addr_bar_y = max(addr_bar_y, height - pad - mm_to_px(10))

    # Thin white border line above address
    border_y = addr_bar_y - mm_to_px(1)
    draw.line(
        [(pad, border_y), (width - pad, border_y)], fill=(255, 255, 255, 128), width=1
    )

    # Deposit address — monospaced, full width
    draw.text((pad, addr_bar_y), deposit_address, font=font_addr, fill=text_rgb)

    # === Powered by ===
    powered_y = height - pad - mm_to_px(1)
    dimmed = tuple(max(0, int(c * 0.6)) for c in text_rgb)
    draw.text((pad, powered_y), "Powered by xmrfts.com", font=font_powered, fill=dimmed)


def _draw_vertical_layout(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    overlay_draw: ImageDraw.ImageDraw,
    overlay: Image.Image,
    width: int,
    height: int,
    pad: int,
    label: str,
    description: str | None,
    public_website: str | None,
    deposit_address: str,
    target_amount_xmr: str | None,
    total_received_xmr: str,
    text_rgb: tuple[int, int, int],
    font_label: ImageFont.FreeTypeFont,
    font_website: ImageFont.FreeTypeFont,
    font_desc: ImageFont.FreeTypeFont,
    font_amount: ImageFont.FreeTypeFont,
    font_addr: ImageFont.FreeTypeFont,
    font_powered: ImageFont.FreeTypeFont,
    qr_size: int,
) -> None:
    """Draw vertical layout: description at top, QR center, address below."""
    content_width = width - 2 * pad
    y = pad

    # === Top: label, website, description, amounts ===
    draw.text((pad, y), label, font=font_label, fill=text_rgb)
    bbox = font_label.getbbox(label)
    y += bbox[3] - bbox[1] + mm_to_px(1)

    if public_website:
        dimmed = tuple(max(0, int(c * 0.7 + 255 * 0.3)) for c in text_rgb)
        draw.text((pad, y), public_website, font=font_website, fill=dimmed)
        bbox = font_website.getbbox(public_website)
        y += bbox[3] - bbox[1] + mm_to_px(1.5)

    if description:
        y = _draw_text_wrapped(
            draw, description, pad, y, content_width, font_desc, text_rgb
        )
        y += mm_to_px(1)

    # Received amount
    received_text = f"{total_received_xmr} XMR"
    draw.text((pad, y), received_text, font=font_amount, fill=text_rgb)
    bbox = font_amount.getbbox(received_text)
    y += bbox[3] - bbox[1] + mm_to_px(1)

    if target_amount_xmr:
        target_text = f"Target: {target_amount_xmr} XMR"
        draw.text((pad, y), target_text, font=font_desc, fill=text_rgb)
        y += font_desc.getbbox(target_text)[3] - font_desc.getbbox(target_text)[1]

    y += mm_to_px(3)

    # === Center: QR code ===
    qr_img = _generate_qr_image(deposit_address, qr_size)
    qr_x = (width - qr_size) // 2
    img.paste(qr_img, (qr_x, y), qr_img.convert("RGBA"))
    y += qr_size + mm_to_px(3)

    # === Deposit address — wrapped if needed ===
    addr_lines = _wrap_text(deposit_address, content_width, font_addr)
    for line in addr_lines:
        line_bbox = font_addr.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, y), line, font=font_addr, fill=text_rgb)
        y += line_bbox[3] - line_bbox[1] + mm_to_px(1)

    # === Powered by — bottom left ===
    dimmed = tuple(max(0, int(c * 0.6)) for c in text_rgb)
    draw.text(
        (pad, height - pad - mm_to_px(1)),
        "Powered by xmrfts.com",
        font=font_powered,
        fill=dimmed,
    )


def _wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """Wrap text to fit within max_width, breaking at character boundaries for addresses."""
    if not text:
        return []

    # For addresses, try to break at reasonable points
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]

    if text_width <= max_width:
        return [text]

    # Character-by-character wrapping for monospace addresses
    lines: list[str] = []
    current_line = ""
    for char in text:
        test = current_line + char
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test

    if current_line:
        lines.append(current_line)

    return lines


def get_format_dimensions(format_type: str) -> str:
    """Return human-readable dimensions for a format."""
    fmt = FORMATS.get(format_type)
    if not fmt:
        return ""
    return f"{fmt['width_mm']:.1f} × {fmt['height_mm']:.1f} mm"
