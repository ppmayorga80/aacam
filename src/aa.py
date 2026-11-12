"""Ascii Art Utilities (AA) 
Python module for converting images to ASCII art and vice versa.
This module provides functions to convert images to ASCII art and to convert ASCII art back to string representation
"""
import cv2
import numpy as np
import curses

FONT_WIDTH = 9
FONT_HEIGHT = 16

CHARACTER_DENSITY = " _.,-=+:;cba!?0123456789$W#@N"
CHARACTER_DENSITY_INVERT = CHARACTER_DENSITY[::-1]
NUM_CHARS = len(CHARACTER_DENSITY)

CHARACTER_LUT = np.frombuffer(CHARACTER_DENSITY.encode("ascii"), dtype=np.uint8)
CHARACTER_LUT_INVERT = np.frombuffer(CHARACTER_DENSITY_INVERT.encode("ascii"), dtype=np.uint8)

def image2aa(image:np.ndarray, scale:float=1.0, invert:bool=False)->np.ndarray:
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

    