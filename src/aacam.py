"""Ascii Art Camera (AACAM) is a Python application that captures 
video from a webcam or video file and converts it into ASCII art 
in real-time. 
It uses OpenCV for video capture, Pillow for image processing, and 
pyvirtualcam to create a virtual camera output.

Usage:
    aacam.py [--input=<input>] [--scale=<scale>] [--reverse] [--output=<output>] [--font-shape=<shape>] [--font=<font>] [--chars=<chars>]

Options:
    -i,--input=<input>        Video input source [default: 0] integer for webcam id, or path to video file
    -s,--scale=<scale>        Scale factor for the ASCII art [default: 1.0]
    -r,--reverse              Compute the reverse intensity of the ASCII characters
    -o,--output=<output>      Output of the ascii art: terminal or vcam [default: terminal]
    --font-shape=<shape>      The font shape for saving the ASCII art [default: 16,8]
    -f,--font=<font>          The font path [default: ]
    -c,--chars=<chars>        Char density string for the ASCII art [default: " _.,-=+:;cba!?0123456789$W#@N"]
                              values can be your own text except for the following keys:
                              "min": " .:*#",
                              "med": " .,:ilwW",
                              "avg": " .:-=+*#%@",
                              "max": " _.,-=+:;cba!?0123456789$W#@N",
                              "sym": " .-:;=+*#%&$@",
                              "alt": " .,-~:;+=xX$&#@",
                              "num": " .:-=+1234567890#@",
                              "ext": " .,-~:;=!+*?%S#&@$",
                              "full": " .,-~:;=!i><+rLv?1)(|/tjfnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",

"""
import cv2
import curses
import time
import pyvirtualcam

from docopt import docopt, DocoptExit
from functools import partial
from dotenv import load_dotenv

load_dotenv()

from aa import image2aa, aa2lines, aa2image, load_mono_font, image_shape_to_aa_shape, EnvVars, is_image_file
from audio_player import AudioPlayer


def main_curses(stdscr, path: int | str, scale: float = 1.0, reverse: bool = False):
    curses.curs_set(0)
    curses.set_escdelay(25)
    stdscr.nodelay(True)

    is_image = is_image_file(path)
    if is_image:
        static_frame = cv2.imread(path)
        if static_frame is None:
            raise ValueError(f"Could not open image: {path}")
        image_rows, image_cols = static_frame.shape[:2]
        fps = 30.0
        cap = None
    else:
        static_frame = None
        cap = cv2.VideoCapture(path)
        image_rows, image_cols = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = cap.get(cv2.CAP_PROP_FPS)

    is_video = isinstance(path, str) and not is_image
    audio_player = AudioPlayer(path) if is_video else None
    fallback_start = time.perf_counter()
    audio_active = False

    try:
        cli_rows, cli_cols = stdscr.getmaxyx()
        aa_rows, aa_cols = image_shape_to_aa_shape(shape=(image_rows, image_cols), scale=scale)
        frame_idx = 0
        dx, dy = 0, 0

        while True:
            if audio_player is not None:
                audio_player.tick()

            key = stdscr.getch()
            if key == curses.KEY_LEFT:
                dx = max(dx - 1, -aa_cols)
                stdscr.erase()
            elif key in (ord('A'), ord('a')):
                dx = max(dx - 10, -aa_cols)
                stdscr.erase()
            elif key == curses.KEY_RIGHT:
                dx = min(dx + 1, cli_cols)
                stdscr.erase()
            elif key in (ord('D'), ord('d')):
                dx = min(dx + 10, cli_cols)
                stdscr.erase()
            elif key == curses.KEY_UP:
                dy = max(dy - 1, -aa_rows)
                stdscr.erase()
            elif key in (ord('W'), ord('w')):
                dy = max(dy - 10, -aa_rows)
                stdscr.erase()
            elif key == curses.KEY_DOWN:
                dy = min(dy + 1, cli_rows)
                stdscr.erase()
            elif key in (ord('S'), ord('s')):
                dy = min(dy + 10, cli_rows)
                stdscr.erase()
            elif key == ord('+'):
                scale = min(scale + 0.1, 5.0)
                aa_rows, aa_cols = image_shape_to_aa_shape(shape=(image_rows, image_cols), scale=scale)
                stdscr.erase()
            elif key == ord('-'):
                scale = max(scale - 0.1, 0.1)
                aa_rows, aa_cols = image_shape_to_aa_shape(shape=(image_rows, image_cols), scale=scale)
                stdscr.erase()
            elif key in (27, ord('q'), ord('Q')):  # ESC or q, Q
                break
            elif key == curses.KEY_RESIZE:
                cli_rows, cli_cols = stdscr.getmaxyx()
                stdscr.erase()

            r0 = min(aa_rows, max(0, -dy))
            rn = max(r0, min(aa_rows, cli_rows - dy))
            c0 = min(aa_cols, max(0, -dx))
            cn = max(c0, min(aa_cols, cli_cols - dx))
            x0, y0 = max(0, dx), max(0, dy)

            media_time = 0.0
            if is_video and fps > 0:
                pts = audio_player.get_time() if audio_player is not None else 0.0
                if pts > 0.0:
                    audio_active = True
                    media_time = pts
                elif not audio_active and audio_player is not None and audio_player.active and (
                        time.perf_counter() - fallback_start) < 0.5:
                    media_time = 0.0
                else:
                    if audio_active:
                        fallback_start = time.perf_counter() - (frame_idx / fps)
                        audio_active = False
                    media_time = time.perf_counter() - fallback_start

            if is_image:
                frame = static_frame
            else:
                if is_video and fps > 0:
                    expected_frame = int(media_time * fps)
                    while frame_idx < expected_frame:
                        if not cap.grab():
                            break
                        frame_idx += 1

                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1

            aa_frame = image2aa(frame, scale=scale, reverse=reverse)

            if c0 < cn and r0 < rn:
                visible_lines = aa2lines(aa_frame[r0:rn, c0:cn])
                for y, line in enumerate(visible_lines, start=y0):
                    if y == cli_rows - 1 and x0 + len(line) == cli_cols:
                        line = line[:-1]
                    stdscr.addstr(y, x0, line)

            stdscr.refresh()

            if is_image:
                time.sleep(1.0 / 30.0)
            elif is_video and fps > 0:
                sleep_time = (frame_idx / fps) - media_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

    finally:
        if audio_player is not None:
            audio_player.close()
        if isinstance(path, str) and cap is not None:
            cap.release()


def main_vcam(path: int | str, scale: float = 1.0, reverse: bool = False, font=None):
    is_image = is_image_file(path)
    if is_image:
        static_frame = cv2.imread(path)
        if static_frame is None:
            raise ValueError(f"Could not open image: {path}")
        height, width = static_frame.shape[:2]
        fps = 30
        cap = None
    else:
        static_frame = None
        cap = cv2.VideoCapture(path)
        fps = max(int(cap.get(cv2.CAP_PROP_FPS)), 20)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_time = 1.0 / fps if fps > 0 else 1.0 / 30.0
    apply_sleep = isinstance(path, str)

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps) as cam:
            while True:
                start = time.perf_counter() if apply_sleep else 0

                if is_image:
                    frame = static_frame
                else:
                    ret, frame = cap.read()
                    if not ret:
                        break

                aa_frame = image2aa(frame, scale=scale, reverse=reverse, blur_size=3)
                aa_image = aa2image(aa_frame, font=font)
                aa_image = cv2.resize(aa_image, dsize=(width, height), interpolation=cv2.INTER_LINEAR)

                cam.send(aa_image)
                cam.sleep_until_next_frame()

                if apply_sleep:
                    elapsed = time.perf_counter() - start
                    sleep_time = frame_time - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Stopping aacam.py...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cap is not None:
            cap.release()
        print("Done.")


if __name__ == "__main__":
    args = docopt(__doc__)
    input_path = args['--input']
    reverse_flag = args['--reverse']
    output = str(args['--output']).lower()
    scale_factor = float(args['--scale']) if args['--scale'] else 1.0
    font_shape = tuple(int(s) for s in str(args['--font-shape']).split(","))

    font_path = args['--font']
    font = load_mono_font(size=16, font_path=font_path)

    EnvVars.set_chars(args['--chars'])
    EnvVars.set_font_shape(font_shape[0], font_shape[1])

    try:
        input_path = int(input_path)
    except ValueError:
        pass  # Keep input_path as a string if it cannot be converted to int

    if output.lower().startswith("t"):
        curses.wrapper(partial(main_curses, path=input_path, scale=scale_factor, reverse=reverse_flag))
    elif output.lower().startswith(("v", "0")):
        main_vcam(path=input_path, scale=scale_factor, reverse=reverse_flag, font=font)
