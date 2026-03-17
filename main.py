from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import os
import json
import time
from dotenv import load_dotenv
import re

load_dotenv()

SUGGERITI_URL = "https://www.instagram.com/explore/people/"
COOKIES_JSON = os.getenv("INSTAGRAM_COOKIES")  # Cookie di sessione in formato JSON
MAX_FOLLOW = 70  # Numero massimo di account da seguire per sessione
MIN_COMUNI = 7   # minimo "altri" + 1

def carica_cookies(context):
    """Carica i cookie di sessione Instagram nel browser."""
    if not COOKIES_JSON:
        print("Errore: INSTAGRAM_COOKIES non trovato nei secrets.")
        return False
    try:
        cookies = json.loads(COOKIES_JSON)
        context.add_cookies(cookies)
        print(f"Cookie caricati con successo ({len(cookies)} cookie).")
        return True
    except Exception as e:
        print(f"Errore nel caricamento dei cookie: {e}")
        return False


def chiudi_popup(page):
    """Chiude eventuali popup o dialoghi aperti su Instagram."""
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        for testo in ["Non ora", "Not Now", "Chiudi", "Close", "Cancel"]:
            btn = page.locator(f"button:has-text('{testo}')").first
            if btn.is_visible():
                btn.click(timeout=3000)
                time.sleep(0.5)
                break
    except Exception:
        pass


def segui_account_suggeriti(page):
    """
    Naviga sulla pagina dei suggeriti e segue SOLO gli account
    che hanno "+ altri N" con N >= 7 (quindi almeno 7 follower in comune).
    """
    print("Navigo sulla pagina degli account suggeriti...")
    page.goto(SUGGERITI_URL, timeout=60000)
    page.wait_for_timeout(5000)

    if "accounts/login" in page.url:
        print("Errore: non loggato. I cookie potrebbero essere scaduti.")
        return

    print("Login confermato tramite cookie. Inizio follow filtrato...")
    seguiti = 0
    tentativi_falliti = 0
    max_tentativi_falliti = 10

    inizio = time.time()
    max_secondi = 600  # 10 minuti di sicurezza

    while seguiti < MAX_FOLLOW and (time.time() - inizio) < max_secondi:
        try:
            chiudi_popup(page)

            # tutti gli span che contengono il testo "Follower:"
            spans = page.locator("span:has-text('Follower:')")
            count = spans.count()
            print(f"Span 'Follower:' trovati: {count}")

            if count == 0:
                print("Nessuno span trovato. Scrollo/ricarico...")
                page.keyboard.press("End")
                time.sleep(2)
                tentativi_falliti += 1
                if tentativi_falliti >= max_tentativi_falliti:
                    page.goto(SUGGERITI_URL, timeout=60000)
                    page.wait_for_timeout(4000)
                    tentativi_falliti = 0
                continue

            cliccato_almeno_uno = False

            for i in range(count):
                if seguiti >= MAX_FOLLOW:
                    break

                span = spans.nth(i)
                info_text = span.inner_text().strip()
                print("DEBUG info_text:", repr(info_text))

                # es. "Follower: clelia_12.___ + altri 4"
                m = re.search(r"\+ altri\s+(\d+)", info_text)
                if not m:
                    print("Skip: nessun '+ altri N' nel testo")
                    continue

                altri = int(m.group(1))
                comuni = altri + 1  # 1 è il primo nome mostrato

                if comuni < MIN_COMUNI:
                    print(f"Skip: solo {comuni} follower in comune")
                    continue

                # risalgo al contenitore card (div grande che contiene anche il bottone)
                card = span.locator("xpath=ancestor::div[contains(@class,'html-div')][1]") \
                           .locator("xpath=ancestor::div[contains(@class,'html-div')][1]")

                bottone = card.locator(
                    "button:has(div:has-text('Segui'))"
                ).first

                if bottone.count() == 0 or not bottone.is_visible():
                    print("DEBUG: bottone Segui non trovato/visibile per questo span")
                    continue

                try:
                    chiudi_popup(page)
                    bottone.scroll_into_view_if_needed()
                    bottone.click(timeout=3000, force=True)
                    page.wait_for_timeout(1000)

                    seguiti += 1
                    tentativi_falliti = 0
                    cliccato_almeno_uno = True
                    print(
                        f"Seguito account {seguiti}/{MAX_FOLLOW} "
                        f"(follower in comune: {comuni})"
                    )

                    time.sleep(2)

                    if seguiti % 5 == 0:
                        page.reload()
                        page.wait_for_timeout(4000)

                except Exception as e:
                    print(f"Errore click bottone: {e}")
                    chiudi_popup(page)
                    continue

            if not cliccato_almeno_uno:
                tentativi_falliti += 1
                print(
                    f"Nessun bottone cliccabile con >= {MIN_COMUNI} follower in comune "
                    f"(tentativo {tentativi_falliti})"
                )
                page.keyboard.press("End")
                time.sleep(2)
                if tentativi_falliti >= max_tentativi_falliti:
                    page.goto(SUGGERITI_URL, timeout=60000)
                    page.wait_for_timeout(4000)
                    tentativi_falliti = 0

        except Exception as e:
            print(f"Errore nel loop principale: {e}")
            tentativi_falliti += 1
            time.sleep(2)
            continue

    print(
        f"Operazione completata. Account seguiti oggi (>= {MIN_COMUNI} follower in comune): "
        f"{seguiti}"
    )


def main():
    if not COOKIES_JSON:
        print("Errore: INSTAGRAM_COOKIES non trovato. Aggiungi il secret su GitHub.")
        return
    try:
        with sync_playwright() as p:
            # per debug locale: headless=False, slow_mo=500
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            ok = carica_cookies(context)
            if not ok:
                browser.close()
                return
            page = context.new_page()
            segui_account_suggeriti(page)
            browser.close()
    except PWTimeoutError:
        print("Timeout durante la navigazione.")
    except Exception as e:
        print(f"Errore imprevisto: {e}")


if __name__ == "__main__":
    main()
