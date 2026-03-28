"""
ComfyUI custom node: slice .mov / .mp4 and output one frame as IMAGE.
Upload videos via ComfyUI's Input sidebar (drag-drop into input/), then pick from the list or set path override.
"""

import os
import random
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
    """Rough fingerprint of input folder so IS_CHANGED picks up new uploads."""
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
    path_override = (kwargs.get("path_override") or "").strip()
    if path_override and os.path.isfile(path_override):
        return path_override
    if "video" in kwargs:
        video_name = kwargs["video"]
        if HAS_FOLDER_PATHS and video_name:
            input_dir = folder_paths.get_input_directory()
            return os.path.join(input_dir, video_name)
        return ""
    return (kwargs.get("video_path") or "").strip()


class IBVideoSlicer:
    """
    Select a video from ComfyUI input (upload via Input tab) or path, output one frame.
    Optional random pick, loop / loop window, and readable frame counter outputs.
    """

    @classmethod
    def INPUT_TYPES(cls):
        video_choices = _get_video_list_from_input()
        common = {
            "random_frame": ("BOOLEAN", {"default": False}),
            "random_seed": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "When random is on: 0 = different frame each run; >0 = fixed pick for that seed.",
                },
            ),
            "loop_on": ("BOOLEAN", {"default": False}),
            "loop_every_n_frames": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "When loop is on: 0 = wrap over full clip; N>0 = wrap over first N slice indices only.",
                },
            ),
            "start_frame": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1, "step": 1, "display": "number"}),
            "end_frame": ("INT", {"default": -1, "min": -1, "max": 2**31 - 1, "step": 1, "display": "number"}),
            "skip_first_n_frames": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1, "step": 1, "display": "number"}),
            "skip_every_n_frames": (
                "INT",
                {
                    "default": 1,
                    "min": 1,
                    "max": 10000,
                    "step": 1,
                    "display": "number",
                    "tooltip": "1 = use every frame in range; 2 = every 2nd; 3 = every 3rd, etc.",
                },
            ),
            "current_frame_index": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Index into the slice list (after skip/every-nth). Ignored when random is on.",
                },
            ),
        }
        if HAS_FOLDER_PATHS and video_choices:
            return {
                "required": {
                    "video": (
                        video_choices,
                        {
                            "default": video_choices[0],
                            "tooltip": "Files from ComfyUI input/. Upload: sidebar → Input → drag .mp4 / .mov here, then refresh if needed.",
                        },
                    ),
                    **common,
                },
                "optional": {
                    "path_override": (
                        "STRING",
                        {
                            "default": "",
                            "multiline": False,
                            "placeholder": "Full path overrides dropdown (server path, e.g. RunPod /workspace/...)",
                        },
                    ),
                },
            }
        return {
            "required": {
                "video_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "Full path to .mp4 or .mov (or upload to input/ and restart to get dropdown)",
                    },
                ),
                **common,
            },
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("image", "image_width", "image_height", "slice_index", "video_frame", "frame_readout")
    FUNCTION = "slice_frame"
    CATEGORY = "video"

    @classmethod
    def IS_CHANGED(
        cls,
        random_frame,
        random_seed,
        loop_on,
        loop_every_n_frames,
        start_frame,
        end_frame,
        skip_first_n_frames,
        skip_every_n_frames,
        current_frame_index,
        **kwargs,
    ):
        path = _resolve_video_path(**kwargs)
        fp = _input_dir_fingerprint()
        base = (path, fp, start_frame, end_frame, skip_first_n_frames, skip_every_n_frames, loop_on, loop_every_n_frames)
        if random_frame:
            if random_seed != 0:
                return base + ("rand", random_seed)
            return base + ("rand", time.time_ns())
        return base + ("seq", current_frame_index)

    def slice_frame(
        self,
        random_frame,
        random_seed,
        loop_on,
        loop_every_n_frames,
        start_frame,
        end_frame,
        skip_first_n_frames,
        skip_every_n_frames,
        current_frame_index,
        **kwargs,
    ):
        if not HAS_CV2:
            raise ModuleNotFoundError(
                "OpenCV (opencv-python) is required. Install: pip install opencv-python"
            )
        # Backward compat: old workflows may pass every_nth_frame
        if "every_nth_frame" in kwargs and kwargs["every_nth_frame"] is not None:
            skip_every_n_frames = int(kwargs["every_nth_frame"])
        path = _resolve_video_path(**kwargs)
        if not path or not os.path.isfile(path):
            raise FileNotFoundError(f"Video file not found: {path!r}")

        lower = path.lower()
        if not (lower.endswith(".mp4") or lower.endswith(".mov")):
            raise ValueError("Only .mp4 and .mov are supported.")

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {path}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                raise RuntimeError("Video has no frames or frame count unknown.")

            effective_start = start_frame + skip_first_n_frames
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

            if random_frame:
                if random_seed > 0:
                    rng = random.Random(random_seed)
                    idx = rng.randint(0, n - 1)
                else:
                    idx = random.randint(0, n - 1)
            elif loop_on:
                window = loop_every_n_frames if loop_every_n_frames > 0 else n
                window = max(1, min(window, n))
                idx = current_frame_index % window
            else:
                idx = min(max(0, current_frame_index), n - 1)

            video_frame_number = indices[idx]

            cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame_number)
            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                raise RuntimeError(f"Failed to read frame {video_frame_number} from {path}.")

            frame_rgb = frame_bgr[:, :, ::-1].copy()
            img_float = np.array(frame_rgb, dtype=np.float32) / 255.0
            image = torch.from_numpy(img_float)[None, ...]

            height, width = image.shape[1], image.shape[2]
            readout = (
                f"slice {idx + 1}/{n}  |  video frame {video_frame_number}  |  "
                f"{'random' if random_frame else 'sequential'}{'' if random_frame else ('  loop' if loop_on else '')}"
            )
            return (image, width, height, idx, video_frame_number, readout)

        finally:
            cap.release()


# Legacy class name: same implementation (saved workflows may reference either)
VideoSliceFrame = IBVideoSlicer

NODE_CLASS_MAPPINGS = {
    "IBVideoSlicer": IBVideoSlicer,
    "VideoSliceFrame": IBVideoSlicer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IBVideoSlicer": "ib video slicer",
    "VideoSliceFrame": "ib video slicer",
}
