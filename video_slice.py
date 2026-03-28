"""
ComfyUI custom node: slice .mov / .mp4 and output one frame as IMAGE.
Upload via "choose file to upload" (frontend) or place files under ComfyUI input/.
"""

import os
import random
import secrets
import time
import numpy as np
import torch

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import folder_paths
    HAS_FOLDER_PATHS = True
except ImportError:
    HAS_FOLDER_PATHS = False

VIDEO_EXTENSIONS = (".mp4", ".mov")

# Last slice-list index per absolute video path (for increment / decrement)
_SLICE_INDEX_STATE: dict[str, int] = {}


def _get_video_list_from_input():
    if not HAS_FOLDER_PATHS:
        return []
    try:
        input_dir = folder_paths.get_input_directory()
        if not os.path.isdir(input_dir):
            return []
        out = []
        for root, _dirs, files in os.walk(input_dir, followlinks=True):
            rel = os.path.relpath(root, input_dir)
            for f in files:
                if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
                    if rel == ".":
                        out.append(f)
                    else:
                        out.append(os.path.join(rel, f).replace("\\", "/"))
        return sorted(out)
    except Exception:
        return []


def _input_dir_fingerprint():
    if not HAS_FOLDER_PATHS:
        return 0
    try:
        input_dir = folder_paths.get_input_directory()
        if not os.path.isdir(input_dir):
            return 0
        mtimes = []
        for root, _dirs, files in os.walk(input_dir, followlinks=True):
            for f in files:
                if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
                    p = os.path.join(root, f)
                    try:
                        mtimes.append(os.path.getmtime(p))
                    except OSError:
                        pass
        return (len(mtimes), round(max(mtimes, default=0), 3))
    except Exception:
        return 0


def _resolve_video_path(**kwargs):
    if "video" in kwargs:
        video_name = kwargs["video"]
        if HAS_FOLDER_PATHS and video_name:
            input_dir = folder_paths.get_input_directory()
            return os.path.join(input_dir, video_name)
        return ""
    return (kwargs.get("video_path") or "").strip()


def _wrap_size(n: int, loop_on: bool, loop_every_n_frames: int) -> int:
    if n <= 0:
        return 1
    if loop_on and loop_every_n_frames > 0:
        return max(1, min(loop_every_n_frames, n))
    return n


def _next_index_increment(path_key: str, n: int, wrap: int) -> int:
    prev = _SLICE_INDEX_STATE.get(path_key)
    if prev is None:
        idx = 0
    else:
        idx = (prev + 1) % wrap
    _SLICE_INDEX_STATE[path_key] = idx
    return idx


def _next_index_decrement(path_key: str, n: int, wrap: int) -> int:
    prev = _SLICE_INDEX_STATE.get(path_key)
    if prev is None:
        idx = (wrap - 1) % wrap
    else:
        idx = (prev - 1) % wrap
    _SLICE_INDEX_STATE[path_key] = idx
    return idx


def _apply_lag(idx: int, n: int, lag_on: bool) -> int:
    if not lag_on or n <= 1:
        return idx
    if random.random() >= 0.5:
        return idx
    deltas = [d for d in range(-7, 8) if d != 0]
    delta = random.choice(deltas)
    return min(max(0, idx + delta), n - 1)


class IBVideoSlicer:
    """
    Video → single IMAGE frame. frame_mode: increment / decrement / random over slice list.
    Optional lag: 50% chance to nudge slice index by ±1…±7 (clamped).
    """

    @classmethod
    def INPUT_TYPES(cls):
        video_files = _get_video_list_from_input()
        common = {
            "frame_mode": (
                ["increment", "decrement", "random"],
                {"default": "increment"},
            ),
            "lag_on": ("BOOLEAN", {"default": False}),
            "loop_on": ("BOOLEAN", {"default": False}),
            "loop_every_n_frames": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "If loop on: 0 = wrap full slice list; N>0 = wrap first N indices only.",
                },
            ),
            "start_frame": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1, "step": 1, "display": "number"}),
            "end_frame": ("INT", {"default": -1, "min": -1, "max": 2**31 - 1, "step": 1, "display": "number"}),
            "skip_every_n_frames": (
                "INT",
                {
                    "default": 1,
                    "min": 1,
                    "max": 10000,
                    "step": 1,
                    "display": "number",
                    "tooltip": "1 = every frame in range; 2 = every second, etc.",
                },
            ),
        }
        return {
            "required": {
                "video": (
                    video_files if video_files else [""],
                    {"default": video_files[0] if video_files else ""},
                ),
                **common,
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "image",
        "image_width",
        "image_height",
        "total_frames_count",
        "current_frame_count",
        "slice_index",
    )
    FUNCTION = "slice_frame"
    CATEGORY = "video"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Increment/decrement/lag/random must not be cached; input folder still tracked for new uploads
        return (time.time_ns(), _input_dir_fingerprint())

    def slice_frame(self, frame_mode, lag_on, loop_on, loop_every_n_frames, start_frame, end_frame, skip_every_n_frames, video, **kwargs):
        if not HAS_CV2:
            raise ModuleNotFoundError(
                "OpenCV (opencv-python) is required. Install: pip install opencv-python"
            )
        if "every_nth_frame" in kwargs and kwargs["every_nth_frame"] is not None:
            skip_every_n_frames = max(1, int(kwargs["every_nth_frame"]))

        kw = {k: v for k, v in kwargs.items() if k != "video"}
        path = _resolve_video_path(video=video, **kw)
        if not path or not os.path.isfile(path):
            raise FileNotFoundError(
                f"Video file not found. Upload or choose a file in the video list, or put .mp4/.mov in input/. Got: {path!r}"
            )

        lower = path.lower()
        if not (lower.endswith(".mp4") or lower.endswith(".mov")):
            raise ValueError("Only .mp4 and .mov are supported.")

        path_key = os.path.abspath(path)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {path}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                raise RuntimeError("Video has no frames or frame count unknown.")

            effective_start = start_frame
            effective_end = end_frame if end_frame >= 0 else (total_frames - 1)
            effective_end = min(effective_end, total_frames - 1)

            if effective_start > effective_end:
                raise ValueError(
                    f"Effective start frame ({effective_start}) is after effective end ({effective_end})."
                )

            indices = []
            i = effective_start
            while i <= effective_end:
                indices.append(i)
                i += skip_every_n_frames

            if not indices:
                raise ValueError("No frames in selected range with given skip_every_n_frames.")

            n = len(indices)
            wrap = _wrap_size(n, loop_on, loop_every_n_frames)

            rng = random.Random(secrets.randbits(64))

            if frame_mode == "random":
                idx = rng.randint(0, n - 1)
            elif frame_mode == "decrement":
                idx = _next_index_decrement(path_key, n, wrap)
            else:
                idx = _next_index_increment(path_key, n, wrap)

            idx = _apply_lag(idx, n, lag_on)

            video_frame_number = indices[idx]

            cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame_number)
            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                raise RuntimeError(f"Failed to read frame {video_frame_number} from {path}.")

            frame_rgb = frame_bgr[:, :, ::-1].copy()
            img_float = np.array(frame_rgb, dtype=np.float32) / 255.0
            image = torch.from_numpy(img_float)[None, ...]

            height, width = image.shape[1], image.shape[2]
            return (image, width, height, total_frames, video_frame_number, idx)

        finally:
            cap.release()


VideoSliceFrame = IBVideoSlicer

NODE_CLASS_MAPPINGS = {
    "IBVideoSlicer": IBVideoSlicer,
    "VideoSliceFrame": IBVideoSlicer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IBVideoSlicer": "ib video slicer",
    "VideoSliceFrame": "ib video slicer",
}
