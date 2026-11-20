"""Viral Video Finder for Top Hispanic Creators (GTA 6 / GTA)."""
import os
import sys
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from common import ytdlp_json, ytdlp_base, run

HISPANIC_CREATORS = [
    {"name": "Todos los Creadores", "query": ""},
    {"name": "DjMaRiiO", "query": "djmariio"},
    {"name": "Willyrex", "query": "willyrex"},
    {"name": "DaniRep", "query": "danirep"},
    {"name": "Vegetta777", "query": "vegetta777"},
    {"name": "AuronPlay", "query": "auronplay"},
    {"name": "Ibai", "query": "ibai"},
    {"name": "IlloJuan", "query": "illojuan"},
    {"name": "TheGrefg", "query": "thegrefg"},
]

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def format_duration(sec: float) -> str:
    if not sec:
        return "0:00"
    m = int(sec // 60)
    s = int(sec % 60)
    h = int(m // 60)
    m = int(m % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def fetch_viral_videos(filter_creator: str = "", sort_by: str = "views", limit: int = 12):
    """
    Finds top videos about GTA 6 (Grand Theft Auto VI) from Hispanic creators.
    Strictly filters out GTA 5 / GTA V.
    sort_by: 'views' (most viewed) or 'velocity' (views per hour)
    """
    creator_part = f"{filter_creator} " if filter_creator else "(willyrex OR djmariio OR danirep OR vegetta777 OR auronplay OR ibai OR illojuan OR thegrefg) "
    query_str = f'("gta 6" OR "gta vi") {creator_part} -"gta 5" -"gta v"'.strip()
    
    # YouTube sort: CAMSAhAB = View Count, CAI%253D = Upload Date
    sort_param = "&sp=CAMSAhAB" if sort_by == "views" else "&sp=CAI%253D"
    search_url = f"https://www.youtube.com/results?search_query={query_str.replace(' ', '+')}{sort_param}"

    try:
        flat = ytdlp_json(search_url, ["--flat-playlist", "--playlist-end", str(max(limit * 3, 35))])
    except Exception as e:
        print(f"[ViralRadar] Error searching: {e}")
        return []

    entries = [e for e in flat.get("entries", []) if e.get("url") and "/shorts/" not in e.get("url", "")]
    
    def get_video_info(item):
        u = item.get("url")
        if not u:
            return None
        try:
            r = run(ytdlp_base() + ["-J", "--skip-download", u], capture=True, check=False)
            if r.returncode == 0 and r.stdout:
                return json.loads(r.stdout)
            return None
        except Exception:
            return None

    # Fetch details in parallel
    with ThreadPoolExecutor(max_workers=6) as ex:
        infos = [i for i in ex.map(get_video_info, entries[:limit + 10]) if i]

    now = time.time()
    results = []
    for i in infos:
        if i.get("is_live"):
            continue

        raw_title = i.get("title", "")
        title_lower = raw_title.lower()

        # Strict GTA 6 verification: must reference GTA 6 / VI, not GTA 5
        has_gta6 = ("gta 6" in title_lower or "gta vi" in title_lower or "gta6" in title_lower or 
                    "grand theft auto vi" in title_lower or "grand theft auto 6" in title_lower)
        is_only_gta5 = ("gta 5" in title_lower or "gta v" in title_lower) and not has_gta6

        if not has_gta6 or is_only_gta5:
            continue

        ts = i.get("timestamp") or i.get("release_timestamp") or (now - 86400)
        age_hours = max(0.5, (now - ts) / 3600)
        views = i.get("view_count") or 0
        v_per_hour = views / age_hours

        # Calculate a Viral Potential Score (1-10)
        score = min(9.9, round(4.0 + (views / 250_000) + (v_per_hour / 15_000), 1))

        results.append({
            "id": i.get("id"),
            "url": i.get("webpage_url") or f"https://www.youtube.com/watch?v={i.get('id')}",
            "title": raw_title,
            "channel": i.get("channel") or i.get("uploader", "Creador"),
            "views": views,
            "views_formatted": format_number(views),
            "views_per_hour": round(v_per_hour),
            "velocity_formatted": f"+{format_number(round(v_per_hour))}/h",
            "duration": i.get("duration", 0),
            "duration_formatted": format_duration(i.get("duration", 0)),
            "thumbnail": i.get("thumbnail") or f"https://i.ytimg.com/vi/{i.get('id')}/hqdefault.jpg",
            "score": score,
            "age_hours": round(age_hours, 1)
        })

    if sort_by == "velocity":
        results.sort(key=lambda x: x["views_per_hour"], reverse=True)
    else:
        results.sort(key=lambda x: x["views"], reverse=True)

    return results[:limit]
