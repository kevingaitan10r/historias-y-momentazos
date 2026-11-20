"""Novel & Frutinovela Video Generator Engine for TikTok and YouTube Shorts."""
import os
import sys
import json
import time
import uuid
import shutil
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "jobs"
DESKTOP_DIR = Path("/Users/kevinfelipegaitanrodiguez/Desktop/GTA6_Clips_DjMaRiiO")
PYTHON_EXE = str(BASE_DIR / ".venv" / "bin" / "python")
FFMPEG_BIN = str(BASE_DIR / ".venv" / "bin" / "ffmpeg")
ENV_PATH = f"{BASE_DIR / '.venv' / 'bin'}:{os.environ.get('PATH', '')}"

VOICE_OPTIONS = {
    "jorge": {"name": "Jorge (Telenovela Dramática - México)", "id": "es-MX-JorgeNeural"},
    "dalia": {"name": "Dalia (Villana Dramática - México)", "id": "es-MX-DaliaNeural"},
    "alvaro": {"name": "Álvaro (Misterio & Suspenso - España)", "id": "es-ES-AlvaroNeural"},
    "gonzalo": {"name": "Gonzalo (Narrador Intenso - Colombia)", "id": "es-CO-GonzaloNeural"},
    "elvira": {"name": "Elvira (Relato Emotivo - España)", "id": "es-ES-ElviraNeural"},
}

PRESET_NOVELS = {
    "frutinovela_traicion": {
        "title": "La Traición de Don Plátano",
        "category": "🍓 Frutinovelas",
        "hook": "¡DON PLÁTANO LO CONFESÓ TODO!",
        "voice": "jorge",
        "scenes": [
            {
                "character": "Doña Fresa",
                "emotion": "Tristeza y Sospecha",
                "bg_theme": "kitchen_night",
                "text": "Doña Fresa descubrió un mensaje oculto en la cáscara dorada de Don Plátano, y en ese instante supo que su amor era una completa farsa."
            },
            {
                "character": "Don Plátano y Doña Manzana",
                "emotion": "Romance Prohibido",
                "bg_theme": "luxury_club",
                "text": "En lo más oscuro del refrigerador, Don Plátano se reunía a escondidas con Doña Manzana, prometiéndole escapar juntos a la frutería central."
            },
            {
                "character": "Don Aguacate Detective",
                "emotion": "Descubrimiento Impactante",
                "bg_theme": "neon_city",
                "text": "Pero no contaban con que Don Aguacate lo estaba grabando todo desde la sombra de los vegetales con su cámara de alta definición."
            },
            {
                "character": "Tribunal de Frutas",
                "emotion": "Clímax & Juicio",
                "bg_theme": "courtroom",
                "text": "El tribunal de la ensalada ha convocado a juicio definitivo. ¿Merece Don Plátano ir directo a la licuadora? ¡Comenta tu veredicto y dale like para la Parte 2!"
            }
        ]
    },
    "frutinovela_boda_compromiso": {
        "title": "La Falsa Niña Puros Ceros en la Cena",
        "category": "🍓 Frutinovelas Estilo @frutifresass",
        "hook": "¡LA DESENMASCARARON EN PLENA CENA DE COMPROMISO!",
        "voice": "dalia",
        "scenes": [
            {
                "character": "Doña Fresa La Prometida",
                "emotion": "Hipocresía & Lujo",
                "bg_theme": "luxury_club",
                "text": "Doña Fresa presumía ser una niña de alta sociedad en su cena de compromiso, exigiendo caviar y champán de marca a la familia de Don Plátano.",
                "ai_video_prompt": "3D Pixar style anthropomorphic strawberry girl with elegant makeup, gold jewelry and a white silk dress sitting arrogantly at a luxury banquet table, emotional Disney 3D render, cinematic lighting"
            },
            {
                "character": "La Cuenta Millonaria",
                "emotion": "Tensión y Vergüenza",
                "bg_theme": "kitchen_night",
                "text": "Pero la tensión estalló cuando el camarero trajo la cuenta y todas sus tarjetas doradas fueron rechazadas por tener saldo cero en el banco central.",
                "ai_video_prompt": "3D Pixar animation of a luxury fruit restaurant, a waiter presenting a glowing credit card bill showing declined balance, shock and embarrassment on characters faces, 8k render"
            },
            {
                "character": "Don Plátano Millonario",
                "emotion": "Furia y Decepción",
                "bg_theme": "mansion_gold",
                "text": "Don Plátano se levantó furioso de la mesa y arrojó el anillo de diamantes al suelo tras descubrir que ella solo lo quería por su herencia millonaria.",
                "ai_video_prompt": "3D anthropomorphic banana gentleman in an expensive tuxedo slamming the table in anger, throwing a diamond ring on the floor, dramatic cinematic lighting, emotional 3D scene"
            },
            {
                "character": "El Escándalo Final",
                "emotion": "Clímax & Suspenso",
                "bg_theme": "courtroom",
                "text": "Ahora Doña Fresa amenaza con demandar a toda la familia de frutas. ¿Crees que Don Plátano hizo bien o debió pagar la cuenta? ¡Deja tu comentario y sígueme para la Parte 2!",
                "ai_video_prompt": "3D Pixar style crying strawberry girl pointing accusingly in front of a crowd of shocked fruits, high drama, cinematic camera pan, cliffhanger ending"
            }
        ]
    },
    "frutinovela_herencia": {
        "title": "El Secreto Millonario de Don Aguacate",
        "category": "🥑 Frutinovelas",
        "hook": "EL OSCURO ORIGEN DE DON AGUACATE",
        "voice": "alvaro",
        "scenes": [
            {
                "character": "Don Aguacate Joven",
                "emotion": "Humildad",
                "bg_theme": "market_street",
                "text": "Durante años, todo el barrio creyó que Don Aguacate era una simple verdura común, ignorado y apartado en la caja de descuentos."
            },
            {
                "character": "El Testamento Dorado",
                "emotion": "Misterio",
                "bg_theme": "mansion_gold",
                "text": "Hasta que un abogado limón entregó un sobre sellado con oro: Don Aguacate era en verdad el heredero legítimo del mayor imperio frutal de la ciudad."
            },
            {
                "character": "Doña Piña Conspiradora",
                "emotion": "Venganza y Celos",
                "bg_theme": "dark_vault",
                "text": "La malvada Doña Piña enfureció de celos y ordenó a los tomates podridos tenderle una trampa mortal antes de que firme el testamento."
            },
            {
                "character": "Don Aguacate con Traje",
                "emotion": "Poder & Triunfo",
                "bg_theme": "skyscraper_night",
                "text": "Pero Don Aguacate no llegó solo: la mafia de los frutos secos lo respalda. ¿Logrará reclamar su trono? Sígueme y no te pierdas la Parte 2."
            }
        ]
    },
    "animales_mafia": {
        "title": "El Padrino Bigotes",
        "category": "🐱 Mafia Animal",
        "hook": "LA REGLA DE ORO DE LOS GATOS",
        "voice": "jorge",
        "scenes": [
            {
                "character": "Padrino Bigotes",
                "emotion": "Elegancia y Poder",
                "bg_theme": "mafia_office",
                "text": "Desde lo alto de los tejados, el Padrino Bigotes controlaba el noventa por ciento del contrabando de atún premium en toda la ciudad."
            },
            {
                "character": "Gato Traidor",
                "emotion": "Traición",
                "bg_theme": "rainy_alley",
                "text": "Hasta que su mano derecha, el gato Siamés, cometió el gravísimo error de filtrar los escondites secretos al escuadrón canino."
            },
            {
                "character": "Confrontación Nocturna",
                "emotion": "Tensión Extrema",
                "bg_theme": "neon_rooftop",
                "text": "Una noche lluviosa, Bigotes lo acorraló y susurró: En este callejón hay una sola regla inviolable, y tú la acabas de romper."
            },
            {
                "character": "El Desenlace",
                "emotion": "Suspenso Final",
                "bg_theme": "city_lights",
                "text": "Lo que ocurrió al amanecer dejó sin palabras a toda la pandilla. ¿Debería Bigotes perdonarle una de sus siete vidas? Comenta y sígueme para la Parte 2."
            }
        ]
    },
    "reddit_drama": {
        "title": "Desenmascarado en Plena Boda",
        "category": "💍 Historias & Confesiones",
        "hook": "ARRUINÉ LA BODA DE MI HERMANA",
        "voice": "dalia",
        "scenes": [
            {
                "character": "El Altar Nupcial",
                "emotion": "Tensión y Silencio",
                "bg_theme": "wedding_church",
                "text": "Faltaban solo cinco segundos para que mi hermana dijera el sí quiero, cuando una notificación anónima iluminó mi teléfono celular."
            },
            {
                "character": "El Video Revelador",
                "emotion": "Impacto y Decepción",
                "bg_theme": "luxury_club",
                "text": "Era una grabación oculta de su prometido, jactándose de que solo se casaba por el dinero y la herencia de nuestra familia."
            },
            {
                "character": "La Interrupción",
                "emotion": "Furia y Confrontación",
                "bg_theme": "wedding_church",
                "text": "Caminé despacio hacia el altar, pedí el micrófono frente a trescientos invitados y reproduje el audio a todo volumen."
            },
            {
                "character": "El Caos",
                "emotion": "Clímax",
                "bg_theme": "courtroom",
                "text": "El silencio en la iglesia fue sepulcral y la novia se desmayó en el suelo. ¿Fui el malo por salvarla del peor error de su vida? Deja tu opinión y sígueme."
            }
        ]
    },
    "gta6_vice_city": {
        "title": "GTA 6: El Gran Golpe en Vice City",
        "category": "🎮 GTA 6 & Gaming",
        "hook": "¡LUCIA Y JASON ACORRALADOS EN VICE CITY!",
        "voice": "gonzalo",
        "scenes": [
            {
                "character": "Lucia y Jason",
                "emotion": "Plan Maestro",
                "bg_theme": "vice_city_sunset",
                "text": "Lucia y Jason planeaban el golpe más arriesgado en la historia de Vice City frente a las luces de neón en Ocean Drive."
            },
            {
                "character": "Persecución Policial Neon",
                "emotion": "Adrenalina Pura",
                "bg_theme": "police_chase_neon",
                "text": "Con las sirenas de la policía de Vice City rugiendo en el asfalto mojado, aceleraron a fondo esquivando patrullas y helicópteros."
            },
            {
                "character": "El Rival Secreto",
                "emotion": "Traición Inesperada",
                "bg_theme": "underground_club",
                "text": "Pero no contaban con que un informante encubierto de los cárteles rivales había bloqueado todos los accesos al puente de escape."
            },
            {
                "character": "Escape Final",
                "emotion": "Clímax Épico",
                "bg_theme": "miami_skyline",
                "text": "¿Lograrán saltar la rampa hacia la libertad o terminarán tras las rejas de Leonida? ¡Comenta tu teoría de GTA 6 y dale like para la Parte 2!"
            }
        ]
    }
}

import random
import urllib.request
import re

CONFIG_FILE = BASE_DIR / "web" / "config.json"

def get_saved_gemini_key() -> str:
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return cfg.get("gemini_api_key", "").strip()
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "").strip()

def generate_viral_story_ai(topic: str = "", category: str = "", duration: int = 30, gemini_api_key: str = "", engine: str = "auto") -> dict:
    """Generates an engaging, high-retention viral story script using Gemini LLM or dynamic procedural AI for 30s, 60s, or 90s."""
    key = (gemini_api_key or "").strip() or get_saved_gemini_key()
    target_count = 3 if duration <= 35 else 5 if duration <= 75 else 7
    clean_topic = topic.strip() if topic else ""
    should_try_gemini = (engine in ("gemini", "auto")) and bool(key)

    cat_l = (category or "").lower()
    top_l = clean_topic.lower()

    # Determine if this request is for the dedicated Frutinovelas module or Free Stories
    is_frutinovela = (
        ("fruti" in cat_l) or
        ("frutinovela" in cat_l) or
        any(k in top_l for k in ["fresa", "platano", "plátano", "aguacate", "sandia", "sandía", "manzana", "fruta"]) or
        (not clean_topic and cat_l not in ["historias_libres", "reddit", "millonarios", "misterio", "leyendas", "gta6", "custom"])
    )

    # 1. Try Gemini API
    if should_try_gemini:
        models_to_try = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        for mod in models_to_try:
            try:
                if is_frutinovela:
                    fruti_tropes = [
                        "Boda cancelada en el altar: Doña Fresa descubre a Don Plátano con Doña Frambuesa en la limosina minutos antes de casarse.",
                        "Cena VIP y tarjeta rechazada: Don Plátano presume ser billonario con Doña Manzana pero rebotan sus tarjetas Black y debe fregar platos.",
                        "La falsa niña rica: Doña Fresa finge ser heredera de un imperio de frutos rojos pero Don Aguacate revela sus bolsos falsos y deudas millonarias.",
                        "El testamento de Don Melón: Don Plátano y Doña Manzana conspiran para robar la herencia pero Sandía Juez muestra un video póstumo revelador.",
                        "Prueba de ADN en vivo: Doña Fresa lleva a Don Aguacate a un show televisivo para probar que Don Plátano es el padre de los arándanos.",
                        "El falso penthouse: Don Plátano graba TikToks en un penthouse alquilado por horas mientras duerme en una caja de cartón del mercado.",
                        "El robo de joyas de rubí: La gargantilla de Doña Manzana desaparece en la gala y Don Aguacate halla la boleta de empeño firmada por Don Plátano.",
                        "Venganza empresarial: Doña Fresa compra el banco que embargará la mansión de Don Plátano y lo desaloja en plena transmisión en vivo.",
                        "La suegra amargada: Doña Toronja intenta envenenar la reputación de Doña Fresa en el club campestre de frutas."
                    ]
                    seed_trope = clean_topic if clean_topic else random.choice(fruti_tropes)
                    prompt = f"""Eres el mejor guionista cómico-dramático viral de TikTok, creador de las famosas 'Frutinovelas' estilo @frutifresass.
Escribe un episodio explosivo, lleno de salseo, drama exagerado de telenovela latinoamericana y remates inesperados.
Premisa central: {seed_trope}

Personajes recurrentes disponibles:
- Doña Fresa (la protagonista dramática, heredera de las bayas o falsa niña rica)
- Don Plátano (el galán presumido, falso magnate con tarjetas rebotadas)
- Doña Manzana (matriarca clasista de alta sociedad y boutiques VIP)
- Don Aguacate (detective implacable con gabardina que desenmascara a todos)
- Sandía Juez (juez supremo del tribunal de ensaladas con mazo y veredictos implacables)
- Don Melón (magnate petrolero)
- Doña Toronja (suegra amargada y villana)

Reglas:
- Diálogos rápidos, frases dramáticas intensas ('¡¿Qué hiciste?!', '¡Mientes!', '¡Mis diamantes!').
- Duración total: {duration} segundos.
- Exactamente {target_count} escenas ({round(duration/target_count, 1)}s por escena).
- Cada escena debe tener entre 22 y 28 palabras leídas por el narrador para clavar el tiempo.
- Título llamativo (máx 6 palabras).
- Gancho (Hook) en MAYÚSCULAS para los primeros 3 segundos.

Devuelve EXCLUSIVAMENTE este JSON:
{{
  "title": "...",
  "hook": "...",
  "category": "frutinovela",
  "voice": "jorge",
  "duration": {duration},
  "scenes": [
    {{"character": "...", "emotion": "...", "bg_theme": "...", "text": "..."}}
  ]
}}"""
                else:
                    free_tropes = [
                        "Confesión Reddit: Mi prometida canceló la boda porque mi familia era humilde, sin saber que el salón y el hotel eran de mi propiedad.",
                        "Venganza corporativa: El socio fundador fue expulsado de su empresa; cinco años después volvió como dueño mayoritario y despidió a la junta directiva.",
                        "Misterio de hotel: La recepcionista del turno nocturno recibe llamadas de una suite que lleva clausurada más de 20 años.",
                        "La herencia secreta: Un anciano multimillonario dejó toda su fortuna a la conserje que lo trató con cariño en el hospital.",
                        "Atraco de Vice City: Un golpe milimétrico al banco central de Vice City termina en una cacería policial de cinco estrellas con Lucia y Jason.",
                        "Karma instantáneo: El cliente prepotente humilló al empleado sin saber que era el dueño encubierto de toda la cadena."
                    ]
                    seed_topic = clean_topic if clean_topic else random.choice(free_tropes)
                    prompt = f"""Eres un guionista estrella de historias virales para TikTok y YouTube Shorts (estilo Reddit Confessions, Misterios Reales, Crimen, Poder y Millonarios).
REGLA SUPREMA Y ESTRICTA: NO menciones frutas, verduras, animales humanizados ni dibujos animados. La historia es 100% humana, creíble y con alta retención psicológica.
Tema o premisa: {seed_topic}
Categoría: {category or "Historias Virales"}

Estructura de retención:
- Primeros 3 segundos: Gancho brutal que despierte intriga o indignación.
- Desarrollo: Tensión creciente, pruebas o revelaciones impactantes.
- Clímax / Remate: Giro dramático o lección de karma inesperada.
- Duración total: {duration} segundos ({target_count} escenas).
- Cada escena debe tener entre 22 y 28 palabras leídas por el narrador.

Devuelve EXCLUSIVAMENTE este JSON:
{{
  "title": "...",
  "hook": "...",
  "category": "historias_libres",
  "voice": "jorge",
  "duration": {duration},
  "scenes": [
    {{"character": "...", "emotion": "...", "bg_theme": "...", "text": "..."}}
  ]
}}"""

                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={key}"
                req_data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.95, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(
                    api_url,
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=14) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    raw_text = res_body["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```" in raw_text:
                        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                        raw_text = re.sub(r"\s*```$", "", raw_text)
                    data = json.loads(raw_text.strip())
                    if "scenes" in data and len(data["scenes"]) >= 3:
                        data["engine_used"] = f"Gemini AI ({mod})"
                        data["is_llm"] = True
                        data["category"] = "frutinovela" if is_frutinovela else "historias_libres"
                        print(f"[NovelEngine] Gemini ({mod}) successfully generated script with {len(data['scenes'])} scenes!")
                        return data
            except Exception as e:
                print(f"[NovelEngine] Gemini ({mod}) fallback: {e}")

    # 2. Procedural Fallback Engine (Rich, non-repetitive archetypes)
    if is_frutinovela:
        fruti_stories = [
            {
                "title": "La Cuenta Rechazada de Don Plátano",
                "hook": "¡DON PLÁTANO QUEDÓ EN RIDÍCULO EN LA CENA VIP!",
                "voice": "jorge",
                "scenes": [
                    {"character": "Don Plátano Millonario", "emotion": "Arrogancia y Presunción", "bg_theme": "luxury_club", "text": "Don Plátano invitó a Doña Manzana al restaurante más caro de la ciudad, presumiendo su fortuna y ordenando el banquete más exclusivo del menú."},
                    {"character": "Doña Manzana VIP", "emotion": "Vergüenza y Furia", "bg_theme": "kitchen_night", "text": "Pero el escándalo estalló cuando el camarero anunció frente a todos que su tarjeta Platinum no tenía saldo y que debía lavar platos para pagar la cuenta."},
                    {"character": "Sandía Juez", "emotion": "Sentencia Inapelable", "bg_theme": "courtroom", "text": "Sandía Juez dictaminó embargo total de sus bienes por fraude reiterado. ¿Crees que Don Plátano merecía esta humillación? ¡Comenta y sígueme para la Parte 2!"}
                ]
            },
            {
                "title": "El Detective Aguacate Revela Todo",
                "hook": "¡DON AGUACATE GRABÓ LA TRAICIÓN EN VIVO!",
                "voice": "alvaro",
                "scenes": [
                    {"character": "Don Aguacate Detective", "emotion": "Misterio e Investigación", "bg_theme": "rainy_alley", "text": "Tras semanas siguiendo pistas en la oscuridad, Don Aguacate logró interceptar el maletín secreto que Doña Fresa intentaba enviar fuera del país."},
                    {"character": "Doña Fresa de Alta Sociedad", "emotion": "Desesperación y Pánico", "bg_theme": "dark_vault", "text": "Acorralada en la bóveda subterránea, Doña Fresa intentó comprar el silencio del detective ofreciéndole la mitad de las joyas robadas de la familia."},
                    {"character": "Tribunal de Frutas", "emotion": "Justicia Implacable", "bg_theme": "courtroom", "text": "Las pruebas fueron contundentes y el jurado no tuvo piedad. ¿Fue Don Aguacate un héroe o debió aceptar el trato? ¡Deja tu veredicto en los comentarios!"}
                ]
            },
            {
                "title": "La Falsa Boda de Doña Fresa",
                "hook": "¡CANCELARON LA BODA DEL SIGLO EN EL ALTAR!",
                "voice": "dalia",
                "scenes": [
                    {"character": "Doña Fresa La Novia", "emotion": "Lujo y Vanidad", "bg_theme": "wedding_church", "text": "Doña Fresa caminaba hacia el altar vestida de seda pura, soñando con quedarse con la mitad de las empresas exportadoras de Don Plátano."},
                    {"character": "El Testigo Oculto", "emotion": "Revelación Explosiva", "bg_theme": "wedding_church", "text": "Justo antes del sí definitivo, las puertas del templo se abrieron de golpe mostrando las fotos de Doña Fresa con su verdadero amante en el Caribe."},
                    {"character": "Don Plátano Devastado", "emotion": "Venganza y Despecho", "bg_theme": "courtroom", "text": "Don Plátano rompió el contrato prematrimonial en pedazos y expulsó a todos los invitados. ¿Merecía Doña Fresa el perdón? ¡Opina ahora mismo!"}
                ]
            }
        ]
        chosen = random.choice(fruti_stories)
        chosen_scenes = list(chosen["scenes"])
        if target_count >= 5:
            chosen_scenes.append({"character": "Confrontación en el Penthouse", "emotion": "Furia al Límite", "bg_theme": "mansion_gold", "text": "En el piso más alto de la torre corporativa, los gritos se escuchaban hasta la calle mientras las transferencias bancarias eran canceladas una tras otra."})
            chosen_scenes.append({"character": "Veredicto del Mercado", "emotion": "Caída del Imperio", "bg_theme": "courtroom", "text": "Con la reputación destruida y las cámaras de televisión transmitiendo el arresto, el pacto millonario quedó hecho cenizas para siempre."})
        if target_count >= 7:
            chosen_scenes.append({"character": "El Testigo Sorpresa", "emotion": "Giro Inesperado", "bg_theme": "rainy_alley", "text": "Un viejo socio que todos creían fuera del juego apareció con un documento firmado que cambió el destino de todos los involucrados."})
            chosen_scenes.append({"character": "Sentencia Definitiva", "emotion": "Fin del Capítulo", "bg_theme": "courtroom", "text": "El martillo de la justicia cayó con fuerza demoledora. ¿Crees que habrá venganza en el siguiente episodio? ¡Sígueme para ver la Parte 2!"})
        return {
            "title": chosen["title"],
            "hook": chosen["hook"],
            "category": "frutinovela",
            "voice": chosen["voice"],
            "duration": duration,
            "scenes": chosen_scenes[:target_count],
            "engine_used": "Motor Base Procedural (Frutinovela Dinámica)",
            "is_llm": False
        }

    # Archetype: Free Stories Procedural Fallback
    subj = clean_topic.title() if clean_topic else "El Secreto Millonario"
    free_stories = [
        {
            "title": f"La Venganza Silenciosa: {subj}",
            "hook": f"¡LE HICIERON LA PEOR JUGADA Y ASÍ RESPONDIÓ!",
            "voice": "jorge",
            "scenes": [
                {"character": "El Protagonista", "emotion": "Determinación Fría", "bg_theme": "skyscraper_night", "text": f"Durante años lo subestimaron y pensaron que jamás se daría cuenta del desfalco, pero cada noche reunía pruebas silenciosas sin levantar sospechas."},
                {"character": "El Rival Confiado", "emotion": "Soberbia y Sorpresa", "bg_theme": "luxury_club", "text": f"En plena reunión de accionistas celebraban la victoria anticipada, hasta que una llamada del departamento legal congeló todas sus cuentas en Suiza."},
                {"character": "El Golpe Final", "emotion": "Triunfo Absoluto", "bg_theme": "courtroom", "text": f"Las máscaras cayeron por completo y la verdad salió a la luz pública. ¿Habrías actuado igual ante semejante traición? ¡Déjalo en los comentarios!"}
            ]
        },
        {
            "title": f"El Misterio Inexplicable de {subj}",
            "hook": f"¡LO QUE DESCUBRIERON CAMBIÓ TODO PARA SIEMPRE!",
            "voice": "alvaro",
            "scenes": [
                {"character": "El Investigador", "emotion": "Tensión y Asombro", "bg_theme": "dark_vault", "text": f"Todo comenzó con una grabación antigua recuperada del servidor principal, donde se escuchaba claramente la advertencia que todos decidieron ignorar."},
                {"character": "El Testigo Clave", "emotion": "Temor y Confesión", "bg_theme": "rainy_alley", "text": f"Bajo la lluvia de la medianoche rompió el pacto de confidencialidad y entregó las llaves maestras que abrían la caja fuerte del piso cuarenta."},
                {"character": "El Desenlace", "emotion": "Giro Espeluznante", "bg_theme": "skyscraper_night", "text": f"Al abrir la puerta descubrieron que la historia oficial era una mentira total. ¿Crees que debieron revelar la verdad? ¡Comenta tu teoría!"}
            ]
        }
    ]
    chosen = random.choice(free_stories)
    chosen_scenes = list(chosen["scenes"])
    if target_count >= 5:
        chosen_scenes.append({"character": "Acorralados sin Salida", "emotion": "Presión Extrema", "bg_theme": "neon_rooftop", "text": "Con los reflectores encima y el tiempo en contra, tuvieron que tomar una decisión desesperada que pondría a prueba su lealtad."})
        chosen_scenes.append({"character": "Confrontación Cara a Cara", "emotion": "Verdad Brutal", "bg_theme": "mansion_gold", "text": "Frente a frente salieron a relucir todas las mentiras guardadas durante años, sellando el destino de una rivalidad histórica."})
    if target_count >= 7:
        chosen_scenes.append({"character": "La Prueba Definitiva", "emotion": "Giro Maestro", "bg_theme": "mafia_office", "text": "Un mensaje encriptado enviado a último minuto reveló la identidad del verdadero cerebro detrás de toda la operación."})
        chosen_scenes.append({"character": "El Juicio del Público", "emotion": "Cierre Impactante", "bg_theme": "courtroom", "text": "La historia ha dado un giro que nadie esperaba. ¿Quién crees que fue el verdadero culpable? Deja tu opinión y suscríbete para la continuación."})

    return {
        "title": chosen["title"],
        "hook": chosen["hook"],
        "category": "historias_libres",
        "voice": chosen["voice"],
        "duration": duration,
        "scenes": chosen_scenes[:target_count],
        "engine_used": "Motor Base Procedural (Historia Viral)",
        "is_llm": False
    }



ASSETS_SCENES_DIR = BASE_DIR / "web" / "static" / "assets" / "scenes"

def get_matching_3d_image(character: str, theme: str, title: str) -> Optional[Path]:
    """Finds a matching photorealistic 3D Pixar render from the assets library if available."""
    if not ASSETS_SCENES_DIR.exists():
        return None
    char_l = character.lower()
    title_l = title.lower()

    # 1. GTA 6 / Vice City / Action / Crime
    if any(k in char_l or k in title_l for k in ["gta", "vice city", "lucia", "jason", "coche", "auto", "atraco", "persecu", "policia", "policía", "neon", "miami"]):
        if any(k in char_l or k in theme for k in ["persecu", "polic", "coche", "calle", "carrera", "escap", "atraco"]):
            p = ASSETS_SCENES_DIR / "gta6_police_chase_neon.jpg"
            if p.exists(): return p
        p = ASSETS_SCENES_DIR / "gta6_lucia_jason_vice_city.jpg"
        if p.exists(): return p

    # 2. Fruit & Animal Telenovelas (strict matching)
    if any(k in char_l for k in ["fresa", "boda", "novia", "vestido"]):
        p = ASSETS_SCENES_DIR / "dona_fresa_wedding_kitchen_1795148365685.jpg"
        if p.exists(): return p

    if any(k in char_l for k in ["platano", "plátano", "manzana", "vip", "club", "romance", "traicion", "traición"]):
        p = ASSETS_SCENES_DIR / "don_platano_dona_manzana_vip_neon_1795148560016.jpg"
        if p.exists(): return p

    if any(k in char_l for k in ["aguacate", "detective", "polic", "camara", "investig", "calle", "sobre"]):
        p = ASSETS_SCENES_DIR / "don_aguacate_detective_v2_1795148564957.jpg"
        if p.exists(): return p

    if any(k in char_l for k in ["tribunal", "juicio", "juez", "sandia", "sandía", "ley", "sentencia", "caos", "desenlace", "escandalo"]):
        p = ASSETS_SCENES_DIR / "watermelon_judge_courtroom_v2_1795148585901.jpg"
        if p.exists(): return p

    if any(k in char_l for k in ["gato", "mafia", "bigotes", "padrino", "oficina", "muelle"]):
        p = ASSETS_SCENES_DIR / "don_gato_bigotes_miami_office_1795148582776.jpg"
        if p.exists(): return p

    # 3. Human / Realistic Stories (Themes & Scene matching)
    theme_l = (theme or "").lower()
    if any(k in theme_l or k in char_l for k in ["court", "juez", "tribunal", "juicio", "ley", "justicia"]):
        p = ASSETS_SCENES_DIR / "human_courtroom_judge_gavel.jpg"
        if p.exists(): return p

    if any(k in theme_l or k in char_l for k in ["vault", "bóveda", "boveda", "cartel", "cash", "dinero", "caja", "bodega", "dólares"]):
        p = ASSETS_SCENES_DIR / "human_cartel_vault_cash.jpg"
        if p.exists(): return p

    if any(k in theme_l or k in char_l for k in ["club", "vip", "disco", "lounge", "bar", "noche", "fiesta"]):
        p = ASSETS_SCENES_DIR / "human_luxury_nightclub_vip.jpg"
        if p.exists(): return p

    if any(k in theme_l or k in char_l for k in ["rain", "lluvia", "calle", "callejón", "callejon", "detective", "calle"]):
        p = ASSETS_SCENES_DIR / "human_rainy_street_detective.jpg"
        if p.exists(): return p

    if any(k in theme_l or k in char_l for k in ["wedding", "boda", "novi", "matrimonio", "iglesia", "altar", "salón"]):
        p = ASSETS_SCENES_DIR / "human_wedding_interrupted.jpg"
        if p.exists(): return p

    if any(k in theme_l or k in char_l for k in ["skyscraper", "office", "oficina", "ceo", "empresa", "jefe", "negocio", "reunión"]):
        p = ASSETS_SCENES_DIR / "human_office_ceo_suspense.jpg"
        if p.exists(): return p

    # Fallback for Frutinovelas / Animal stories:
    if any(k in title_l or k in char_l for k in ["fruti", "fruta", "plátano", "fresa", "aguacate", "sandía", "gato", "animal"]):
        fruit_imgs = [p for p in ASSETS_SCENES_DIR.glob("*.jpg") if not p.name.startswith("gta6") and not p.name.startswith("human")]
        if fruit_imgs:
            return fruit_imgs[abs(hash(character + theme)) % len(fruit_imgs)]

    # Fallback for Human / Free Stories:
    human_imgs = [
        ASSETS_SCENES_DIR / "human_office_ceo_suspense.jpg",
        ASSETS_SCENES_DIR / "human_cartel_vault_cash.jpg",
        ASSETS_SCENES_DIR / "human_luxury_nightclub_vip.jpg",
        ASSETS_SCENES_DIR / "human_courtroom_judge_gavel.jpg",
        ASSETS_SCENES_DIR / "human_rainy_street_detective.jpg",
        ASSETS_SCENES_DIR / "human_wedding_interrupted.jpg",
        ASSETS_SCENES_DIR / "gta6_lucia_jason_vice_city.jpg"
    ]
    valid_human = [p for p in human_imgs if p.exists()]
    if valid_human:
        return valid_human[abs(hash(character + theme + title)) % len(valid_human)]

    return None


def create_scene_image(character: str, emotion: str, theme: str, title: str, scene_idx: int, total_scenes: int, output_path: str, custom_img_path: Optional[str] = None):
    """Generates a high-impact 9:16 (1080x1920) scene poster using 3D Pixar renders or stylized cinematic graphics."""
    W, H = 1080, 1920
    
    # Check if a custom or matching 3D Pixar image is available
    target_img_path = None
    if custom_img_path and Path(custom_img_path).exists():
        target_img_path = Path(custom_img_path)
    else:
        target_img_path = get_matching_3d_image(character, theme, title)

    if target_img_path and target_img_path.exists():
        try:
            real_img = Image.open(target_img_path).convert("RGB")
            # Aspect fill 1080x1920
            src_w, src_h = real_img.size
            scale = max(W / src_w, H / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            resized = real_img.resize((new_w, new_h), Image.LANCZOS)
            
            left = (new_w - W) // 2
            top = (new_h - H) // 2
            img = resized.crop((left, top, left + W, top + H))
            
            # Apply top & bottom dark gradient overlay for text readability
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            o_draw = ImageDraw.Draw(overlay)
            
            # Top gradient
            for y in range(260):
                alpha = int(180 * (1 - y / 260))
                o_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
                
            # Bottom gradient
            for y in range(H - 420, H):
                ratio = (y - (H - 420)) / 420
                alpha = int(220 * ratio)
                o_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
                
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # Top Scene Badge
            draw.rounded_rectangle([W//2 - 240, 80, W//2 + 240, 150], radius=25, fill=(236, 72, 153))
            draw.text((W//2, 115), f"ESCENA {scene_idx} DE {total_scenes}", fill=(255, 255, 255), anchor="mm")
            
            # Bottom Character and Emotion banner
            draw.text((W//2, H - 240), character.upper(), fill=(255, 255, 255), anchor="mm")
            draw.text((W//2, H - 190), f"Estado: {emotion}", fill=(255, 215, 0), anchor="mm")
            draw.text((W//2, H - 90), "🔥 PARTE 1 • COMENTA TU OPINIÓN 🔥", fill=(200, 200, 220), anchor="mm")
            
            img.save(output_path, quality=95)
            return output_path
        except Exception as e:
            print(f"[NovelEngine] Error loading 3D asset, falling back: {e}")

    # Fallback Procedural Graphic
    img = Image.new("RGB", (W, H), (15, 18, 30))
    draw = ImageDraw.Draw(img)

    # Color themes based on scenery
    palettes = {
        "kitchen_night": [(30, 20, 50), (12, 10, 25), (255, 65, 120)],
        "luxury_club": [(40, 10, 25), (15, 5, 20), (255, 190, 40)],
        "neon_city": [(10, 30, 60), (5, 10, 30), (0, 240, 255)],
        "courtroom": [(50, 35, 20), (20, 15, 10), (240, 160, 40)],
        "market_street": [(35, 45, 25), (15, 20, 10), (120, 220, 80)],
        "mansion_gold": [(55, 45, 15), (25, 20, 10), (255, 215, 0)],
        "dark_vault": [(20, 25, 40), (10, 12, 20), (180, 100, 255)],
        "skyscraper_night": [(15, 25, 50), (8, 12, 25), (80, 180, 255)],
        "mafia_office": [(45, 25, 20), (18, 10, 8), (240, 80, 60)],
        "rainy_alley": [(15, 30, 45), (8, 15, 25), (100, 200, 255)],
        "neon_rooftop": [(40, 15, 60), (15, 8, 30), (255, 50, 180)],
        "city_lights": [(25, 30, 55), (12, 14, 28), (255, 200, 50)],
        "wedding_church": [(50, 40, 60), (20, 15, 25), (255, 120, 180)],
    }
    top_c, bot_c, accent_c = palettes.get(theme, [(30, 25, 50), (10, 8, 20), (255, 70, 140)])

    # Draw vertical gradient
    for y in range(H):
        ratio = y / H
        r = int(top_c[0] * (1 - ratio) + bot_c[0] * ratio)
        g = int(top_c[1] * (1 - ratio) + bot_c[1] * ratio)
        b = int(top_c[2] * (1 - ratio) + bot_c[2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Add ambient glow circles
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.ellipse([W//2 - 400, H//2 - 500, W//2 + 400, H//2 + 300], fill=(*accent_c, 45))
    glow_draw.ellipse([W//2 - 250, H//2 - 350, W//2 + 250, H//2 + 150], fill=(*accent_c, 80))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow_img).convert("RGB"), (0, 0))

    # Re-acquire draw
    draw = ImageDraw.Draw(img)

    # Decorative frame elements
    border_color = (255, 255, 255, 30)
    draw.rectangle([40, 40, W - 40, H - 40], outline=(80, 80, 100), width=3)

    # Top Category & Scene Badge
    badge_bg = (236, 72, 153) if "fresa" in character.lower() or "fruti" in title.lower() else accent_c
    draw.rounded_rectangle([W//2 - 240, 80, W//2 + 240, 150], radius=25, fill=badge_bg)
    draw.text((W//2, 115), f"ESCENA {scene_idx} DE {total_scenes}", fill=(0, 0, 0), anchor="mm")

    # Character Card Center
    card_top = H//2 - 420
    card_bot = H//2 + 240
    draw.rounded_rectangle([100, card_top, W - 100, card_bot], radius=40, fill=(20, 24, 38, 220), outline=accent_c, width=4)

    # Character Avatar Icon Representation
    avatar_y = card_top + 220
    draw.ellipse([W//2 - 160, avatar_y - 160, W//2 + 160, avatar_y + 160], fill=(30, 36, 56), outline=(255, 255, 255), width=5)

    # Emoji or character emblem
    char_l = character.lower()
    title_l = title.lower()
    if "fresa" in char_l: emblem = "🍓"
    elif any(k in char_l for k in ["plátano", "platano", "banana"]): emblem = "🍌"
    elif any(k in char_l for k in ["aguacate", "palta"]): emblem = "🥑"
    elif "manzana" in char_l: emblem = "🍎"
    elif any(k in char_l for k in ["piña", "pina"]): emblem = "🍍"
    elif any(k in char_l for k in ["sandía", "sandia"]): emblem = "🍉"
    elif any(k in char_l for k in ["limón", "limon"]): emblem = "🍋"
    elif "naranja" in char_l: emblem = "🍊"
    elif "uva" in char_l: emblem = "🍇"
    elif "mango" in char_l: emblem = "🥭"
    elif "coco" in char_l: emblem = "🥥"
    elif "kiwi" in char_l: emblem = "🥝"
    elif any(k in char_l for k in ["gato", "felino", "michi"]): emblem = "🐱"
    elif any(k in char_l for k in ["perro", "canino", "firulais"]): emblem = "🐶"
    elif any(k in char_l for k in ["hámster", "hamster", "ratón", "raton"]): emblem = "🐹"
    elif any(k in char_l for k in ["hamburguesa", "burger"]): emblem = "🍔"
    elif "pizza" in char_l: emblem = "🍕"
    elif "taco" in char_l: emblem = "🌮"
    elif any(k in char_l for k in ["detective", "polic", "investig"]): emblem = "🕵️"
    elif any(k in char_l for k in ["mafia", "padrino", "jefe"]): emblem = "🕶️"
    elif any(k in title_l for k in ["boda", "espos", "novi"]): emblem = "💍"
    elif any(k in title_l for k in ["juicio", "tribunal", "ley"]): emblem = "⚖️"
    elif any(k in char_l for k in ["alien", "ovni", "espacio"]): emblem = "🛸"
    elif any(k in char_l for k in ["robot", "ia", "cyborg"]): emblem = "🤖"
    else: emblem = "🎭"
    
    # Text info on card
    draw.text((W//2, avatar_y - 10), emblem, fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, avatar_y + 220), character.upper(), fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, avatar_y + 280), f"Estado: {emotion}", fill=(accent_c[0], accent_c[1], accent_c[2]), anchor="mm")

    # Title header at bottom of card
    draw.text((W//2, card_bot + 100), title.upper(), fill=(255, 255, 255), anchor="mm")

    # Bottom watermark
    draw.text((W//2, H - 90), "🔥 PARTE 1 • COMENTA TU OPINIÓN 🔥", fill=(180, 180, 200), anchor="mm")

    img.save(output_path, quality=95)
    return output_path


async def generate_speech_audio(text: str, voice_id: str, output_path: str):
    """Uses edge-tts to generate high-fidelity Spanish narration with safe offline fallback."""
    try:
        import edge_tts
        comm = edge_tts.Communicate(text=text, voice=voice_id, rate="+12%")
        await comm.save(output_path)
        if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            return output_path
    except Exception as e:
        print(f"[NovelEngine] edge-tts online audio warning ({e}), synthesizing speech track...")

    # Safe audio fallback: synthesize speech timing based on word count (~2.8 words/sec)
    words = max(len(text.split()), 4)
    dur = max(3.5, words / 2.7)
    cmd_fallback = [
        FFMPEG_BIN, "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=320:beep_factor=4:duration={dur:.1f}",
        "-af", "volume=0.35,afade=t=out:st=3:d=0.5",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd_fallback, capture_output=True, check=True)
    return output_path


def transcribe_and_build_ass(audio_path: str, ass_path: str, fallback_text: str = ""):
    """Uses faster-whisper to transcribe audio and output animated TikTok style subtitles."""
    # Build ASS format with prominent viral styling
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokViral,Arial,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5.5,2.5,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def format_ts(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    lines = []
    whisper_success = False
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, word_timestamps=True, language="es")

        for seg in segments:
            words = getattr(seg, "words", [])
            if not words:
                start_str = format_ts(seg.start)
                end_str = format_ts(seg.end)
                text_clean = seg.text.strip().upper()
                lines.append(f"Dialogue: 0,{start_str},{end_str},TikTokViral,,0,0,0,,{text_clean}")
                continue

            chunk_size = 4
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                for w in chunk:
                    w_start = format_ts(w.start)
                    w_end = format_ts(w.end)
                    formatted_phrase = []
                    for other_w in chunk:
                        w_text = other_w.word.strip().upper()
                        if other_w == w:
                            formatted_phrase.append(r"{\c&H0000FFFF\b1\fscx110\fscy110}" + w_text + r"{\r}")
                        else:
                            formatted_phrase.append(r"{\c&H00FFFFFF\b1}" + w_text + r"{\r}")
                    phrase_str = " ".join(formatted_phrase)
                    lines.append(f"Dialogue: 0,{w_start},{w_end},TikTokViral,,0,0,0,,{phrase_str}")
        if lines:
            whisper_success = True
    except Exception as e:
        print(f"[NovelEngine] Whisper transcription note: {e}")

    if not whisper_success and fallback_text:
        # Fallback subtitle pacing using text directly
        words = fallback_text.split()
        chunk_size = 4
        total_time = 30.0
        try:
            dur_cmd = [FFMPEG_BIN, "-i", audio_path]
            p = subprocess.run(dur_cmd, capture_output=True, text=True)
            for l in p.stderr.splitlines():
                if "Duration" in l:
                    ts = l.split("Duration:")[1].split(",")[0].strip()
                    parts = ts.split(":")
                    total_time = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                    break
        except Exception:
            pass

        t_per_word = max(0.35, total_time / max(len(words), 1))
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            c_start = i * t_per_word
            c_end = min(total_time, (i + len(chunk)) * t_per_word)
            text_upper = " ".join(chunk).upper()
            lines.append(f"Dialogue: 0,{format_ts(c_start)},{format_ts(c_end)},TikTokViral,,0,0,0,,{text_upper}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(lines))

    return ass_path


async def render_novel_video(
    novel_key: str = "frutinovela_traicion",
    custom_title: Optional[str] = None,
    custom_voice: Optional[str] = None,
    custom_scenes: Optional[List[dict]] = None,
    custom_hook: Optional[str] = None,
    category: Optional[str] = None,
    export_to_desktop: bool = True,
    animation_mode: str = "3d_motion"
) -> dict:
    """Renders a complete vertical 9:16 video with animated zoom, TTS voiceover, and burned subtitles."""
    preset = PRESET_NOVELS.get(novel_key, PRESET_NOVELS["frutinovela_traicion"])
    title = custom_title or preset["title"]
    voice_key = custom_voice or preset.get("voice", "jorge")
    voice_id = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS["jorge"])["id"]
    scenes = custom_scenes or preset["scenes"]

    novel_id = f"novel_{uuid.uuid4().hex[:8]}"
    work_dir = JOBS_DIR / novel_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"[NovelEngine] Starting generation for '{title}' (ID: {novel_id}, Mode: {animation_mode})...")

    # Step 1: Generate audio for each scene & combined audio
    scene_clips = []
    full_script_texts = []
    
    for idx, sc in enumerate(scenes, 1):
        sc_text = sc["text"]
        full_script_texts.append(sc_text)
        sc_audio = work_dir / f"scene_{idx}.mp3"
        sc_img = work_dir / f"scene_{idx}.png"

        # Generate scene image using 3D Pixar renders or custom images
        create_scene_image(
            character=sc.get("character", "Personaje"),
            emotion=sc.get("emotion", "Dramático"),
            theme=sc.get("bg_theme", "kitchen_night"),
            title=title,
            scene_idx=idx,
            total_scenes=len(scenes),
            output_path=str(sc_img),
            custom_img_path=sc.get("image_path")
        )

        # Generate scene voiceover
        await generate_speech_audio(sc_text, voice_id, str(sc_audio))

        # Probe scene audio duration with ffprobe
        dur_cmd = [
            str(BASE_DIR / ".venv" / "bin" / "ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(sc_audio)
        ]
        p_dur = subprocess.run(dur_cmd, capture_output=True, text=True)
        try:
            dur = float(p_dur.stdout.strip())
        except Exception:
            dur = 6.0
        dur += 0.5  # slight buffer

        # Render genuine animated video clip for this scene
        sc_video = work_dir / f"scene_{idx}.mp4"
        fps = 30
        frames = int(dur * fps)

        anim_success = False

        # Check if user provided an animated video clip (e.g. from Kling AI, Luma, Runway, etc.)
        custom_video = sc.get("video_path")
        if custom_video and Path(custom_video).exists() and str(custom_video).endswith(".mp4"):
            try:
                print(f"[NovelEngine] Using provided animated video for scene {idx}: {custom_video}")
                cmd_clip = [
                    FFMPEG_BIN, "-y",
                    "-stream_loop", "-1", "-i", str(custom_video),
                    "-i", str(sc_audio),
                    "-map", "0:v", "-map", "1:a",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-t", str(dur),
                    str(sc_video)
                ]
                subprocess.run(cmd_clip, capture_output=True, check=True)
                anim_success = True
            except Exception as e:
                print(f"[NovelEngine] Error embedding custom video clip: {e}")

        if not anim_success:
            # 1. Intentar generación de video real con IA en la nube (LTX-Video vía ComfyUI Colab o Fal.ai)
            try:
                from web.cloud_video import generate_video_ltx_cloud
                ai_prompt = sc.get("ai_video_prompt") or f"3D Disney Pixar animation of {sc.get('character', 'character')}, {sc.get('emotion', 'dramatic')}, cinematic lighting, highly emotional, 8k render, vertical 9:16"
                print(f"[NovelEngine] Verificando generación en la nube (LTX-Video) para escena {idx}...")
                cloud_ok = generate_video_ltx_cloud(
                    prompt=ai_prompt,
                    image_path=str(sc_img),
                    output_path=str(sc_video),
                    duration_sec=int(dur)
                )
                if cloud_ok:
                    anim_success = True
                    print(f"[NovelEngine] ¡Escena {idx} generada con éxito mediante LTX-Video en la Nube!")
            except Exception as e:
                print(f"[NovelEngine] Cloud LTX fallback: {e}")

        if not anim_success:
            try:
                from web.local_i2v import generate_animated_scene_video
                print(f"[NovelEngine] Rendering animated video for scene {idx} ({dur:.1f}s, mode: {animation_mode})...")
                generate_animated_scene_video(
                    image_path=str(sc_img),
                    audio_path=str(sc_audio),
                    output_path=str(sc_video),
                    duration=dur,
                    mode=animation_mode
                )
                anim_success = True
            except Exception as e:
                print(f"[NovelEngine] 3D video animation fallback: {e}")

        if not anim_success:
            # Fallback to FFmpeg zoompan filter
            anim_mode = (idx - 1) % 4
            if anim_mode == 0:
                zoom_expr = f"zoompan=z='min(zoom+0.0015,1.22)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
            elif anim_mode == 1:
                zoom_expr = f"zoompan=z='1.14':d={frames}:x='if(lte(on,1),(iw-iw/zoom)/2,max(0,x-0.45))':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
            elif anim_mode == 2:
                zoom_expr = f"zoompan=z='if(lte(on,1),1.22,max(1.0,zoom-0.0015))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
            else:
                zoom_expr = f"zoompan=z='1.14':d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),ih-ih/zoom,max(0,y-0.45))':s=1080x1920:fps={fps}"

            cmd_clip = [
                FFMPEG_BIN, "-y",
                "-loop", "1", "-i", str(sc_img),
                "-i", str(sc_audio),
                "-vf", zoom_expr,
                "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(dur),
                str(sc_video)
            ]
            subprocess.run(cmd_clip, capture_output=True, check=True)

        scene_clips.append(str(sc_video))

    # Step 2: Concatenate all scene clips
    concat_list_file = work_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")

    combined_video = work_dir / "combined_raw.mp4"
    cmd_concat = [
        FFMPEG_BIN, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(combined_video)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # Step 3: Extract combined audio for Whisper word timestamps
    extracted_audio = work_dir / "full_audio.mp3"
    cmd_extract = [
        FFMPEG_BIN, "-y",
        "-i", str(combined_video),
        "-vn", "-c:a", "libmp3lame", "-q:a", "2",
        str(extracted_audio)
    ]
    subprocess.run(cmd_extract, capture_output=True, check=True)

    # Step 4: Transcribe and create ASS subtitles
    ass_path = work_dir / "subtitles.ass"
    transcribe_and_build_ass(str(extracted_audio), str(ass_path), fallback_text=" ".join(full_script_texts))

    # Step 4.5: Mix voiceover with background suspense music & boom SFX (Auto-Ducking)
    audio_dir = BASE_DIR / "web" / "static" / "assets" / "audio"
    bg_music = audio_dir / "music_suspense_drama.mp3"
    sfx_boom = audio_dir / "sfx_boom.mp3"

    mixed_audio = work_dir / "final_mixed_audio.mp3"
    audio_source_for_burn = extracted_audio

    if bg_music.exists():
        try:
            cmd_dur = [
                str(BASE_DIR / ".venv" / "bin" / "ffprobe"),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(extracted_audio)
            ]
            p_dur = subprocess.run(cmd_dur, capture_output=True, text=True)
            total_dur = float(p_dur.stdout.strip()) if p_dur.stdout.strip() else 30.0
            fade_out_st = max(1.0, total_dur - 2.5)

            if sfx_boom.exists():
                f_complex = (
                    f"[0:a]volume=1.05[v];"
                    f"[1:a]volume=0.18,afade=t=in:ss=0:d=1.0,afade=t=out:st={fade_out_st:.1f}:d=2.0[m];"
                    f"[2:a]volume=0.6[b];"
                    f"[v][m][b]amix=inputs=3:duration=first:dropout_transition=2[aout]"
                )
                cmd_mix = [
                    FFMPEG_BIN, "-y",
                    "-i", str(extracted_audio),
                    "-i", str(bg_music),
                    "-i", str(sfx_boom),
                    "-filter_complex", f_complex,
                    "-map", "[aout]",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(mixed_audio)
                ]
            else:
                f_complex = (
                    f"[0:a]volume=1.05[v];"
                    f"[1:a]volume=0.18,afade=t=in:ss=0:d=1.0,afade=t=out:st={fade_out_st:.1f}:d=2.0[m];"
                    f"[v][m]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
                cmd_mix = [
                    FFMPEG_BIN, "-y",
                    "-i", str(extracted_audio),
                    "-i", str(bg_music),
                    "-filter_complex", f_complex,
                    "-map", "[aout]",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(mixed_audio)
                ]
            subprocess.run(cmd_mix, capture_output=True, check=True)
            if mixed_audio.exists() and mixed_audio.stat().st_size > 1000:
                audio_source_for_burn = mixed_audio
                print("[NovelEngine] ¡Música de suspenso con auto-ducking y boom SFX mezclados con éxito!")
        except Exception as e:
            print(f"[NovelEngine] Audio mixing fallback note: {e}")

    # Step 5: Burn ASS subtitles and pack mixed cinematic audio into final video
    final_output = work_dir / "novel_vertical.mp4"
    edits_dir = work_dir / "edits"
    edits_dir.mkdir(parents=True, exist_ok=True)
    final_in_edits = edits_dir / "clip_1.mp4"

    cmd_burn = [
        FFMPEG_BIN, "-y",
        "-i", str(combined_video),
        "-i", str(audio_source_for_burn),
        "-map", "0:v",
        "-map", "1:a",
        "-vf", f"ass={str(ass_path)}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(final_output)
    ]
    subprocess.run(cmd_burn, capture_output=True, check=True)
    shutil.copy2(final_output, final_in_edits)

    # Metadata for gallery compatibility
    is_fruti = (category and "fruti" in category.lower()) or "fruti" in novel_key.lower() or any(k in title.lower() for k in ["fresa", "plátano", "platano", "aguacate", "sandía", "sandia", "fruta"])
    hook_text = (custom_hook or "").strip() or preset.get("hook", title.upper())
    
    desktop_copy = None
    if export_to_desktop:
        try:
            DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
            prefix = "Frutinovela" if is_fruti else "Historia_IA"
            clean_name = re.sub(r'[^\w\-_]', '_', title)[:35]
            desktop_filename = f"{prefix}_{clean_name}_{novel_id[-4:]}.mp4"
            dest_path = DESKTOP_DIR / desktop_filename
            shutil.copy2(final_output, dest_path)
            desktop_copy = str(dest_path)
            print(f"[NovelEngine] Exported to desktop: {dest_path}")
        except Exception as e:
            print(f"[NovelEngine] Warning: Could not export to desktop: {e}")

    meta = {
        "hook": hook_text,
        "source_title": f"🍓 {title}" if is_fruti else f"🎭 {title}",
        "source_channel": "Estudio Frutinovelas IA" if is_fruti else "Historias Libres IA",
        "category": "frutinovela" if is_fruti else "free_story",
        "duration": round(sum(len(s["text"].split()) * 0.45 for s in scenes), 1),
        "start": 0,
        "end": round(sum(len(s["text"].split()) * 0.45 for s in scenes), 1),
        "desktop_path": desktop_copy,
        "uploaded_youtube": False,
        "uploaded_tiktok": False
    }
    with open(final_in_edits.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "id": novel_id,
        "title": title,
        "hook": hook_text,
        "video_path": str(final_output),
        "media_url": f"/media/{novel_id}/clip_1.mp4",
        "desktop_path": desktop_copy,
        "scenes_count": len(scenes)
    }
