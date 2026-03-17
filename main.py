from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import os
import json
import time
from dotenv import load_dotenv
import re

print("DEBUG: main.py caricato")

load_dotenv()

SUGGERITI_URL = "https://www.instagram.com/explore/people/"
COOKIES_JSON = os.getenv("INSTAGRAM_COOKIES")  # Cookie di sessione in formato JSON
MAX_FOLLOW = 70  # Numero massimo di account da seguire per sessione
MIN_COMUNI = 7   # Minimo follower in comune richiesti


def carica_cookies(context):
    """Carica i cookie di sessione Instagram nel browser."""
    print("DEBUG: carica_cookies() chiamata")
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
    Naviga sulla pagina dei suggeriti e segue solo gli account
    che hanno almeno MIN_COMUNI follower in comune.
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

    while seguiti < MAX_FOLLOW:
        try:
            chiudi_popup(page)

            # Ogni "row" contiene avatar, nome, testo follower in comune e bottone Segui.
            # Partiamo da un div generico che contenga un bottone Segui/Follow.
            rows = page.locator("div").filter(
                has=page.locator("button:has-text('Segui'), button:has-text('Follow')")
            )
            count = rows.count()
            print(f"Righe suggerite trovate: {count}")

            if count == 0:
                print("Nessun suggerimento trovato. Ricarico la pagina...")
                page.goto(SUGGERITI_URL, timeout=60000)
                page.wait_for_timeout(4000)
                tentativi_falliti += 1
                if tentativi_falliti >= max_tentativi_falliti:
                    print("Troppi tentativi falliti. Uscita.")
                    break
                continue

            cliccato_almeno_uno = False

            for i in range(count):
                if seguiti >= MAX_FOLLOW:
                    break

                row = rows.nth(i)

                # Cerca lo span che contiene "Follower" (italiano) o "Mutual followers"/"Followers you follow" ecc.
                info_loc = row.locator(
                    "span:has-text('Follower'), span:has-text('followers in common'), "
                    "span:has-text('Mutual followers')"
                )

                if info_loc.count() == 0:
                    continue

                info_text = info_loc.first.inner_text().strip()
                # Esempi possibili:
                # "vallesamm + altri 9"
                # "vallesamm e altri 9"
                # "mario.rossi"
                # "mario.rossi and 3 others" (inglese)

                comuni = 0
                # casi "altri 9" / "others 9"
                m = re.search(r"(altri|others)\s+(\d+)", info_text)
                if m:
                    comuni = int(m.group(2)) + 1  # uno è il nome mostrato
                else:
                    # Se non ci sono "altri"/"others" ma almeno un nome, consideriamo 1 in comune
                    if info_text:
                        comuni = 1

                if comuni < MIN_COMUNI:
                    # Non raggiunge la soglia minima, passa al prossimo suggerimento
                    continue

                bottone = row.locator("button:has-text('Segui'), button:has-text('Follow')").first
                if not bottone.is_visible():
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
                    f"Nessun bottone cliccabile trovato con >= {MIN_COMUNI} "
                    f"follower in comune (tentativo {tentativi_falliti})"
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
    print("DEBUG: main() avviato")
    print("DEBUG: COOKIES_JSON presente:", bool(COOKIES_JSON))
    if not COOKIES_JSON:
        print("Errore: INSTAGRAM_COOKIES non trovato. Aggiungi il secret su GitHub.")
        return
    try:
        with sync_playwright() as p:
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
    print("DEBUG: __main__ eseguito")
    main()
