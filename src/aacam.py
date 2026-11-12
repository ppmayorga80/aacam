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
    -o,--output=<output>      Output file path for saving the ASCII art or a number to redirect video output [default: -1]

    
"""
from importlib.resources import path

import cv2
import numpy as np
import curses
import time
import pyvirtualcam

from docopt import docopt
from functools import partial

from aa import image2aa, aa2lines, aa2image, load_mono_font

def main_curses(stdscr, path:int|str, scale:float=1.0, invert:bool=False):
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

def main_cam(path:int|str, scale:float=1.0, invert:bool=False):
    cap = cv2.VideoCapture(path)
    fps = max(int(cap.get(cv2.CAP_PROP_FPS)),20)
    frame_time = 1.0 / fps if fps > 0 else 1.0 / 30.0
    apply_sleep = True if isinstance(path, int) else False  # Only apply sleep for webcam input

    width,height=1280,720
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps) as cam:
            while True:
                start = time.perf_counter() if not apply_sleep else 0  

                ret, frame = cap.read()
                if not ret:
                    break
                # frame = cv2.resize(frame,dsize=(width,height),interpolation=cv2.INTER_NEAREST)
                aa_frame = image2aa(frame, scale=scale, invert=invert, blur_size=3)
                aa_image = aa2image(aa_frame)
                aa_image = cv2.resize(aa_image,dsize=(width,height),interpolation=cv2.INTER_LINEAR)


                cam.send(aa_image)
                cam.sleep_until_next_frame()

                if apply_sleep:
                    elapsed = time.perf_counter() - start
                    sleep_time = frame_time - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Stoping aacam.py...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cap.release()
        print("Done.")


if __name__ == "__main__":
    args = docopt(__doc__)
    input_path = args['--source']
    invert_flag = args['--invert']
    output_path = args['--output']
    scale_factor = float(args['--scale']) if args['--scale'] else 1.0

    try:
        input_path = int(input_path)
    except ValueError:
        pass  # Keep input_path as a string if it cannot be converted to int
    try:
        output_path = int(output_path)
    except ValueError:
        pass  # Keep output_path as a string if it cannot be converted to int

    if isinstance(output_path,int) and output_path==-1:
        curses.wrapper(partial(main_curses, path=input_path, scale=scale_factor, invert=invert_flag))
    else:
        main_cam(path=output_path,scale=scale_factor,invert=invert_flag)