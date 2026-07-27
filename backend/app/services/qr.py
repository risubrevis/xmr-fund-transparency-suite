"""QR code generation for deposit addresses.

Produces QR codes as base64 PNG data URLs (for inline embedding in widget
JSON / HTML) and as resampled PNG bytes (for downloadable image files).
"""

import base64
import io
from typing import cast

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.pil import PilImage

# Allowed pixel sizes for downloadable QR code PNGs.
QR_PNG_SIZES = (48, 96, 128, 256, 512)


def generate_qr_data_url(data: str, size: int = 200) -> str:
    """Generate a QR code as a base64 PNG data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    # make_image() is typed as BaseImage (save has no `format` kwarg), but the
    # default factory returns a PilImage whose save() accepts format=.
    img = cast(PilImage, qr.make_image(fill_color="#000000", back_color="#ffffff"))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_qr_png(data: str, size: int = 256) -> bytes:
    """Generate a QR code PNG resized to the requested square pixel size.

    The QR is rendered at a high box_size for crispness, then the underlying
    PIL image is resampled to exactly ``size`` x ``size`` pixels.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = cast(PilImage, qr.make_image(fill_color="#000000", back_color="#ffffff"))
    pil_img = img.get_image().resize((size, size))
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()