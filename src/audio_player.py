import ctypes
import math
import os
import sys
import time


class AudioPlayer:
    """Cross-platform in-process audio player for video files (macOS & Windows)."""

    def __init__(self, path: str):
        self.platform = sys.platform
        self.active = False
        abs_path = os.path.abspath(path)

        if self.platform == "darwin":
            self._init_macos(abs_path)
        elif self.platform == "win32":
            self._init_windows(abs_path)

    def _init_macos(self, abs_path: str) -> None:
        try:
            from Foundation import NSURL, NSRunLoop, NSDate, NSDefaultRunLoopMode
            from AVFoundation import AVPlayer
            from CoreMedia import CMTimeGetSeconds
        except ImportError:
            return

        self._run_loop = NSRunLoop.currentRunLoop()
        self._ns_date = NSDate
        self._default_mode = NSDefaultRunLoopMode
        self._cm_time_get_seconds = CMTimeGetSeconds

        url = NSURL.fileURLWithPath_(abs_path)
        self._player = AVPlayer.playerWithURL_(url)
        self._player.setVolume_(1.0)
        self._player.play()

        deadline = time.perf_counter() + 1.0
        while self._player.status() == 0 and time.perf_counter() < deadline:
            self._run_loop.runUntilDate_(
                self._ns_date.dateWithTimeIntervalSinceNow_(0.01)
            )

        self.active = self._player.status() == 1

    def _init_windows(self, abs_path: str) -> None:
        try:
            self._winmm = ctypes.windll.winmm
        except AttributeError:
            return

        self._alias = f"aacam_audio_{os.getpid()}_{id(self)}"
        err = self._mci(f'open "{abs_path}" type mpegvideo alias {self._alias}')
        if err != 0:
            err = self._mci(f'open "{abs_path}" alias {self._alias}')

        if err == 0:
            self._mci(f"set {self._alias} time format milliseconds")
            if self._mci(f"play {self._alias}") == 0:
                self.active = True
            else:
                self._mci(f"close {self._alias}")

    def _mci(self, cmd: str) -> int:
        return self._winmm.mciSendStringW(cmd, None, 0, None)

    def tick(self) -> None:
        """Pump the OS event loop when required (macOS AVPlayer)."""
        if self.platform == "darwin" and self.active:
            self._run_loop.runMode_beforeDate_(
                self._default_mode, self._ns_date.distantPast()
            )

    def get_time(self) -> float:
        """Return current audio playback position in seconds."""
        if not self.active:
            return 0.0

        if self.platform == "darwin":
            pts = self._cm_time_get_seconds(self._player.currentTime())
            return float(pts) if math.isfinite(pts) else 0.0

        if self.platform == "win32":
            buf = ctypes.create_unicode_buffer(64)
            err = self._winmm.mciSendStringW(
                f"status {self._alias} position", buf, 64, None
            )
            if err == 0 and buf.value.isdigit():
                return int(buf.value) / 1000.0

        return 0.0

    def close(self) -> None:
        """Stop playback and release OS audio resources."""
        if not self.active:
            return

        if self.platform == "darwin":
            self._player.pause()
            self._player = None
        elif self.platform == "win32":
            self._mci(f"stop {self._alias}")
            self._mci(f"close {self._alias}")

        self.active = False

    def __enter__(self) -> "AudioPlayer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()