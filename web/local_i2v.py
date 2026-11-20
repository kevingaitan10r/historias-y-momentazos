"""Local Image-to-Video (I2V) Animation Module for Apple Silicon M4.
Provides:
1. 3D Parallax & Depth Motion Video (Ultra-fast 3D camera orbit & breathing displacement)
2. Stable Video Diffusion (SVD-XT) Frame Diffusion
"""
import os
import sys
import time
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
FFMPEG_BIN = str(BASE_DIR / ".venv" / "bin" / "ffmpeg")
MODELS_CACHE_DIR = BASE_DIR / "web" / "models"
MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_SVD_PIPE = None

def get_system_ai_status() -> dict:
    """Returns local AI and hardware status."""
    has_torch = False
    has_mps = False
    try:
        import torch
        has_torch = True
        has_mps = torch.backends.mps.is_available()
    except Exception:
        pass

    return {
        "hardware": "Apple M4 (16GB)",
        "torch": has_torch,
        "mps": has_mps,
        "modes_available": [
            {"id": "3d_motion", "name": "🎬 Video 3D Parallax & Profundidad (Rápido, 2 seg)", "default": True},
            {"id": "svd", "name": "🤖 Stable Video Diffusion IA (Cuadro a Cuadro)", "default": False}
        ]
    }

def generate_3d_parallax_video(image_path: str, output_path: str, duration: float = 4.0, fps: int = 30) -> str:
    """
    Generates a cinematic 3D parallax motion video from a 2D/3D image using depth disparity warping.
    The characters float and move in realistic 3D perspective relative to the background.
    """
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    H_orig, W_orig = img.shape[:2]
    W, H = 1080, 1920
    if (W_orig, H_orig) != (W, H):
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)

    # Compute depth proxy: central subject prominence + bilateral filtered luminance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    y_coords, x_coords = np.mgrid[0:H, 0:W]
    cx, cy = float(W / 2), float(H * 0.45)
    dist = np.sqrt(((x_coords - cx) / (W / 2)) ** 2 + ((y_coords - cy) / (H / 2)) ** 2)
    depth_base = np.clip(1.0 - dist * 0.72, 0.08, 1.0)
    depth_lum = cv2.bilateralFilter(gray.astype(np.float32) / 255.0, 9, 75, 75)
    depth = (depth_base * 0.65 + depth_lum * 0.35).astype(np.float32)

    total_frames = max(int(fps * duration), 30)
    temp_raw = Path(output_path).parent / f"raw_3d_{int(time.time() * 1000)}.mp4"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(temp_raw), fourcc, fps, (W, H))

    for i in range(total_frames):
        t = i / total_frames
        phase = 2.0 * np.pi * t
        
        # Smooth camera orbit and breathing oscillation
        shift_x = float(np.sin(phase) * 16.0)
        shift_y = float(np.cos(phase * 2.0) * 7.0)
        scale = float(1.0 + 0.032 * np.sin(phase))

        map_x = ((x_coords.astype(np.float32) + (depth * shift_x) - cx) / scale + cx).astype(np.float32)
        map_y = ((y_coords.astype(np.float32) + (depth * shift_y) - cy) / scale + cy).astype(np.float32)

        warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        writer.write(warped)

    writer.release()

    # Re-encode with FFmpeg into clean H.264
    cmd_h264 = [
        FFMPEG_BIN, "-y",
        "-i", str(temp_raw),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "18",
        str(output_path)
    ]
    subprocess.run(cmd_h264, capture_output=True, check=True)

    try:
        temp_raw.unlink()
    except Exception:
        pass

    return output_path

def generate_svd_diffusion_video(
    image_path: str,
    output_path: str,
    duration: float = 4.0,
    motion_bucket_id: int = 127,
    fps: int = 7,
    num_frames: int = 25
) -> str:
    """
    Generates video with full AI frame diffusion using Stable Video Diffusion (SVD-XT).
    """
    global _SVD_PIPE
    from PIL import Image
    import torch

    in_img = Image.open(image_path).convert("RGB")
    target_size = (576, 1024)
    img_resized = in_img.resize(target_size, Image.LANCZOS)

    if _SVD_PIPE is None:
        from diffusers import StableVideoDiffusionPipeline
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        dtype = torch.float16 if device == "mps" else torch.float32

        print(f"[LocalI2V] Loading SVD-XT pipeline on {device} ({dtype})...")
        _SVD_PIPE = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
            torch_dtype=dtype,
            cache_dir=str(MODELS_CACHE_DIR)
        )
        _SVD_PIPE.to(device)
        try:
            _SVD_PIPE.enable_attention_slicing()
        except Exception:
            pass

    print(f"[LocalI2V] Generating {num_frames} frames via SVD...")
    generator = torch.manual_seed(int(time.time()))
    frames = _SVD_PIPE(
        img_resized,
        decode_chunk_size=4,
        generator=generator,
        motion_bucket_id=motion_bucket_id,
        noise_aug_strength=0.08,
        num_frames=num_frames
    ).frames[0]

    temp_dir = Path(output_path).parent / f"svd_frames_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        frame_hd = frame.resize((1080, 1920), Image.LANCZOS)
        frame_hd.save(temp_dir / f"frame_{i:04d}.png")

    raw_svd_video = temp_dir / "raw_svd.mp4"
    cmd_encode = [
        FFMPEG_BIN, "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(raw_svd_video)
    ]
    subprocess.run(cmd_encode, capture_output=True, check=True)

    cmd_smooth = [
        FFMPEG_BIN, "-y",
        "-stream_loop", "-1",
        "-i", str(raw_svd_video),
        "-t", str(duration),
        "-vf", "minterpolate='mi_mode=blend:fps=30'",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd_smooth, capture_output=True, check=True)

    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return output_path

def generate_animated_scene_video(
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
    mode: str = "3d_motion"
) -> str:
    """
    Main entry point: Generates a real moving video from a still image and merges with speech audio.
    mode: '3d_motion' (instant 3D parallax) or 'svd' (AI diffusion).
    """
    temp_video = Path(output_path).parent / f"anim_temp_{int(time.time() * 1000)}.mp4"

    if mode == "svd":
        try:
            generate_svd_diffusion_video(image_path, str(temp_video), duration=duration)
        except Exception as e:
            print(f"[LocalI2V] SVD diffusion fallback to 3D motion: {e}")
            generate_3d_parallax_video(image_path, str(temp_video), duration=duration)
    else:
        generate_3d_parallax_video(image_path, str(temp_video), duration=duration)

    # Merge animated video with the scene audio
    cmd_merge = [
        FFMPEG_BIN, "-y",
        "-i", str(temp_video),
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]
    subprocess.run(cmd_merge, capture_output=True, check=True)

    try:
        temp_video.unlink()
    except Exception:
        pass

    return output_path
