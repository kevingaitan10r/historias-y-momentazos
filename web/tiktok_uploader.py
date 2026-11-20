"""TikTok Uploader Module with Anti-Detect (Stealth) and Local Profile."""
import os
import json
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_FILE = BASE_DIR / "web" / "tiktok_session.json"
PROFILE_DIR = BASE_DIR / "web" / "user_data_tiktok"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
    "--lang=es-ES,es",
    "--remote-debugging-port=0"
]

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

def is_logged_in() -> bool:
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            cookies = data.get("cookies", [])
            valid_keys = ("sessionid", "sessionid_ss", "sid_guard", "sid_tt", "passport_auth_status", "uid_tt")
            if any(c.get("name") in valid_keys for c in cookies):
                return True
        except Exception:
            pass
    return False

def logout_account():
    """Removes stored session and profile cookies to allow switching TikTok accounts."""
    if SESSION_FILE.exists():
        try:
            SESSION_FILE.unlink()
        except Exception:
            pass
    try:
        import shutil
        if PROFILE_DIR.exists():
            shutil.rmtree(PROFILE_DIR)
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[TikTok] Error clearing profile: {e}")
    return {"status": "success", "message": "Cuenta de TikTok desconectada."}

def save_session_from_cookie(cookie_input: str):
    """Saves a valid TikTok session JSON directly from a browser sessionid cookie or full cookie string."""
    cookie_input = cookie_input.strip()
    if not cookie_input:
        return {"status": "error", "message": "La cookie no puede estar vacía."}
    
    exp = time.time() + (86400 * 365)  # 1 año
    cookies = []

    # Caso 1: JSON array de Cookie-Editor
    if cookie_input.startswith("[") and cookie_input.endswith("]"):
        try:
            raw_list = json.loads(cookie_input)
            for c in raw_list:
                if c.get("name") and c.get("value"):
                    cookies.append({
                        "name": c["name"],
                        "value": c["value"],
                        "domain": c.get("domain", ".tiktok.com"),
                        "path": c.get("path", "/"),
                        "expires": c.get("expirationDate", exp),
                        "httpOnly": bool(c.get("httpOnly", True)),
                        "secure": bool(c.get("secure", True)),
                        "sameSite": "Lax"
                    })
        except Exception:
            pass

    # Caso 2: Cadena con punto y coma (e.g. "sessionid=xyz; ttwid=abc; ...")
    if not cookies and ("=" in cookie_input and ";" in cookie_input):
        pairs = [p.strip() for p in cookie_input.split(";") if "=" in p]
        for p in pairs:
            k, v = p.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and v:
                cookies.append({
                    "name": k,
                    "value": v,
                    "domain": ".tiktok.com",
                    "path": "/",
                    "expires": exp,
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "Lax"
                })

    # Caso 3: Token puro de sessionid o "sessionid=xyz"
    if not cookies:
        token = cookie_input.strip().strip('"').strip("'")
        if token.startswith("sessionid="):
            token = token.split("sessionid=", 1)[1].strip()
        for k in ("sessionid", "sessionid_ss", "sid_guard", "sid_tt", "passport_auth_status"):
            val = "1" if k == "passport_auth_status" else token
            cookies.append({
                "name": k,
                "value": val,
                "domain": ".tiktok.com",
                "path": "/",
                "expires": exp,
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            })

    storage = {"cookies": cookies, "origins": []}
    SESSION_FILE.write_text(json.dumps(storage, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[TikTok] Guardadas {len(cookies)} cookies en {SESSION_FILE}")
    return {"status": "success", "message": f"¡Sesión de TikTok guardada con éxito ({len(cookies)} cookies)! Ya puedes subir clips."}

async def login_interactive():
    """Opens visible Chrome with stealth flags for the user to log in to TikTok."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            headless=False,
            user_agent=USER_AGENT,
            ignore_default_args=["--enable-automation"],
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 850}
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
        """)

        print("[TikTok] Opening TikTok login with Stealth Profile...")
        await page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")

        start_time = time.time()
        logged_in = False
        while time.time() - start_time < 360:
            cookies = await context.cookies()
            valid_keys = ("sessionid", "sessionid_ss", "sid_guard", "sid_tt", "passport_auth_status", "uid_tt")
            has_session = any(c.get("name") in valid_keys for c in cookies)
            current_url = page.url
            
            # URL redirection to feed or profile also confirms login
            url_logged = ("tiktok.com/@" in current_url or 
                          "tiktok.com/foryou" in current_url or 
                          "creator-center" in current_url or
                          ("tiktok.com" in current_url and "login" not in current_url and len(cookies) > 5))
            
            if has_session or url_logged:
                # Wait 3 extra seconds to make sure persistent storage cookies settle
                await asyncio.sleep(3)
                cookies_after = await context.cookies()
                if any(c.get("name") in valid_keys for c in cookies_after):
                    logged_in = True
                    print("[TikTok] Login confirmed! Saving session...")
                    break
            await asyncio.sleep(2)

        if logged_in:
            storage = await context.storage_state()
            SESSION_FILE.write_text(json.dumps(storage, indent=2), encoding="utf-8")
            await context.close()
            return {"status": "success", "message": "Sesión de TikTok guardada con éxito."}
        else:
            await context.close()
            return {"status": "timeout", "message": "Tiempo agotado para iniciar sesión."}

async def upload_video(video_path: str, title: str = "", tags: str = "#GTA6 #GTA #Gaming #Clips", post_mode: str = "draft"):
    v_path = Path(video_path).resolve()
    if not v_path.exists():
        return {"status": "error", "message": f"El archivo no existe: {video_path}"}

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            headless=False,
            user_agent=USER_AGENT,
            ignore_default_args=["--enable-automation"],
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 800}
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Inyectar cookies de sesión guardadas
        if SESSION_FILE.exists():
            try:
                s_data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
                stored_cookies = s_data.get("cookies", [])
                if stored_cookies:
                    sanitized = []
                    for c in stored_cookies:
                        item = {
                            "name": str(c["name"]),
                            "value": str(c["value"]),
                            "domain": c.get("domain", ".tiktok.com"),
                            "path": c.get("path", "/")
                        }
                        if "secure" in c:
                            item["secure"] = bool(c["secure"])
                        if "httpOnly" in c:
                            item["httpOnly"] = bool(c["httpOnly"])
                        sanitized.append(item)
                    await context.add_cookies(sanitized)
                    print(f"[TikTok] Inyectadas {len(sanitized)} cookies en la sesión.")
            except Exception as e:
                print(f"[TikTok] Error inyectando cookies: {e}")

        try:
            print(f"[TikTok] Opening Creator Upload for {v_path.name}...")
            await page.goto("https://www.tiktok.com/creator-center/upload?from=upload", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)

            if "login" in page.url:
                await context.close()
                return {"status": "error", "message": "La sesión de TikTok expiró. Vuelve a conectar tu cuenta."}

            file_input = page.locator("input[type='file']")
            if await file_input.count() == 0:
                for frame in page.frames:
                    if await frame.locator("input[type='file']").count() > 0:
                        file_input = frame.locator("input[type='file']").first
                        break

            if await file_input.count() > 0:
                print(f"[TikTok] Setting file input: {v_path}")
                await file_input.set_input_files(str(v_path))
            else:
                await page.set_input_files("input[type='file']", str(v_path))

            print("[TikTok] Waiting for video processing...")
            await asyncio.sleep(8)

            caption_text = f"{title} {tags}".strip()
            caption_box = page.locator("div[contenteditable='true'], .public-DraftEditor-content, textarea").first
            if await caption_box.count() > 0:
                await caption_box.click()
                await page.keyboard.press("Meta+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(caption_text, delay=20)

            await asyncio.sleep(4)

            if post_mode == "post":
                post_btn = page.locator("button:has-text('Publicar'), button:has-text('Post')").first
                if await post_btn.count() > 0:
                    await post_btn.click()
                    await asyncio.sleep(6)
                    await context.close()
                    return {"status": "success", "message": "¡Video publicado en TikTok con éxito!"}
            else:
                draft_btn = page.locator("button:has-text('Guardar como borrador'), button:has-text('Save draft'), button:has-text('Borrador')").first
                if await draft_btn.count() > 0:
                    await draft_btn.click()
                    await asyncio.sleep(5)
                    await context.close()
                    return {"status": "success", "message": "¡Video guardado en borradores de TikTok!"}

            await asyncio.sleep(5)
            await context.close()
            return {"status": "success", "message": "Video cargado en el portal de TikTok."}

        except Exception as e:
            await context.close()
            return {"status": "error", "message": f"Error subiendo a TikTok: {str(e)}"}
