import cv2
import numpy as np
from aa import aa2image, image2aa, load_mono_font


img = cv2.imread("/Users/pedro/Downloads/cat-01.png")
if img is None:
	raise FileNotFoundError("Could not load image: /Users/pedro/Downloads/cat-01.png")

font = load_mono_font(size=16, font_path="/Users/pedro/Library/Fonts/MesloLGS NF Regular")
aa = image2aa(img, reverse=True)
aa_img = aa2image(aa,font=font)

cv2.imshow("CAT",img)
cv2.imshow("ASCII",aa_img)
cv2.waitKey(0)