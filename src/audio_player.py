import math
import os
import subprocess
import sys
import tempfile
import time


class AudioPlayer:
    """Cross-platform in-process audio player for video files."""

    def __init__(self, path: str):
        self.platform = sys.platform
        self.active = False
        self._player = None
        self._wav_path = None

        abs_path = os.path.abspath(path)

        if self.platform == "darwin":
            self._init_macos(abs_path)
        elif self.platform == "win32":
            self._init_windows(abs_path)

    # ==========================================================
    # MACOS
    # ==========================================================

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

        while (
            self._player.status() == 0
            and time.perf_counter() < deadline
        ):
            self._run_loop.runUntilDate_(
                self._ns_date.dateWithTimeIntervalSinceNow_(0.01)
            )

        self.active = self._player.status() == 1

    # ==========================================================
    # WINDOWS
    # ==========================================================

    def _find_ffmpeg_win(self) -> str:

        try:
            import ffpyplayer

            pkg_dir = os.path.dirname(ffpyplayer.__file__)

            for root, _, files in os.walk(pkg_dir):
                for f in files:
                    if f.lower() == "ffmpeg.exe":
                        return os.path.join(root, f)

        except Exception:
            pass

        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()

        except Exception:
            pass

        return "ffmpeg"

    def _init_windows(self, abs_path: str) -> None:

        if not os.path.exists(abs_path):
            return

        try:
            import pygame
        except ImportError:
            return

        ffmpeg_bin = self._find_ffmpeg_win()

        fd, wav_path = tempfile.mkstemp(
            prefix="aacam_",
            suffix=".wav"
        )

        os.close(fd)

        self._wav_path = wav_path

        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-i",
            abs_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            wav_path,
        ]

        try:

            creationflags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

            res = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )

            if (
                res.returncode != 0
                or not os.path.exists(wav_path)
                or os.path.getsize(wav_path) <= 44
            ):
                self._cleanup_wav()
                return

            pygame.mixer.init(
                frequency=44100,
                size=-16,
                channels=2,
            )

            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()

            self.active = True

        except Exception as exc:
            print(exc)
            self._cleanup_wav()

    # ==========================================================
    # COMMON
    # ==========================================================

    def _cleanup_wav(self) -> None:

        if self._wav_path and os.path.exists(self._wav_path):
            try:
                os.remove(self._wav_path)
            except OSError:
                pass

        self._wav_path = None

    def tick(self) -> None:

        if self.platform == "darwin" and self.active:
            self._run_loop.runMode_beforeDate_(
                self._default_mode,
                self._ns_date.distantPast(),
            )

    def get_time(self) -> float:

        if not self.active:
            return 0.0

        if self.platform == "darwin" and self._player is not None:

            pts = self._cm_time_get_seconds(
                self._player.currentTime()
            )

            return (
                float(pts)
                if math.isfinite(pts)
                else 0.0
            )

        if self.platform == "win32":

            try:
                import pygame

                pos_ms = pygame.mixer.music.get_pos()

                if pos_ms < 0:
                    return 0.0

                return pos_ms / 1000.0

            except Exception:
                return 0.0

        return 0.0

    def close(self) -> None:

        if not self.active:
            return

        if self.platform == "darwin" and self._player is not None:

            self._player.pause()
            self._player = None

        elif self.platform == "win32":

            try:
                import pygame

                pygame.mixer.music.stop()
                pygame.mixer.quit()

            except Exception:
                pass

            self._cleanup_wav()

        self.active = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()