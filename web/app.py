import os
import sys
import json
import time
import uuid
import shutil
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from web.tiktok_uploader import is_logged_in, login_interactive, upload_video, logout_account as tt_logout_account, save_session_from_cookie
from web.youtube_uploader import is_logged_in as is_yt_logged_in, login_interactive as yt_login_interactive, upload_video as yt_upload_video, logout_account as yt_logout_account
from web.viral_radar import fetch_viral_videos, HISPANIC_CREATORS
from web.novel_engine import PRESET_NOVELS, VOICE_OPTIONS, render_novel_video, generate_viral_story_ai, get_saved_gemini_key
from web.ai_hooks import generate_clip_hook_ai

PYTHON_EXE = str(BASE_DIR / ".venv" / "bin" / "python")
ENV_PATH = f"{BASE_DIR / '.venv' / 'bin'}:{os.environ.get('PATH', '')}"

app = FastAPI(title="GTA VI AutoClip Desk & TikTok Suite")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
JOBS_STORE: Dict[str, dict] = {}
DESKTOP_DIR = Path("/Users/kevinfelipegaitanrodiguez/Desktop/GTA6_Clips_DjMaRiiO")
try:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

CONFIG_FILE = BASE_DIR / "web" / "config.json"

class SettingsRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    comfyui_endpoint: Optional[str] = None
    fal_api_key: Optional[str] = None

class JobRequest(BaseModel):
    url: str
    top_clips: int = 3
    max_minutes: int = 15
    layout: str = "blur"  # blur, fill, facecam
    default_hook: str = ""
    export_to_desktop: bool = True

class TikTokUploadRequest(BaseModel):
    clip_path: str
    title: str = ""
    tags: str = "#GTA6 #GTA #Gaming #Clips #Willyrex #DjMaRiiO"
    post_mode: str = "draft"  # draft or post

class TikTokCookieRequest(BaseModel):
    sessionid: str

class YouTubeUploadRequest(BaseModel):
    clip_path: str
    title: str = ""
    description: str = "Momentos épicos de GTA 6 #Shorts #GTA6 #Gaming #ShortsVideo"
    visibility: str = "PUBLIC"  # PUBLIC, UNLISTED, PRIVATE

class NovelGenerateRequest(BaseModel):
    preset: str = "frutinovela_traicion"
    custom_title: Optional[str] = None
    custom_hook: Optional[str] = None
    category: Optional[str] = "frutinovela"
    voice: str = "jorge"
    duration: int = 30
    scenes: Optional[List[dict]] = None
    export_to_desktop: bool = True
    animation_mode: str = "3d_motion"

class StoryIdeaRequest(BaseModel):
    topic: str = ""
    category: str = ""
    duration: int = 30
    gemini_api_key: str = ""
    engine: str = "auto"  # auto, gemini, procedural
    animation_mode: str = "3d_motion"


def run_process_async(job_id: str, req: JobRequest):
    """Executes the pipeline (moments.py + cut.py) in the background and streams status."""
    job = JOBS_STORE[job_id]
    job["status"] = "processing"
    job["step"] = "Descargando y analizando video (moments.py)..."
    job["logs"].append(f"Iniciando análisis para: {req.url}")

    try:
        # Step 1: Run moments.py with smart duration/heatmap handling
        max_min_val = 0 if req.max_minutes in (0, -1) else req.max_minutes
        cmd_moments = [
            PYTHON_EXE,
            str(BASE_DIR / "scripts" / "moments.py"),
            req.url,
            "--top", str(req.top_clips),
            "--max-minutes", str(max_min_val)
        ]
        
        proc = subprocess.Popen(
            cmd_moments,
            cwd=str(BASE_DIR),
            env=dict(os.environ, PATH=ENV_PATH),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        job_dir_path = None
        for line in iter(proc.stdout.readline, ''):
            clean_l = line.strip()
            if clean_l:
                job["logs"].append(clean_l)
                if "job:" in clean_l:
                    job_dir_path = clean_l.split("job:")[-1].strip()
                    job["job_dir"] = job_dir_path

        proc.wait()
        if proc.returncode != 0:
            job["status"] = "failed"
            job["step"] = "Error extrayendo momentos del video."
            return

        if not job_dir_path or not os.path.exists(job_dir_path):
            # Fallback search latest in jobs
            all_jobs = sorted((BASE_DIR / "jobs").glob("*"), key=os.path.getmtime, reverse=True)
            if all_jobs:
                job_dir_path = str(all_jobs[0])
                job["job_dir"] = job_dir_path

        candidates_file = Path(job_dir_path) / "candidates.json"
        if not candidates_file.exists():
            job["status"] = "failed"
            job["step"] = "No se pudieron encontrar candidatos destacados."
            return

        with open(candidates_file, "r", encoding="utf-8") as f:
            candidates_data = json.load(f)

        info = candidates_data.get("info", {})
        video_title = info.get("title", "")
        channel_name = info.get("channel") or info.get("uploader", "")
        candidates = candidates_data.get("candidates", [])
        total_to_cut = min(len(candidates), req.top_clips)
        job["step"] = f"Generando {total_to_cut} clips verticales con ganchos IA (9:16)..."
        job["logs"].append(f"Se detectaron {len(candidates)} momentos virales. Creando títulos y ganchos atractivos con IA...")

        # Step 2: Cut each candidate
        generated_clips = []
        for i, cand in enumerate(candidates[:total_to_cut], 1):
            pick_num = cand["n"]
            cand_text = cand.get("text", "")

            # Generate attractive hook / title using AI (Gemini or Smart NLP)
            if req.default_hook and req.default_hook.strip():
                hook = req.default_hook.strip()
            else:
                hook = generate_clip_hook_ai(
                    cand_text=cand_text,
                    video_title=video_title,
                    channel=channel_name,
                    pick_idx=i,
                    gemini_key=get_saved_gemini_key()
                )

            job["step"] = f"Renderizando clip {i} de {total_to_cut}: '{hook}'..."
            job["logs"].append(f"Gancho IA: '{hook}' (Momento #{pick_num})")
            job["logs"].append(f"Renderizando clip #{pick_num} con layout '{req.layout}'...")

            cmd_cut = [
                PYTHON_EXE,
                str(BASE_DIR / "scripts" / "cut.py"),
                job_dir_path,
                "--pick", str(pick_num),
                "--layout", req.layout,
                "--hook", hook
            ]

            p_cut = subprocess.run(
                cmd_cut,
                cwd=str(BASE_DIR),
                env=dict(os.environ, PATH=ENV_PATH),
                capture_output=True,
                text=True
            )

            clip_mp4 = Path(job_dir_path) / "edits" / f"clip_{pick_num}.mp4"
            if clip_mp4.exists():
                clip_info = {
                    "pick": pick_num,
                    "path": str(clip_mp4),
                    "hook": hook,
                    "score": cand.get("score", 0),
                    "start": cand.get("start", 0),
                    "end": cand.get("end", 0),
                    "filename": clip_mp4.name,
                    "job_dir_name": Path(job_dir_path).name
                }
                
                # Copy to Desktop if requested
                if req.export_to_desktop:
                    dest_file = DESKTOP_DIR / f"{Path(job_dir_path).name}_clip_{pick_num}.mp4"
                    shutil.copy2(clip_mp4, dest_file)
                    clip_info["desktop_path"] = str(dest_file)
                    job["logs"].append(f"Exportado al Escritorio: {dest_file.name}")

                generated_clips.append(clip_info)
            else:
                job["logs"].append(f"Aviso: Falló el recorte del candidato #{pick_num}: {p_cut.stderr[-200:]}")

        job["status"] = "completed"
        job["step"] = f"¡Completado! {len(generated_clips)} clips listos."
        job["clips"] = generated_clips

    except Exception as e:
        job["status"] = "failed"
        job["step"] = f"Error: {str(e)}"
        job["logs"].append(f"Exception: {str(e)}")


async def run_novel_async(job_id: str, req: NovelGenerateRequest):
    """Generates a vertical Frutinovela / Novel clip with TTS and subtitles."""
    job = JOBS_STORE[job_id]
    job["status"] = "processing"
    job["step"] = "Creando imágenes cinematográficas y voz en off con IA..."
    job["logs"].append(f"Iniciando generación de novela: '{req.custom_title or req.preset}'")

    try:
        job["logs"].append(f"Configurando escenas y síntesis de voz (Modo Video: {req.animation_mode})...")
        result = await render_novel_video(
            novel_key=req.preset,
            custom_title=req.custom_title,
            custom_voice=req.voice,
            custom_scenes=req.scenes,
            custom_hook=req.custom_hook,
            category=req.category,
            export_to_desktop=req.export_to_desktop,
            animation_mode=req.animation_mode
        )
        
        clip_info = {
            "pick": 1,
            "path": result["video_path"],
            "hook": result["hook"],
            "score": 99.9,
            "start": 0,
            "end": 35.0,
            "filename": Path(result["video_path"]).name,
            "job_dir_name": result["id"],
            "media_url": result["media_url"]
        }
        if result.get("desktop_path"):
            clip_info["desktop_path"] = result["desktop_path"]
            job["logs"].append(f"Exportado al Escritorio: {Path(result['desktop_path']).name}")

        job["status"] = "completed"
        job["step"] = "¡Novela completada con éxito!"
        job["clips"] = [clip_info]
        job["logs"].append(f"Video vertical 9:16 generado listo para TikTok y YouTube Shorts: {result['id']}")

    except Exception as e:
        job["status"] = "failed"
        job["step"] = f"Error en generación de novela: {str(e)}"
        job["logs"].append(f"Exception: {str(e)}")


@app.get("/")
def get_index():
    index_path = BASE_DIR / "web" / "static" / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/api/status")
def get_system_status():
    ffmpeg_ok = bool(shutil.which("ffmpeg", path=ENV_PATH))
    return {
        "ffmpeg": ffmpeg_ok,
        "tiktok_logged_in": is_logged_in(),
        "youtube_logged_in": is_yt_logged_in(),
        "desktop_folder": str(DESKTOP_DIR),
        "total_jobs": len(JOBS_STORE),
        "active_jobs": sum(1 for j in JOBS_STORE.values() if j["status"] == "processing")
    }


@app.get("/api/jobs")
def list_jobs():
    return list(JOBS_STORE.values())


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return JOBS_STORE[job_id]


@app.post("/api/jobs")
def create_job(req: JobRequest, bg_tasks: BackgroundTasks):
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    JOBS_STORE[job_id] = {
        "id": job_id,
        "url": req.url,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "queued",
        "step": "En cola...",
        "logs": [],
        "clips": [],
        "params": req.dict()
    }
    bg_tasks.add_task(run_process_async, job_id, req)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/settings")
def get_settings():
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "gemini_api_key": cfg.get("gemini_api_key", ""),
        "comfyui_endpoint": cfg.get("comfyui_endpoint", ""),
        "fal_api_key": cfg.get("fal_api_key", ""),
        "desktop_dir": str(DESKTOP_DIR)
    }


@app.post("/api/settings")
def save_settings(req: SettingsRequest):
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    if req.gemini_api_key is not None:
        cfg["gemini_api_key"] = req.gemini_api_key.strip()
    if req.comfyui_endpoint is not None:
        cfg["comfyui_endpoint"] = req.comfyui_endpoint.strip()
    if req.fal_api_key is not None:
        cfg["fal_api_key"] = req.fal_api_key.strip()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return {"status": "success", "message": "Ajustes guardados correctamente."}


@app.post("/api/comfyui/test")
def test_comfy(data: dict):
    from web.cloud_video import test_comfyui_connection
    url = data.get("endpoint", "")
    return test_comfyui_connection(url)


@app.get("/api/clips")
def list_all_clips():
    """Scans and lists all generated clips available across all jobs and Desktop folder with category and upload status."""
    clips = []
    # Scan jobs directory
    for clip_file in sorted((BASE_DIR / "jobs").glob("*/edits/*.mp4"), key=os.path.getmtime, reverse=True):
        job_dir = clip_file.parent.parent
        meta_file = clip_file.with_suffix(".json")
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        is_novel = "novel_" in job_dir.name or "🍓" in meta.get("source_title", "")
        category = meta.get("category", "novel" if is_novel else "gta6")
        dur = meta.get("duration")
        if dur is None:
            dur = round(meta.get("end", 0) - meta.get("start", 0), 1)

        clips.append({
            "id": f"{job_dir.name}_{clip_file.name}",
            "job_id": job_dir.name,
            "filename": clip_file.name,
            "path": str(clip_file),
            "media_url": f"/media/{job_dir.name}/{clip_file.name}",
            "hook": meta.get("hook", clip_file.stem),
            "source_title": meta.get("source_title", job_dir.name),
            "source_channel": meta.get("source_channel", ""),
            "category": category,
            "duration": dur,
            "uploaded_youtube": bool(meta.get("uploaded_youtube", False)),
            "uploaded_youtube_at": meta.get("uploaded_youtube_at", ""),
            "uploaded_tiktok": bool(meta.get("uploaded_tiktok", False)),
            "uploaded_tiktok_at": meta.get("uploaded_tiktok_at", ""),
            "desktop_path": meta.get("desktop_path", ""),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(clip_file)))
        })
    return clips


@app.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: str):
    """Deletes a clip from jobs directory AND deletes corresponding file from Desktop folder."""
    found = False
    deleted_desktop = False
    desktop_path = None

    for clip_file in (BASE_DIR / "jobs").glob("*/edits/*.mp4"):
        job_dir = clip_file.parent.parent
        cid = f"{job_dir.name}_{clip_file.name}"
        if cid == clip_id:
            meta_file = clip_file.with_suffix(".json")
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    desktop_path = meta.get("desktop_path")
                except Exception:
                    pass
                try:
                    meta_file.unlink()
                except Exception:
                    pass

            # Remove MP4
            try:
                clip_file.unlink()
                found = True
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"No se pudo borrar el clip: {e}")

            # Remove from Desktop if tracked
            if desktop_path and Path(desktop_path).exists():
                try:
                    Path(desktop_path).unlink()
                    deleted_desktop = True
                except Exception:
                    pass
            else:
                # Search by clip name or job prefix in DESKTOP_DIR
                try:
                    if DESKTOP_DIR.exists():
                        for df in DESKTOP_DIR.glob("*.mp4"):
                            if (clip_file.stem in df.name) or (job_dir.name[-6:] in df.name):
                                try:
                                    df.unlink()
                                    deleted_desktop = True
                                except Exception:
                                    pass
                except Exception:
                    pass

            # Clean empty job folder if no other clips exist
            try:
                remaining = list(clip_file.parent.glob("*.mp4"))
                if not remaining:
                    shutil.rmtree(job_dir, ignore_errors=True)
                    JOBS_STORE.pop(job_dir.name, None)
            except Exception:
                pass
            break

    if not found:
        raise HTTPException(status_code=404, detail="Clip no encontrado para eliminar.")

    msg = "Clip eliminado correctamente del panel"
    if deleted_desktop:
        msg += " y de la carpeta en el Escritorio."
    else:
        msg += "."
    return {"status": "success", "message": msg}


@app.get("/media/{job_name}/{clip_name}")
def stream_clip(job_name: str, clip_name: str):
    file_path = BASE_DIR / "jobs" / job_name / "edits" / clip_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Clip no encontrado")
    return FileResponse(path=str(file_path), media_type="video/mp4")


@app.post("/api/tiktok/login")
async def trigger_tiktok_login(bg_tasks: BackgroundTasks):
    bg_tasks.add_task(login_interactive)
    return {"status": "started", "message": "Se ha abierto Google Chrome para que inicies sesión en TikTok. Tus credenciales se guardarán localmente."}


@app.post("/api/tiktok/logout")
def trigger_tiktok_logout():
    tt_logout_account()
    return {"status": "ok", "message": "Cuenta de TikTok desconectada correctamente."}


@app.post("/api/tiktok/session-cookie")
def trigger_tiktok_cookie(req: TikTokCookieRequest):
    return save_session_from_cookie(req.sessionid)


@app.post("/api/tiktok/switch-account")
async def trigger_tiktok_switch_account(bg_tasks: BackgroundTasks):
    tt_logout_account()
    bg_tasks.add_task(login_interactive)
    return {"status": "started", "message": "Sesión de TikTok cerrada. Se ha abierto Google Chrome para iniciar sesión con una nueva cuenta."}


@app.post("/api/tiktok/upload")
async def trigger_tiktok_upload(req: TikTokUploadRequest):
    result = await upload_video(
        video_path=req.clip_path,
        title=req.title,
        tags=req.tags,
        post_mode=req.post_mode
    )
    if result.get("status") == "success":
        meta_file = Path(req.clip_path).with_suffix(".json")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["uploaded_tiktok"] = True
                meta["uploaded_tiktok_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"[TikTok] Error updating meta: {e}")
    return result


@app.post("/api/youtube/login")
def trigger_youtube_login():
    """Opens native Google Chrome for safe, unblocked Google login."""
    return yt_login_interactive()


@app.get("/api/youtube/verify")
def trigger_youtube_verify():
    """Quick check for valid YouTube Studio session."""
    return {"logged_in": is_yt_logged_in()}


@app.post("/api/youtube/logout")
def trigger_youtube_logout():
    yt_logout_account()
    return {"status": "ok", "message": "Cuenta de YouTube desconectada correctamente."}


@app.post("/api/youtube/switch-account")
def trigger_youtube_switch_account():
    yt_logout_account()
    return yt_login_interactive()


@app.post("/api/youtube/upload")
async def trigger_youtube_upload(req: YouTubeUploadRequest):
    result = await yt_upload_video(
        video_path=req.clip_path,
        title=req.title,
        description=req.description,
        visibility=req.visibility
    )
    if result.get("status") == "success":
        meta_file = Path(req.clip_path).with_suffix(".json")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["uploaded_youtube"] = True
                meta["uploaded_youtube_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"[YouTube] Error updating meta: {e}")
    return result


@app.get("/api/creators")
def get_creators():
    return HISPANIC_CREATORS


@app.get("/api/trends")
def get_trends(creator: str = "", sort_by: str = "views", limit: int = 12):
    """Returns top viral GTA videos from Hispanic creators."""
    return fetch_viral_videos(filter_creator=creator, sort_by=sort_by, limit=limit)


@app.get("/api/novels/presets")
def get_novel_presets():
    return {
        "presets": PRESET_NOVELS,
        "voices": VOICE_OPTIONS
    }


@app.post("/api/novels/generate")
async def create_novel_job(req: NovelGenerateRequest, bg_tasks: BackgroundTasks):
    job_id = f"job-nov-{uuid.uuid4().hex[:6]}"
    title = req.custom_title or PRESET_NOVELS.get(req.preset, {}).get("title", "Novela Viral IA")
    JOBS_STORE[job_id] = {
        "id": job_id,
        "url": f"🍓 Novela: {title}",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "queued",
        "step": "En cola para renderizar...",
        "logs": [],
        "clips": [],
        "params": req.dict()
    }
    bg_tasks.add_task(run_novel_async, job_id, req)
    return {"job_id": job_id, "status": "queued", "title": title}


@app.post("/api/novels/generate-idea")
def generate_novel_idea(req: StoryIdeaRequest):
    """Uses LLM or Procedural AI to write a viral story script and scenes."""
    story = generate_viral_story_ai(
        topic=req.topic,
        category=req.category,
        duration=req.duration,
        gemini_api_key=req.gemini_api_key,
        engine=req.engine
    )
    return story


@app.post("/api/novels/auto-create")
async def auto_create_novel_video(req: StoryIdeaRequest, bg_tasks: BackgroundTasks):
    """One-click: Generates viral script, scenes, audio, and renders 9:16 video."""
    story = generate_viral_story_ai(
        topic=req.topic,
        category=req.category,
        duration=req.duration,
        gemini_api_key=req.gemini_api_key,
        engine=req.engine
    )
    job_id = f"job-auto-{uuid.uuid4().hex[:6]}"
    title = story["title"]
    engine_name = story.get("engine_used", "IA")
    
    novel_req = NovelGenerateRequest(
        preset="custom",
        custom_title=title,
        custom_hook=story.get("hook"),
        category=req.category or story.get("category", "frutinovela"),
        voice=story.get("voice", "jorge"),
        duration=req.duration,
        scenes=story["scenes"],
        export_to_desktop=True,
        animation_mode=req.animation_mode
    )
    
    JOBS_STORE[job_id] = {
        "id": job_id,
        "url": f"🚀 Auto IA: {title}",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "queued",
        "step": f"Preparando guión generado por {engine_name}...",
        "logs": [f"Idea creada: '{title}'", f"Motor: {engine_name}", f"Gancho: '{story.get('hook', '')}'"],
        "clips": [],
        "params": novel_req.dict()
    }
    bg_tasks.add_task(run_novel_async, job_id, novel_req)
    return {
        "job_id": job_id,
        "status": "queued",
        "title": title,
        "hook": story.get("hook", ""),
        "scenes": story["scenes"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
