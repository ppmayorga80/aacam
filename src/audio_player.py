import math
import os
import subprocess
import sys
import tempfile
import time


class AudioPlayer:
    """Cross-platform in-process audio player for video files (macOS & Windows)."""

    def __init__(self, path: str):
        self.platform = sys.platform
        self.active = False
        self._player = None
        self._wav_path = None
        self._start_time = 0.0
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

    def _find_ffmpeg_win(self) -> str:
        """Localiza ffmpeg.exe dentro de ffpyplayer, imageio_ffmpeg o en el PATH."""
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
            import winsound
        except ImportError:
            return

        ffmpeg_bin = self._find_ffmpeg_win()

        fd, wav_path = tempfile.mkstemp(prefix="aacam_", suffix=".wav")
        os.close(fd)
        self._wav_path = wav_path

        # Extrae solo el audio a WAV PCM (sin tocar SDL2 ni ventanas gráficas)
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-i", abs_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            wav_path,
        ]

        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            res = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            if res.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) <= 44:
                self._cleanup_wav()
                return

            winsound.PlaySound(
                wav_path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            self._start_time = time.perf_counter()
            self.active = True
        except Exception:
            self._cleanup_wav()

    def _cleanup_wav(self) -> None:
        if self._wav_path and os.path.exists(self._wav_path):
            try:
                os.remove(self._wav_path)
            except OSError:
                pass
        self._wav_path = None

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

        if self.platform == "darwin" and self._player is not None:
            pts = self._cm_time_get_seconds(self._player.currentTime())
            return float(pts) if math.isfinite(pts) else 0.0

        if self.platform == "win32":
            return time.perf_counter() - self._start_time

        return 0.0

    def close(self) -> None:
        """Stop playback and release OS audio resources."""
        if not self.active:
            return

        if self.platform == "darwin" and self._player is not None:
            self._player.pause()
            self._player = None
        elif self.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, 0)
            except Exception:
                pass
            self._cleanup_wav()

        self.active = False

    def __enter__(self) -> "AudioPlayer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()