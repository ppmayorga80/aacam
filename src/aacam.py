"""Ascii Art Camera (AACAM) is a Python application that captures 
video from a webcam or video file and converts it into ASCII art 
in real-time. 
It uses OpenCV for video capture, Pillow for image processing, and 
pyvirtualcam to create a virtual camera output.

Usage:
    aacam.py [--input=<input>] [--scale=<scale>] [--reverse] [--output=<output>] [--font-shape=<shape>] [--chars=<chars>] [--write=<file>]

Options:
    -i,--input=<input>        Video input source [default: 0] integer for webcam id, or path to video file
    -s,--scale=<scale>        Scale factor for the ASCII art [default: 1.0]
    -r,--reverse              Compute the reverse intensity of the ASCII characters
    -o,--output=<output>      Output of the ascii art: terminal or vcam [default: terminal], 0 is equivalent to vcam
    -f,--font-shape=<shape>   Font shape (height,width) for ASCII scaling & vcam rendering [default: 16,8]
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
    -w,--write=<file>         writes content to <file> when press key 'w' or 'W' [default: .out]


Zoom and moves:
    +     zoom in
    -     zoom out
    LEFT  move left
    RIGHT move right
    UP    move up
    DOWN  move down
    IJKL  mapping to UP,LEFT,DOWN,RIGHT  

"""
import cv2
import curses
import numpy as np
import time
import pyvirtualcam

from docopt import docopt
from functools import partial
from dotenv import load_dotenv

load_dotenv()

from aa import image2aa,aa2lines,aa2image,load_mono_font,image_shape_to_aa_shape,EnvVars,is_image_file
from audio_player import AudioPlayer


def init_curses(stdscr) -> None:
    """Configure non-blocking curses mode with hidden cursor and minimal ESC delay."""
    curses.curs_set(0)
    if hasattr(curses, "set_escdelay"):
        curses.set_escdelay(25)
    stdscr.nodelay(True)


def open_media_source(
    path: int | str, min_fps: float = 0.0
) -> tuple[bool, bool, cv2.VideoCapture | None, np.ndarray | None, int, int, float]:
    """Open an image, video file, or webcam and return its metadata."""
    is_image = is_image_file(path)
    if is_image:
        static_frame = cv2.imread(path)
        if static_frame is None:
            raise ValueError(f"Could not open image: {path}")
        height, width = static_frame.shape[:2]
        return True, False, None, static_frame, height, width, 30.0

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video source: {path}")

    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if min_fps > 0:
        fps = max(float(int(fps)), min_fps)

    is_video = isinstance(path, str)
    return False, is_video, cap, None, height, width, fps


def handle_nav_key(
    key: int,
    dx: int,
    dy: int,
    factor: float,
    initial_factor: float,
    min_factor: float,
    max_factor: float,
    aa_rows: int,
    aa_cols: int,
    view_rows: int,
    view_cols: int,
) -> tuple[int, int, float, bool, bool]:
    """Handle pan, zoom/scale, reset, and quit keys. Returns (dx, dy, factor, changed, should_quit, should_write)."""
    changed = False
    should_quit = False
    should_write = False

    if key == curses.KEY_LEFT:
        dx = max(dx - 1, -aa_cols)
        changed = True
    elif key in (ord('J'), ord('j')):
        dx = max(dx - 10, -aa_cols)
        changed = True
    elif key == curses.KEY_RIGHT:
        dx = min(dx + 1, view_cols)
        changed = True
    elif key in (ord('L'), ord('l')):
        dx = min(dx + 10, view_cols)
        changed = True
    elif key == curses.KEY_UP:
        dy = max(dy - 1, -aa_rows)
        changed = True
    elif key in (ord('I'), ord('i')):
        dy = max(dy - 10, -aa_rows)
        changed = True
    elif key == curses.KEY_DOWN:
        dy = min(dy + 1, view_rows)
        changed = True
    elif key in (ord('K'), ord('k')):
        dy = min(dy + 10, view_rows)
        changed = True
    elif key in (ord('+'), ord('=')):
        factor = round(min(factor + 0.1, max_factor), 2)
        changed = True
    elif key == ord('-'):
        factor = round(max(factor - 0.1, min_factor), 2)
        changed = True
    elif key == ord('0'):
        dx, dy, factor = 0, 0, initial_factor
        changed = True
    elif key in (ord('W'), ord('w')):
        should_write = True
    elif key in (27, ord('q'), ord('Q')):  # ESC or q, Q
        should_quit = True

    return dx, dy, factor, changed, should_quit, should_write


def compute_viewport_slices(
    dx: int,
    dy: int,
    aa_rows: int,
    aa_cols: int,
    view_rows: int,
    view_cols: int,
) -> tuple[int, int, int, int, int, int]:
    """Compute source slice bounds (r0, rn, c0, cn) and destination offsets (x0, y0)."""
    r0 = min(aa_rows, max(0, -dy))
    rn = max(r0, min(aa_rows, view_rows - dy))
    c0 = min(aa_cols, max(0, -dx))
    cn = max(c0, min(aa_cols, view_cols - dx))
    x0, y0 = max(0, dx), max(0, dy)
    return r0, rn, c0, cn, x0, y0


def main_curses(stdscr, path: int | str, scale: float = 1.0, reverse: bool = False, write_path:str=".out"):
    init_curses(stdscr)
    is_image, is_video, cap, static_frame, image_rows, image_cols, fps = open_media_source(path)

    audio_player = AudioPlayer(path) if is_video else None
    fallback_start = time.perf_counter()
    audio_active = False
    initial_scale = scale

    try:
        cli_rows, cli_cols = stdscr.getmaxyx()
        aa_rows, aa_cols = image_shape_to_aa_shape(shape=(image_rows, image_cols), scale=scale)
        frame_idx = 0
        dx, dy = 0, 0
        should_write = False

        while True:
            if audio_player is not None:
                audio_player.tick()

            key = stdscr.getch()
            if key == curses.KEY_RESIZE:
                cli_rows, cli_cols = stdscr.getmaxyx()
                stdscr.erase()
            elif key != -1:
                dx, dy, new_scale, changed, should_quit, should_write = handle_nav_key(
                    key, dx, dy, scale, initial_scale, 0.1, 5.0, aa_rows, aa_cols, cli_rows, cli_cols
                )
                if should_quit:
                    break
                if changed:
                    next_rows, next_cols = image_shape_to_aa_shape(
                        shape=(image_rows, image_cols), scale=new_scale
                    )
                    if next_rows >= 1 and next_cols >= 1:
                        scale = new_scale
                        aa_rows, aa_cols = next_rows, next_cols
                    stdscr.erase()

            r0, rn, c0, cn, x0, y0 = compute_viewport_slices(dx, dy, aa_rows, aa_cols, cli_rows, cli_cols)

            media_time = 0.0
            if is_video and fps > 0:
                pts = audio_player.get_time() if audio_player is not None else 0.0
                if pts > 0.0:
                    audio_active = True
                    media_time = pts
                elif (
                    not audio_active
                    and audio_player is not None
                    and audio_player.active
                    and (time.perf_counter() - fallback_start) < 0.5
                ):
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
                if should_write:
                    with open(write_path,"wb") as fp:
                        fp.write(b"\n".join(visible_lines))

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
        if cap is not None:
            cap.release()


def draw_vcam_hud(
    stdscr,
    cam_device: str,
    width: int,
    height: int,
    fps: int,
    scale: float,
    zoom: float,
    font_size: int,
    dx: int,
    dy: int,
) -> None:
    stdscr.erase()
    lines = [
        f"AACAM Virtual Camera Active -> {cam_device} ({width}x{height} @ {fps} FPS)",
        f"Scale: {scale:.1f}x   Zoom: {zoom:.1f}x (Font: {font_size}px)   Pan: ({dx}, {dy})",
        "Controls: [Arrows / WASD] Pan   [+ / -] Zoom   [0] Reset   [Q / ESC] Quit",
    ]
    for row, text in enumerate(lines):
        try:
            stdscr.addstr(row, 0, text)
        except curses.error:
            pass
    stdscr.refresh()


def main_vcam(stdscr, path: int | str, scale: float = 1.0, reverse: bool = False):
    init_curses(stdscr)
    is_image, is_video, cap, static_frame, height, width, fps = open_media_source(path, min_fps=20.0)
    cam_fps = int(round(fps))

    aa_rows, aa_cols = image_shape_to_aa_shape(shape=(height, width), scale=scale)
    base_font_size = max(4, int(round(EnvVars.FONT_HEIGHT / scale)))

    zoom = 1.0
    font_size = base_font_size
    vcam_font = load_mono_font(size=font_size)
    view_rows, view_cols = aa_rows, aa_cols
    dx, dy = 0, 0

    frame_time = 1.0 / cam_fps if cam_fps > 0 else 1.0 / 30.0

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=cam_fps) as cam:
            draw_vcam_hud(stdscr, cam.device, width, height, cam_fps, scale, zoom, font_size, dx, dy)

            while True:
                start = time.perf_counter() if is_video else 0.0

                key = stdscr.getch()
                if key == curses.KEY_RESIZE:
                    draw_vcam_hud(stdscr, cam.device, width, height, cam_fps, scale, zoom, font_size, dx, dy)
                elif key != -1:
                    dx, dy, zoom, changed, should_quit = handle_nav_key(
                        key, dx, dy, zoom, 1.0, 0.2, 5.0, aa_rows, aa_cols, view_rows, view_cols
                    )
                    if should_quit:
                        break
                    if changed:
                        view_rows = max(1, int(round(aa_rows / zoom)))
                        view_cols = max(1, int(round(aa_cols / zoom)))
                        new_font_size = max(4, int(round(base_font_size * zoom)))
                        if new_font_size != font_size:
                            font_size = new_font_size
                            vcam_font = load_mono_font(size=font_size)
                        draw_vcam_hud(stdscr, cam.device, width, height, cam_fps, scale, zoom, font_size, dx, dy)

                if is_image:
                    frame = static_frame
                else:
                    ret, frame = cap.read()
                    if not ret:
                        break

                aa_frame = image2aa(frame, scale=scale, reverse=reverse, blur_size=3)
                r0, rn, c0, cn, x0, y0 = compute_viewport_slices(dx, dy, aa_rows, aa_cols, view_rows, view_cols)

                viewport = np.full((view_rows, view_cols), ord(" "), dtype=np.uint8)
                if c0 < cn and r0 < rn:
                    viewport[y0:y0 + (rn - r0), x0:x0 + (cn - c0)] = aa_frame[r0:rn, c0:cn]

                aa_image = aa2image(viewport, font=vcam_font)
                aa_image = cv2.resize(aa_image, dsize=(width, height), interpolation=cv2.INTER_LINEAR)

                cam.send(aa_image)
                cam.sleep_until_next_frame()

                if is_video:
                    elapsed = time.perf_counter() - start
                    sleep_time = frame_time - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
    finally:
        if cap is not None:
            cap.release()


if __name__ == "__main__":
    args = docopt(__doc__)
    input_path = args["--input"]
    reverse_flag = args["--reverse"]
    output = str(args["--output"]).lower()
    scale_factor = float(args["--scale"]) if args["--scale"] else 1.0

    font_h, font_w = map(int, args["--font-shape"].split(","))
    EnvVars.set_font_shape(font_h, font_w)
    EnvVars.set_chars(args["--chars"])

    try:
        input_path = int(input_path)
    except ValueError:
        pass  # Keep input_path as a string if it cannot be converted to int

    if output.lower().startswith("t"):
        curses.wrapper(partial(main_curses, path=input_path, scale=scale_factor, reverse=reverse_flag))
    elif output.lower().startswith(("v", "0")):
        curses.wrapper(partial(main_vcam, path=input_path, scale=scale_factor, reverse=reverse_flag))