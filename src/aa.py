"""Ascii Art Utilities (AA) 
Python module for converting images to ASCII art and vice versa.
This module provides functions to convert images to ASCII art and to convert ASCII art back to string representation
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_WIDTH = 8
FONT_HEIGHT = 16

CHARACTER_DENSITY = " _.,-=+:;cba!?0123456789$W#@N"
CHARACTER_DENSITY_INVERT = CHARACTER_DENSITY[::-1]
NUM_CHARS = len(CHARACTER_DENSITY)

CHARACTER_LUT = np.frombuffer(CHARACTER_DENSITY.encode("ascii"), dtype=np.uint8)
CHARACTER_LUT_INVERT = np.frombuffer(CHARACTER_DENSITY_INVERT.encode("ascii"), dtype=np.uint8)

def image2aa(image:np.ndarray, scale:float=1.0, invert:bool=False, blur_size:int=0)->np.ndarray:
    """
    Convert an image to ASCII art.

    Args:
        image (np.ndarray): The input image.
        invert (bool): Whether to invert the ASCII characters.

    Returns:
        str: The ASCII art representation of the image.
    """
    height, width = image.shape[0:2]

    # Resize the image
    new_width = int(width * scale/FONT_WIDTH)
    new_height = int(height * scale/FONT_HEIGHT)
    gray = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    if blur_size>0:
        gray = cv2.GaussianBlur(gray, ksize=(blur_size,blur_size), sigmaX=0)
    
    idx = (gray.astype(np.uint16) * NUM_CHARS) // 256
    lut = CHARACTER_LUT_INVERT if invert else CHARACTER_LUT
    return lut[idx]


def aa2lines(aa_matrix:np.ndarray)->list[str]:
    """
    Convert an ASCII art matrix to a list of strings.

    Args:
        aa_matrix (np.ndarray): The ASCII art matrix.

    Returns:
        list[str]: The ASCII art as a list of strings.
    """
    return [row.tobytes() for row in aa_matrix]

def load_mono_font(size: int = 10, font_path:str="") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a cross-platform 10pt monospaced font (cached once outside the loop)."""
    # Note: Pillow sizes are in pixels; for strict 10pt at 96 DPI, use size=13.
    candidates = [
        font_path,
        "consola.ttf",                  # Windows (Consolas)
        "cour.ttf",                     # Windows (Courier New)
        "DejaVuSansMono.ttf",           # Linux
        "LiberationMono-Regular.ttf",   # Linux
        "/System/Library/Fonts/Menlo.ttc",  # macOS
    ]
    for font_path in candidates:
        try:
            f = ImageFont.truetype(font_path, size=size)
            return f
        except OSError:
            continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

# Initialize once globally so it isn't reloaded every frame
MONO_FONT_DEFAULT_SIZE = load_mono_font(size=16)

def aa2image(
    aa_matrix: np.ndarray,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont = MONO_FONT_DEFAULT_SIZE,
    as_bgr: bool = True,
) -> np.ndarray:
    """
    Render an ASCII matrix onto a black background with white monospaced characters.

    Args:
        aa_matrix (np.ndarray): 2D array of ASCII characters (uint8 or str).
        font: Preloaded Pillow monospaced font.
        as_bgr (bool): If True, returns an OpenCV BGR np.ndarray; otherwise a PIL.Image.
    """
    rows, cols = aa_matrix.shape

    # Measure exact cell size so every frame keeps a fixed resolution
    char_w = max(1, int(round(font.getlength("M"))))
    try:
        ascent, descent = font.getmetrics()
        char_h = max(1, ascent + descent)
    except AttributeError:
        bbox = font.getbbox("M")
        char_h = max(1, bbox[3] - bbox[1])

    img_w = cols * char_w
    img_h = rows * char_h

    # Convert matrix to a single newline-delimited string
    if aa_matrix.dtype == np.uint8:
        text = b"\n".join(row.tobytes() for row in aa_matrix).decode("ascii")
    else:
        text = "\n".join("".join(row) for row in aa_matrix)

    # Render in 8-bit grayscale (0 = black bg, 255 = white text)
    canvas = Image.new("L", (img_w, img_h), color=0)
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text((0, 0), text, fill=255, font=font, spacing=0)

    # if not as_bgr:
    #     return canvas.convert("RGB")

    gray_arr = np.asarray(canvas)
    return cv2.cvtColor(gray_arr, cv2.COLOR_GRAY2BGR)

