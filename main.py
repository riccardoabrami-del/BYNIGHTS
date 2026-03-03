from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

SUGGERITI_URL = "https://www.instagram.com/explore/people/"
COOKIES_JSON = os.getenv("INSTAGRAM_COOKIES")  # Cookie di sessione in formato JSON
MAX_FOLLOW = 70  # Numero massimo di account da seguire per sessione


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


def segui_account_suggeriti(page):
    """Naviga sulla pagina dei suggeriti e segue gli account."""
    print("Navigo sulla pagina degli account suggeriti...")
    page.goto(SUGGERITI_URL, timeout=60000)
    page.wait_for_timeout(5000)

    # Verifica che il login sia andato a buon fine
    if "accounts/login" in page.url:
        print("Errore: non loggato. I cookie potrebbero essere scaduti.")
        return

    print("Login confermato tramite cookie. Inizio follow...")
    seguiti = 0

    for i in range(MAX_FOLLOW):
        try:
            # Cerca bottoni 'Segui' (italiano) o 'Follow' (inglese)
            bottoni = page.locator("button", has_text="Segui").all()
            if not bottoni:
                bottoni = page.locator("button", has_text="Follow").all()

            if not bottoni:
                print("Nessun bottone Segui trovato. Uscita.")
                break

            bottone = bottoni[0]
            bottone.scroll_into_view_if_needed()
            bottone.click(timeout=5000)
            seguiti += 1
            print(f"Seguito account {seguiti}/{MAX_FOLLOW}")

            # Pausa tra un follow e l'altro per evitare blocchi
            time.sleep(3)

            # Ricarica ogni 5 follow per avere nuovi suggerimenti
            if seguiti % 5 == 0:
                page.reload()
                page.wait_for_timeout(4000)

        except Exception as e:
            print(f"Errore durante il follow {seguiti + 1}: {e}")
            continue

    print(f"Operazione completata. Account seguiti oggi: {seguiti}")


def main():
    if not COOKIES_JSON:
        print("Errore: INSTAGRAM_COOKIES non trovato. Aggiungi il secret su GitHub.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Carica i cookie di sessione
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
