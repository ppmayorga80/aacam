"""Ascii Art Utilities (AA) 
Python module for converting images to ASCII art and vice versa.
This module provides functions to convert images to ASCII art and to convert ASCII art back to string representation
"""
import os
import cv2
import numpy as np

from PIL import Image, ImageDraw, ImageFont


class EnvVars:
    FONT_WIDTH = int(os.environ.get('FONT_WIDTH', '8'))
    FONT_HEIGHT = int(os.environ.get('FONT_HEIGHT', '16'))
    CHARACTER_DENSITY = os.environ.get('CHARACTER_DENSITY', ' .-=o$#*')
    # lut info
    CHARACTER_DENSITY_INVERT = CHARACTER_DENSITY[::-1]
    NUM_CHARS = len(CHARACTER_DENSITY)
    CHARACTER_LUT = np.frombuffer(CHARACTER_DENSITY.encode("ascii"), dtype=np.uint8)
    CHARACTER_LUT_INVERT = np.frombuffer(CHARACTER_DENSITY_INVERT.encode("ascii"), dtype=np.uint8)

    @classmethod
    def update_lut(cls):
        cls.CHARACTER_DENSITY_INVERT = cls.CHARACTER_DENSITY[::-1]
        cls.NUM_CHARS = len(cls.CHARACTER_DENSITY)

        cls.CHARACTER_LUT = np.frombuffer(cls.CHARACTER_DENSITY.encode("ascii"), dtype=np.uint8)
        cls.CHARACTER_LUT_INVERT = np.frombuffer(cls.CHARACTER_DENSITY_INVERT.encode("ascii"), dtype=np.uint8)

    @classmethod
    def set_font_shape(cls, h: int, w: int):
        cls.FONT_WIDTH = w
        cls.FONT_HEIGHT = h

    @classmethod
    def set_chars(cls, value: str):
        dict_values = {
            "min": " .:*#",
            "med": " .,:ilwW",
            "avg": " .:-=+*#%@",
            "max": " _.,-=+:;cba!?0123456789$W#@N",
            # ----------------------------------
            "sym": " .-:;=+*#%&$@",
            "alt": " .,-~:;+=xX$&#@",
            "num": " .:-=+1234567890#@",
            "ext": " .,-~:;=!+*?%S#&@$",
            "full": " .,-~:;=!i><+rLv?1)(|/tjfnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
        }
        if value in dict_values:
            cls.CHARACTER_DENSITY = dict_values[value]
        else:
            cls.CHARACTER_DENSITY = value
        cls.update_lut()


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif")


def is_image_file(path: int | str) -> bool:
    return isinstance(path, str) and path.lower().endswith(IMAGE_EXTENSIONS)


def image_shape_to_aa_shape(shape: tuple[int, int], scale: float = 1.0) -> tuple[int, int]:
    height, width = shape[0:2]

    # Resize the image
    new_height = int(height * scale / EnvVars.FONT_HEIGHT)
    new_width = int(width * scale / EnvVars.FONT_WIDTH)
    return new_height, new_width


def image2aa(image: np.ndarray, scale: float = 1.0, reverse: bool = False, blur_size: int = 0) -> np.ndarray:
    """Converts an image to ASCII art.

    Args:
        image (np.ndarray): The input image array.
        scale (float, optional): Scaling factor applied to resize the image.
            Defaults to 1.0.
        reverse (bool, optional): Whether to invert the brightness-to-character
            mapping. Defaults to False.
        blur_size (int, optional): Kernel size used to blur the image before
            conversion. Set to 0 to disable blurring. Defaults to 0.

    Returns:
        np.ndarray: The ASCII art representation rendered as an image array.
    """
    # Resize the image
    new_height, new_width = image_shape_to_aa_shape(image.shape, scale)
    gray = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    if blur_size > 0:
        gray = cv2.GaussianBlur(gray, ksize=(blur_size, blur_size), sigmaX=0)

    idx = (gray.astype(np.uint16) * EnvVars.NUM_CHARS) // 256
    lut = EnvVars.CHARACTER_LUT_INVERT if reverse else EnvVars.CHARACTER_LUT
    return lut[idx]


def aa2lines(aa_matrix: np.ndarray) -> list[str]:
    """Converts an ASCII art matrix to a list of strings.

    Args:
        aa_matrix (np.ndarray): A 2D array of characters representing the
            ASCII art.

    Returns:
        list[str]: A list where each string represents a row of the ASCII art
            matrix.
    """
    return [row.tobytes() for row in aa_matrix]


def load_mono_font(size: int = 10, font_path: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Loads a cross-platform monospaced font, falling back to PIL's default font.

    Args:
        size (int, optional): The font size in points. Defaults to 10.
        font_path (str, optional): Path to a custom font file. If empty, searches
            common system monospaced font paths. Defaults to "".

    Returns:
        ImageFont.FreeTypeFont | ImageFont.ImageFont: The loaded monospaced font
            object, or Pillow's default bitmap font if no TrueType font is found.
    """
    # Note: Pillow sizes are in pixels; for strict 10pt at 96 DPI, use size=13.
    candidates = [
        font_path,
        "consola.ttf",  # Windows (Consolas)
        "cour.ttf",  # Windows (Courier New)
        "DejaVuSansMono.ttf",  # Linux
        "LiberationMono-Regular.ttf",  # Linux
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
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont = MONO_FONT_DEFAULT_SIZE
) -> np.ndarray:
    """Renders an ASCII matrix onto a black background with white monospaced characters.

    Args:
        aa_matrix (np.ndarray): A 2D array of ASCII characters (`uint8` or `str`).
        font (ImageFont.FreeTypeFont | ImageFont.ImageFont, optional): Preloaded
            Pillow monospaced font. Defaults to `MONO_FONT_DEFAULT_SIZE`.

    Returns:
        np.ndarray | Image.Image: The rendered ASCII art as a BGR NumPy array
    """
    rows, cols = aa_matrix.shape

    # Measure exact cell size so every frame keeps a fixed resolution
    char_w = max(1, int(round(font.getlength("M"))))
    try:
        ascent, descent = font.getmetrics()
        char_h = max(1, ascent + descent)
    except AttributeError:
        bbox = font.getbbox("M")
        char_h = max(1, int(bbox[3] - bbox[1]))

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

    gray_arr = np.asarray(canvas)
    return cv2.cvtColor(gray_arr, cv2.COLOR_GRAY2BGR)
