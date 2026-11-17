import os
import cv2
import numpy as np
from aa import aa2lines, image2aa

def test_load_image():
    PATH="/home/pedro/lena.png"
    assert os.path.exists(PATH), f"Image file does not exist: '{PATH}'"
    img = cv2.imread(PATH)
    assert isinstance(img, (np.ndarray)), "Failed to load image as a numpy array"
    assert img.dtype == np.uint8, "Image array is not of type uint8"
    assert len(img.shape) == 3, "Image array is not a color image"
    
    aa = image2aa(img, reverse=False)
    assert isinstance(aa, np.ndarray), "ASCII art is not a numpy array"
    assert aa.dtype.type is np.str_, "ASCII art array is not of type str"
    
    text = aa2lines(aa)
    assert isinstance(text, list), "ASCII art string is not of type str"
    assert all(isinstance(line, str) for line in text), "Not all lines in ASCII art are strings"
    print(text)
