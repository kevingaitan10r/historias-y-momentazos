"""
Viral AI Hook & Title Generator for Gaming / GTA 6 Shorts.
Uses Gemini LLM when configured, or smart context-aware NLP heuristics.
"""

import json
import os
import re
import urllib.request
from typing import Optional


def _generate_hook_gemini(cand_text: str, video_title: str, channel: str, key: str) -> Optional[str]:
    """Uses Gemini to generate an irresistible, viral curiosity-gap hook."""
    models = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    prompt = f"""Eres un estratega experto en viralidad de YouTube Shorts y TikTok (especialista en Gaming y GTA 6).
Analiza el siguiente momento capturado de un directo/video:
- Título del video original: "{video_title}"
- Creador: "{channel}"
- Transcripción del momento exacto del clip:
\"\"\"{cand_text}\"\"\"

Tu misión: Crear un ÚNICO gancho / título para el clip que detenga el scroll al instante en TikTok y Shorts.
REGLAS ESTRICTAS:
1. Longitud: Entre 4 y 7 palabras.
2. Formato: EN MAYÚSCULAS con 1 o 2 emojis llamativos al final.
3. Estilo: Altísimo impacto, intriga o shock (Curiosity Gap). Ejemplo: "¡DESCUBRE EL ESTADIO SECRETO EN GTA 6! 😱", "¡ESTE COCHE ES UNA LOCURA TOTAL! 🏎️💨", "¡NO ME PUEDO CREER LO QUE HIZO! 🔥"
4. NO uses comillas, NO des explicaciones, devuelve ÚNICAMENTE el gancho en una sola línea."""

    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.85,
                    "maxOutputTokens": 60
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                text = text.replace('"', '').replace("'", "").replace("`", "").strip()
                text = text.splitlines()[0].strip()
                if text and len(text) > 4:
                    return text.upper()
        except Exception:
            continue
    return None


def _generate_hook_heuristic(cand_text: str, video_title: str, pick_idx: int = 1) -> str:
    """Fast, context-aware rule engine for generating viral hooks without API keys."""
    text = (cand_text or "").lower()
    title = (video_title or "").lower()
    combined = f"{title} {text}"

    # 0. Aliens / OVNIs / Misterio Paranormal
    if any(k in combined for k in ["alien", "ovni", "extraterrestre", "abducc", "abducen", "nave espacial", "misterio"]):
        options = [
            "¡LOS ALIENS EXISTEN EN GTA 6! 👽🛸",
            "¡ENCONTRÉ UN ALIEN REAL EN GTA 6! 😱👽",
            "¡EL MISTERIO MÁS PERTURBADOR DE GTA 6! 🛸🔥"
        ]
        return options[(pick_idx - 1) % len(options)]

    # Prioritize specific events in the clip's spoken transcript first
    # 1. Tenis / Estadio / Cancha
    if any(k in text for k in ["tenis", "estadio", "court", "cancha", "news open"]) or any(k in title for k in ["tenis", "estadio"]):
        options = [
            "¡DESCUBRE EL ESTADIO SECRETO EN GTA 6! 😱🎾",
            "¡NO ME CREO LO QUE ENCONTRÓ EN GTA 6! 🎾🔥",
            "¡EL SECRETO MEJOR GUARDADO DE LEONIDA! 👀🎮"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 2. Coches / Vehículo tocho / Superdeportivo / Conducir
    if any(k in text for k in ["vehiculo", "vehículo", "tocho", "coche", "carro", "auto", "conducir", "motor", "carreras"]):
        options = [
            "¡EL VEHÍCULO MÁS TOCHO DE GTA 6! 🏎️💨",
            "¡PROBANDO EL COCHE MÁS RÁPIDO DE GTA 6! 🔥⚡",
            "¡ESTE VEHÍCULO ES UNA COMPLETA LOCURA! 🚗💥"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 3. Aeropuerto / Zona restringida
    if any(k in text for k in ["aeropuerto", "pista de aterrizaje", "terminal", "zona prohibida"]):
        options = [
            "¿SE PUEDE ENTRAR AL AEROPUERTO EN GTA 6? ✈️👀",
            "¡INTENTANDO COLARSE AL AEROPUERTO! 🚨🏃",
            "¡ZONA PROHIBIDA EN GTA 6 DESCUBIERTA! 😱🔥"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 4. Caza militar / Avión / Base militar / Hangar
    if any(k in text for k in ["caza", "base militar", "avion", "avión", "volar", "hangar", "fuerza aérea"]) or any(k in title for k in ["caza", "base militar", "militar"]):
        options = [
            "¡ROBANDO EL CAZA EN LA BASE MILITAR! ✈️💥",
            "¡LOGRÓ ENTRAR A LA BASE MILITAR EN GTA 6! 🚨🔥",
            "¡EL VEHÍCULO MÁS PELIGROSO DE GTA 6! ✈️💀"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 5. Policía / Persecución / Sirenas / Estrellas
    if any(k in combined for k in ["polic", "persecu", "sirena", "arrest", "patrulla", "estrellas", "5 estrellas"]):
        options = [
            "¡5 ESTRELLAS DE POLICÍA EN GTA 6! 🚨🚓",
            "¡ESCAPE IMPOSIBLE DE LA POLICÍA! 🏃💨",
            "¡LA PERSECUCIÓN MÁS TENSA DE VICE CITY! 💥🚨"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 6. Dinero / Atraco / Millonario / Recompensa
    if any(k in combined for k in ["dinero", "atraco", "banco", "millon", "millón", "plata", "monedas", "vender"]):
        options = [
            "¡SE HIZO MILLONARIO EN GTA 6! 💰🔥",
            "¡EL TRUCO PARA GANAR MUCHO DINERO! 💸🤑",
            "¡EL ATRACO MÁS GANANCIOSO DE VICE CITY! 💎💥"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 7. Reacción de shock o exclamación en directo
    if any(k in text for k in ["no me lo puedo creer", "no me lo creo", "qué locura", "dios mio", "dios mío", "hermano", "cabrón", "madre mía"]):
        options = [
            "¡NO ME PUEDO CREER LO QUE ACABA DE PASAR! 😱🔥",
            "¡SU REACCIÓN EN VIVO LO DICE TODO! 🤯💥",
            "¡EL MOMENTO MÁS VIRAL DE TODO EL STREAM! ⚡🎮"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 8. Caos / Fail / Explosión / Muerte
    if any(k in combined for k in ["morir", "muerto", "casi", "explot", "bomba", "destrucci"]):
        options = [
            "¡CASI NO LA CUENTA EN GTA 6! 💀🔥",
            "¡EL FINAL MÁS INESPERADO DEL MUNDO! 💥😱",
            "¡TODO SALIÓ MAL EN GTA 6! 😂💀"
        ]
        return options[(pick_idx - 1) % len(options)]

    # 9. Fallback usando el título del video de forma atractiva
    clean_title = re.sub(r"[#|\[\(].*?[\]\)]", "", video_title).strip()
    if clean_title:
        words = clean_title.split()[:5]
        short_title = " ".join(words).upper()
        return f"¡{short_title}! 🔥🎮"

    return f"¡MOMENTO HISTÓRICO EN GTA 6 #{pick_idx}! 😱🔥"


def generate_clip_hook_ai(
    cand_text: str = "",
    video_title: str = "",
    channel: str = "",
    pick_idx: int = 1,
    gemini_key: str = ""
) -> str:
    """
    Main entry point: Generates an irresistible, high-CTR viral hook/title
    based on the candidate moment transcript and video context.
    """
    if gemini_key:
        hook_gemini = _generate_hook_gemini(cand_text, video_title, channel, gemini_key)
        if hook_gemini:
            return hook_gemini

    return _generate_hook_heuristic(cand_text, video_title, pick_idx)
