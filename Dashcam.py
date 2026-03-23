#!/usr/bin/env python3
import os
import time
import math
import threading
import subprocess
import collections
import logging
from datetime import datetime
from pathlib import Path

from sense_hat import SenseHat

# Where crash clips and temp segments are stored
SAVE_DIR = Path("/home/igneus/crash_clips")
TEMP_DIR = Path("/tmp/crash_segments")

# Each rolling segment length in seconds
SEGMENT_SECONDS = 10

# How many segments to keep (total buffer = SEGMENT_SECONDS * NUM_SEGMENTS)
# Default: 6 x 10s = 60 seconds
NUM_SEGMENTS = 6

# Video settings
VIDEO_WIDTH   = 1280
VIDEO_HEIGHT  = 720
VIDEO_FPS     = 30
VIDEO_BITRATE = "4000000"  # 4 Mbps

# Accelerometer crash threshold in G
ACCEL_THRESHOLD = 1.5

# Gyroscope orientation window (seconds) to check for tilt
ORIENTATION_WINDOW_S = 2.0

# Minimum orientation change in degrees to confirm crash
ORIENTATION_CHANGE_THRESHOLD = 20.0

# Minimum seconds between saves (debounce)
DEBOUNCE_S = 5.0

# Extra seconds to record after crash before saving
POST_CRASH_SECONDS = 10

# Sensor polling rate
POLL_INTERVAL = 0.05  # 20 Hz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("crash_cam")


GREEN  = (0,   200, 0  )
RED    = (220, 0,   0  )
BLUE   = (0,   0,   200)
YELLOW = (220, 200, 0  )


def led_solid(sense, colour):
    sense.set_pixels([colour] * 64)


def led_flash(sense, colour, times=20, hz=4):
    interval = 1.0 / (hz * 2)
    for _ in range(times):
        sense.set_pixels([colour] * 64)
        time.sleep(interval)
        sense.clear()
        time.sleep(interval)



class OrientationHistory:
    """Keeps a timestamped rolling history of pitch and roll readings."""

    def __init__(self, window_seconds):
        self.window = window_seconds
        self._lock = threading.Lock()
        self._history = collections.deque()

    def record(self, pitch, roll):
        now = time.monotonic()
        with self._lock:
            self._history.append((now, pitch, roll))
            cutoff = now - self.window
            while self._history and self._history[0][0] < cutoff:
                self._history.popleft()

    def max_change_in_window(self):
        with self._lock:
            if len(self._history) < 2:
                return 0.0
            pitches = [h[1] for h in self._history]
            rolls   = [h[2] for h in self._history]

        def angular_range(angles):
            sins = [math.sin(math.radians(a)) for a in angles]
            coss = [math.cos(math.radians(a)) for a in angles]
            mean = math.degrees(math.atan2(
                sum(sins) / len(sins),
                sum(coss) / len(coss)
            ))
            return max(abs(((a - mean + 180) % 360) - 180) for a in angles)

        return max(angular_range(pitches), angular_range(rolls))



class SegmentManager:
    """
    Records a continuous stream of short video segments using rpicam-vid.
    Keeps only the most recent NUM_SEGMENTS segments on disk.
    Segments are raw H264 and can be simply concatenated on a crash.
    """

    def __init__(self):
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        for f in TEMP_DIR.glob("seg_*.h264"):
            f.unlink()

        self._lock     = threading.Lock()
        self._segments = collections.deque()
        self._proc     = None
        self._running  = False
        self._thread   = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        log.info("Segment manager started.")

    def stop(self):
        self._running = False
        self._kill_proc()

    def _kill_proc(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def _record_loop(self):
        seg_index = 0
        while self._running:
            seg_path = TEMP_DIR / "seg_{:06d}.h264".format(seg_index)
            seg_index += 1

            cmd = [
                "rpicam-vid",
                "--width",     str(VIDEO_WIDTH),
                "--height",    str(VIDEO_HEIGHT),
                "--framerate", str(VIDEO_FPS),
                "--bitrate",   VIDEO_BITRATE,
                "--timeout",   str(SEGMENT_SECONDS * 1000),
                "--nopreview",
                "-o", str(seg_path),
            ]

            log.debug("Recording segment: %s", seg_path.name)
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._proc.wait()

            if seg_path.exists() and seg_path.stat().st_size > 0:
                with self._lock:
                    self._segments.append(seg_path)
                    while len(self._segments) > NUM_SEGMENTS:
                        old = self._segments.popleft()
                        try:
                            old.unlink()
                        except FileNotFoundError:
                            pass

    def get_segments(self):
        with self._lock:
            return list(self._segments)

    def stitch_to_file(self, dest_path):
        """
        Concatenate all buffered H264 segments into a single file by
        simply appending bytes - works natively with raw H264.
        Returns total bytes written.
        """
        segments = self.get_segments()
        if not segments:
            raise RuntimeError("No segments available to stitch.")

        total = 0
        with open(dest_path, "wb") as out:
            for seg in segments:
                try:
                    data = seg.read_bytes()
                    out.write(data)
                    total += len(data)
                except FileNotFoundError:
                    log.warning("Segment missing during stitch: %s", seg.name)

        return total

class CrashCam:

    def __init__(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)

        # Pre-initialise RTIMU so sense_hat can find a valid RTIMULib.ini
        import RTIMU
        _settings = RTIMU.Settings("RTIMULib")
        _imu = RTIMU.RTIMU(_settings)
        _imu.IMUInit()
        log.info("RTIMU pre-init OK: %s", _imu.IMUName())

        self.sense = SenseHat()
        self.sense.set_imu_config(
            compass_enabled=False,
            gyro_enabled=True,
            accel_enabled=True,
        )

        self.segments    = SegmentManager()
        self.ori_history = OrientationHistory(ORIENTATION_WINDOW_S)

        self._last_save  = 0.0
        self._saving     = False
        self._running    = False

    def _sensor_loop(self):
        log.info("Sensor loop running at %.0f Hz.", 1 / POLL_INTERVAL)
        while self._running:
            accel = self.sense.get_accelerometer_raw()
            ori   = self.sense.get_orientation_degrees()

            ax = accel["x"]
            ay = accel["y"]
            az = accel["z"]

            pitch = ori.get("pitch", 0.0)
            roll  = ori.get("roll",  0.0)

            # Net impact G (remove constant 1 G gravity component)
            g_mag    = math.sqrt(ax**2 + ay**2 + az**2)
            impact_g = abs(g_mag - 1.0)

            self.ori_history.record(pitch, roll)
            ori_change = self.ori_history.max_change_in_window()

            # Live debug output
            print(
                "\rImpact: {:.2f}G  Pitch: {:.1f}  Roll: {:.1f}  OrChange: {:.1f}  ".format(
                    impact_g, pitch, roll, ori_change
                ),
                end="", flush=True
            )

            now = time.monotonic()
            if (
                not self._saving
                and impact_g >= ACCEL_THRESHOLD
                and (now - self._last_save) > DEBOUNCE_S
            ):
                if ori_change >= ORIENTATION_CHANGE_THRESHOLD:
                    log.warning("\nCRASH CONFIRMED - saving clip.")
                    threading.Thread(
                        target=self._save_clip,
                        args=(impact_g, ori_change),
                        daemon=True,
                    ).start()
                else:
                    log.info(
                        "\nFalse positive ignored (%.1f° < %.1f° threshold).",
                        ori_change, ORIENTATION_CHANGE_THRESHOLD,
                    )

            time.sleep(POLL_INTERVAL)

    def _save_clip(self, impact_g, ori_change):
        self._saving = True

        flash_thread = threading.Thread(
            target=led_flash,
            args=(self.sense, RED, 20, 4),
            daemon=True,
        )
        flash_thread.start()

        log.info("Waiting %ds for post-crash footage...", POST_CRASH_SECONDS)
        time.sleep(POST_CRASH_SECONDS)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clip_path = SAVE_DIR / "crash_{}_{:.1f}G.h264".format(timestamp, impact_g)
        meta_path = SAVE_DIR / "crash_{}_{:.1f}G.txt".format(timestamp, impact_g)

        try:
            size = self.segments.stitch_to_file(clip_path)
            self._last_save = time.monotonic()
            log.info("Clip saved: %s (%.1f MB)", clip_path.name, size / 1e6)

            with open(meta_path, "w") as f:
                f.write("Timestamp        : {}\n".format(timestamp))
                f.write("Impact           : {:.2f} G\n".format(impact_g))
                f.write("Orientation change: {:.1f} degrees\n".format(ori_change))
                f.write("Buffer duration  : {}s\n".format(SEGMENT_SECONDS * NUM_SEGMENTS))
                f.write("Post-crash window: {}s\n".format(POST_CRASH_SECONDS))
                f.write("Resolution       : {}x{} @ {}fps\n".format(
                    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS))

            flash_thread.join()
            led_solid(self.sense, BLUE)
            time.sleep(3)

        except Exception as exc:
            log.error("Failed to save clip: %s", exc)
            flash_thread.join()
            led_solid(self.sense, YELLOW)
            time.sleep(3)

        finally:
            led_solid(self.sense, GREEN)
            self._saving = False

    def run(self):
        log.info("CrashCam starting...")
        log.info(
            "Thresholds - Impact: %.1f G | Orientation: %.1f deg | Buffer: %ds",
            ACCEL_THRESHOLD,
            ORIENTATION_CHANGE_THRESHOLD,
            SEGMENT_SECONDS * NUM_SEGMENTS,
        )

        self._running = True
        self.segments.start()
        time.sleep(2)

        led_solid(self.sense, GREEN)

        sensor_thread = threading.Thread(target=self._sensor_loop, daemon=True)
        sensor_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Shutting down...")
        finally:
            self._running = False
            self.segments.stop()
            self.sense.clear()
            log.info("CrashCam stopped.")


if __name__ == "__main__":
    cam = CrashCam()
    cam.run()
