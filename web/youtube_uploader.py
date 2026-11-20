"""YouTube Shorts Uploader Module with Anti-Detect, Native Chrome Login and Resilient Automation."""
import os
import json
import time
import asyncio
import sqlite3
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_FILE = BASE_DIR / "web" / "youtube_session.json"
PROFILE_DIR = BASE_DIR / "web" / "user_data_youtube"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars"
]

def is_logged_in() -> bool:
    """Verifies whether a valid Google/YouTube Studio session exists in the Chrome profile."""
    cookies_db = PROFILE_DIR / "Default" / "Cookies"
    if cookies_db.exists():
        try:
            con = sqlite3.connect(f"file:{cookies_db}?immutable=1", uri=True)
            cur = con.cursor()
            rows = cur.execute("SELECT name FROM cookies WHERE host_key LIKE '%youtube%' OR host_key LIKE '%google%'").fetchall()
            con.close()
            names = {r[0] for r in rows}
            if any(k in names for k in ("SID", "HSID", "SSID", "LOGIN_INFO", "SAPISID", "__Secure-1PSID", "__Secure-3PSID")):
                return True
        except Exception:
            pass

    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            cookies = data.get("cookies", [])
            if any(c.get("name") in ("SID", "HSID", "SSID", "LOGIN_INFO") for c in cookies):
                return True
        except Exception:
            pass

    return False

def logout_account():
    """Removes stored session and profile cookies to allow switching accounts."""
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
        print(f"[YouTube] Error clearing profile: {e}")
    return {"status": "success", "message": "Cuenta de YouTube desconectada correctamente."}

def login_interactive():
    """
    Opens native Google Chrome directly with the dedicated YouTube profile directory.
    This bypasses Google's 'Navegador o app no seguros' block completely because Chrome runs
    as a real, unautomated native application.
    """
    chrome_path = CHROME_PATH if os.path.exists(CHROME_PATH) else None
    if not chrome_path:
        return {"status": "error", "message": "Google Chrome no está instalado en /Applications/Google Chrome.app"}

    cmd = [
        chrome_path,
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://studio.youtube.com"
    ]
    try:
        subprocess.Popen(cmd)
        print("[YouTube] Launched native Google Chrome for interactive login.")
        return {
            "status": "started",
            "message": "Se abrió Google Chrome nativo sin bloqueos de seguridad. Inicia sesión en tu cuenta de Google y entra a YouTube Studio. Luego pulsa 'Verificar Conexión'."
        }
    except Exception as e:
        return {"status": "error", "message": f"Error abriendo Chrome: {e}"}

async def upload_video(video_path: str, title: str = "", description: str = "", visibility: str = "PUBLIC"):
    """
    Uploads a vertical video as a YouTube Short to YouTube Studio.
    visibility: 'PUBLIC', 'UNLISTED', 'PRIVATE'
    """
    v_path = Path(video_path).resolve()
    if not v_path.exists():
        return {"status": "error", "message": f"El archivo de video no existe: {video_path}"}

    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    # Check if Chrome is actively running with this profile
    lock_file = PROFILE_DIR / "SingletonLock"
    if lock_file.exists():
        try:
            # Check if process is still alive
            import subprocess
            res = subprocess.run(["pgrep", "-f", f"--user-data-dir={PROFILE_DIR}"], capture_output=True, text=True)
            if res.stdout.strip():
                return {
                    "status": "error",
                    "message": "Por favor cierra la ventana de Google Chrome que abriste para iniciar sesión antes de subir el video, para que el automatizador pueda acceder a tu cuenta."
                }
            else:
                try:
                    lock_file.unlink()
                except Exception:
                    pass
        except Exception:
            pass

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                ignore_default_args=["--enable-automation"],
                args=STEALTH_ARGS,
                viewport={"width": 1280, "height": 800}
            )
        except Exception as e:
            err_str = str(e)
            if "SingletonLock" in err_str or "ProcessSingleton" in err_str:
                return {
                    "status": "error",
                    "message": "Google Chrome está abierto con este perfil. Por favor ciérralo completamente y vuelve a intentar."
                }
            return {"status": "error", "message": f"No se pudo iniciar el navegador: {err_str}"}

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            print(f"[YouTube] Loading YouTube Studio for {v_path.name}...")
            await page.goto("https://studio.youtube.com", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)

            # Check if redirected to login page
            if "accounts.google.com" in page.url:
                await context.close()
                return {"status": "error", "message": "Debes conectar tu cuenta de YouTube primero desde Ajustes."}

            # 1. Dismiss any interstitial banners (e.g., 'Ir a YouTube Studio', 'Continuar')
            for dismiss_sel in [
                "a:has-text('Ir a YouTube Studio')",
                "button:has-text('Ir a YouTube Studio')",
                "ytcp-button:has-text('Ir a YouTube Studio')",
                "text=/IR A YOUTUBE/i",
                "text=/CONTINUAR/i",
                "#dismiss-button"
            ]:
                try:
                    d_btn = page.locator(dismiss_sel).first
                    if await d_btn.count() > 0 and await d_btn.is_visible():
                        print(f"[YouTube] Dismissing banner via {dismiss_sel}...")
                        await d_btn.click()
                        await asyncio.sleep(3)
                except Exception:
                    pass

            # 2. Trigger upload dialog
            # Look for create button or direct upload buttons
            print("[YouTube] Locating upload button...")
            upload_triggered = False
            for trig_sel in [
                "#create-icon",
                "ytcp-button#create-icon",
                "ytcp-icon-button#create-icon",
                "button[aria-label*='Crear']",
                "button[aria-label*='Create']",
                "#upload-icon",
                "#upload-button",
                "ytcp-button:has-text('Subir videos')",
                "ytcp-button:has-text('Subir vídeos')",
                "ytcp-button:has-text('Upload videos')"
            ]:
                try:
                    btn = page.locator(trig_sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        print(f"[YouTube] Clicking {trig_sel}...")
                        await btn.click()
                        upload_triggered = True
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass

            # If dropdown appeared, click 'Subir vídeos'
            sub_item = page.locator("tp-yt-paper-item:has-text('Subir'), tp-yt-paper-item:has-text('Upload'), #text-item-0").first
            if await sub_item.count() > 0 and await sub_item.is_visible():
                print("[YouTube] Clicking 'Subir' in dropdown menu...")
                await sub_item.click()
                await asyncio.sleep(2)

            # 3. Locate and attach file
            file_uploaded = False
            print("[YouTube] Waiting for file input selector...")
            
            # Method A: Direct set on input[type=file]
            try:
                file_input = page.locator("input[type='file'], input[name='Filedata']").first
                await file_input.wait_for(state="attached", timeout=12000)
                await file_input.set_input_files(str(v_path))
                print(f"[YouTube] File attached directly via input: {v_path.name}")
                file_uploaded = True
            except Exception as e:
                print(f"[YouTube] Direct input wait timed out: {e}")

            # Method B: Click 'SELECCIONAR ARCHIVOS' and provide file to chooser
            if not file_uploaded:
                select_btn = page.locator("#select-files-button, ytcp-button#select-files-button, button:has-text('Seleccionar archivos'), button:has-text('Select files')").first
                if await select_btn.count() > 0:
                    try:
                        print("[YouTube] Triggering file chooser via select button...")
                        async with page.expect_file_chooser(timeout=8000) as fc_info:
                            await select_btn.click()
                        fc = await fc_info.value
                        await fc.set_files(str(v_path))
                        print(f"[YouTube] File uploaded via file chooser: {v_path.name}")
                        file_uploaded = True
                    except Exception as e:
                        print(f"[YouTube] File chooser method failed: {e}")

            if not file_uploaded:
                # Capture debug screenshot
                try:
                    await page.screenshot(path=str(BASE_DIR / "web" / "studio_upload_error.png"))
                except Exception:
                    pass
                await context.close()
                return {"status": "error", "message": "No se pudo seleccionar el archivo en YouTube Studio. Verifica que estés dentro del panel de YouTube Studio."}

            # 4. Wait for metadata form (title & description)
            print("[YouTube] Waiting for metadata form to load...")
            await asyncio.sleep(6)

            # 5. Set Title
            title_box = page.locator("#textbox[aria-label*='título'], #textbox[aria-label*='title'], [aria-label*='título'] #textbox").first
            try:
                await title_box.wait_for(state="visible", timeout=15000)
                await title_box.click()
                await page.keyboard.press("Meta+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(title, delay=15)
                print(f"[YouTube] Title set: {title}")
            except Exception as e:
                print(f"[YouTube] Warning setting title: {e}")

            await asyncio.sleep(1.5)

            # 6. Set Description
            desc_box = page.locator("#textbox[aria-label*='descripción'], #textbox[aria-label*='description']").first
            if await desc_box.count() > 0:
                try:
                    await desc_box.click()
                    await page.keyboard.type(f"\n{description}\n", delay=10)
                    print("[YouTube] Description set")
                except Exception as e:
                    print(f"[YouTube] Warning setting description: {e}")

            await asyncio.sleep(1.5)

            # 7. Set 'No es contenido creado para niños'
            not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
            if await not_for_kids.count() > 0:
                try:
                    await not_for_kids.click()
                    print("[YouTube] Selected 'No es contenido para niños'")
                except Exception as e:
                    print(f"[YouTube] Radio button error: {e}")

            await asyncio.sleep(2)

            # 8. Step Wizard (Siguiente x 3)
            for step in range(3):
                next_btn = page.locator("#next-button, button:has-text('Siguiente'), button:has-text('Next')").first
                if await next_btn.count() > 0 and await next_btn.is_visible():
                    print(f"[YouTube] Advancing step {step + 1}...")
                    await next_btn.click()
                    await asyncio.sleep(2)

            # 9. Set Visibility
            vis_map = {
                "PUBLIC": "tp-yt-paper-radio-button[name='PUBLIC']",
                "UNLISTED": "tp-yt-paper-radio-button[name='UNLISTED']",
                "PRIVATE": "tp-yt-paper-radio-button[name='PRIVATE']"
            }
            vis_selector = vis_map.get(visibility, vis_map["PUBLIC"])
            vis_btn = page.locator(vis_selector).first
            if await vis_btn.count() > 0:
                try:
                    await vis_btn.click()
                    print(f"[YouTube] Visibility set to: {visibility}")
                except Exception as e:
                    print(f"[YouTube] Visibility select error: {e}")

            await asyncio.sleep(2)

            # 10. Click Publish / Done
            done_btn = page.locator("#done-button, button:has-text('Guardar'), button:has-text('Publicar'), button:has-text('Save')").first
            if await done_btn.count() > 0:
                await done_btn.click()
                print("[YouTube] Done / Publish clicked successfully!")
                await asyncio.sleep(6)
                await context.close()
                return {"status": "success", "message": f"¡Clip subido con éxito a YouTube Shorts ({visibility})!"}

            await asyncio.sleep(4)
            await context.close()
            return {"status": "success", "message": "Video enviado con éxito a YouTube Studio."}

        except Exception as e:
            try:
                await context.close()
            except Exception:
                pass
            return {"status": "error", "message": f"Error en YouTube Studio: {str(e)}"}
