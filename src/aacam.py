"""Ascii Art Camera (AACAM) is a Python application that captures 
video from a webcam or video file and converts it into ASCII art 
in real-time. 
It uses OpenCV for video capture, Pillow for image processing, and 
pyvirtualcam to create a virtual camera output.

Usage:
    aacam.py [--source=<source>] [--scale=<scale>] [--invert] [--output=<output>]

Options:
    -s,--source=<source>      Video source [default: 0] integer for webcam id, or path to video file
    -k,--scale=<scale>        Scale factor for the ASCII art [default: 1.0]
    -i,--invert               Invert the ASCII characters
    -o,--output=<output>      Output file path for saving the ASCII art or a number to redirect video output [default: 1]

    
"""
from importlib.resources import path

import cv2
import numpy as np
import curses
import time
from docopt import docopt
from functools import partial

from aa import image2aa, aa2lines



def main(stdscr, path:int|str, scale:float=1.0, invert:bool=False, output:int|str=1):    
    curses.curs_set(0)
    stdscr.nodelay(True)
    h, w = stdscr.getmaxyx()

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1.0 / fps if fps > 0 else 1.0 / 30.0
    apply_sleep = True if isinstance(path, int) else False  # Only apply sleep for webcam input

    while True:
        start = time.perf_counter() if not apply_sleep else 0  # Start timing only if we are applying sleep

        key = stdscr.getch()
        if key in (27, ord('q'), ord('Q')):          # ESC or q,Q
            break
        elif key in (ord('z'),ord('Z')):  # z,Z
            stdscr.clear()
        elif key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            stdscr.clear()

        
        ret, frame = cap.read()
        if not ret:
            break
        aa_frame = image2aa(frame, scale=scale, invert=invert)
        aa_lines = aa2lines(aa_frame)

        for y, line in enumerate(aa_lines[:h]):
            stdscr.addstr(y, 0, line[:w-1])
        stdscr.refresh()

        if apply_sleep:
            elapsed = time.perf_counter() - start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    cap.release()
    
if __name__ == "__main__":
    args = docopt(__doc__)
    input_path = args['--source']
    invert_flag = args['--invert']
    output_path = args['--output']
    scale = float(args['--scale']) if args['--scale'] else 1.0

    try:
        input_path = int(input_path)
    except ValueError:
        pass  # Keep input_path as a string if it cannot be converted to int
    try:
        output_path = int(output_path)
    except ValueError:
        pass  # Keep output_path as a string if it cannot be converted to int

    print(f"Input source: {input_path}:{type(input_path)}, Scale: {scale}:{type(scale)}, Invert: {invert_flag}:{type(invert_flag)}, Output: {output_path}:{type(output_path)}")

    curses.wrapper(partial(main, path=input_path, scale=scale, invert=invert_flag, output=output_path))