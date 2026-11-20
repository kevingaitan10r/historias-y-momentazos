"""Cloud Video Generation Client for ComfyUI (LTX-Video) and Fal.ai (Flux & LTX)."""
import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

def get_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def is_cloud_configured() -> Dict[str, Any]:
    cfg = get_config()
    comfy_url = cfg.get("comfyui_endpoint", "").strip()
    fal_key = cfg.get("fal_api_key", "").strip()
    return {
        "has_comfyui": bool(comfy_url),
        "comfyui_endpoint": comfy_url,
        "has_fal": bool(fal_key),
        "provider": "comfyui" if comfy_url else ("fal" if fal_key else "local")
    }

def test_comfyui_connection(endpoint_url: str) -> dict:
    endpoint_url = endpoint_url.strip().rstrip("/")
    if not endpoint_url:
        return {"ok": False, "message": "La URL no puede estar vacía."}
    try:
        req = urllib.request.Request(f"{endpoint_url}/system_stats", headers={"User-Agent": "HistoriasMomentazos/1.0"})
        with urllib.request.urlopen(req, timeout=8) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                gpu_name = "GPU Activa"
                try:
                    devices = data.get("devices", [])
                    if devices:
                        gpu_name = devices[0].get("name", gpu_name)
                except Exception:
                    pass
                return {"ok": True, "message": f"¡Conectado a ComfyUI con éxito ({gpu_name})!", "data": data}
    except Exception as e:
        return {"ok": False, "message": f"No se pudo conectar a ComfyUI: {str(e)}"}

def generate_video_ltx_cloud(prompt: str, image_path: Optional[str], output_path: str, duration_sec: int = 5) -> bool:
    """Attempts to generate animated video clip using configured cloud provider."""
    cfg = get_config()
    comfy_url = cfg.get("comfyui_endpoint", "").strip().rstrip("/")
    fal_key = cfg.get("fal_api_key", "").strip()

    # 1. Try Fal.ai if key is set
    if fal_key:
        try:
            print(f"[CloudVideo] Calling Fal.ai LTX-Video API for prompt: '{prompt[:40]}...'")
            headers = {
                "Authorization": f"Key {fal_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted, deformed",
                "aspect_ratio": "9:16",
                "duration": duration_sec
            }
            req = urllib.request.Request(
                "https://queue.fal.run/fal-ai/ltx-video",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                video_url = data.get("video", {}).get("url")
                if video_url:
                    urllib.request.urlretrieve(video_url, output_path)
                    print(f"[CloudVideo] Fal.ai video saved: {output_path}")
                    return True
        except Exception as e:
            print(f"[CloudVideo] Fal.ai note: {e}")

    # 2. Try ComfyUI Endpoint if set
    if comfy_url:
        try:
            print(f"[CloudVideo] Sending prompt to ComfyUI Cloud ({comfy_url})...")
            # Minimal LTX Video workflow payload
            prompt_workflow = {
                "3": {
                    "class_type": "LTXVideoSampler",
                    "inputs": {
                        "prompt": prompt,
                        "steps": 20,
                        "cfg": 3.0,
                        "duration": duration_sec
                    }
                }
            }
            req = urllib.request.Request(
                f"{comfy_url}/prompt",
                data=json.dumps({"prompt": prompt_workflow}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                prompt_id = res_data.get("prompt_id")
                if prompt_id:
                    # Poll for completion up to 90 seconds
                    for _ in range(30):
                        time.sleep(3)
                        hist_req = urllib.request.Request(f"{comfy_url}/history/{prompt_id}")
                        with urllib.request.urlopen(hist_req, timeout=10) as h_resp:
                            h_data = json.loads(h_resp.read().decode("utf-8"))
                            if prompt_id in h_data:
                                outputs = h_data[prompt_id].get("outputs", {})
                                for node_out in outputs.values():
                                    vids = node_out.get("videos") or node_out.get("gifs") or []
                                    if vids:
                                        fn = vids[0].get("filename")
                                        view_url = f"{comfy_url}/view?filename={fn}&type=output"
                                        urllib.request.urlretrieve(view_url, output_path)
                                        print(f"[CloudVideo] ComfyUI video downloaded: {output_path}")
                                        return True
        except Exception as e:
            print(f"[CloudVideo] ComfyUI note: {e}")

    return False
