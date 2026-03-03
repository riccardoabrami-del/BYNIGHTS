from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import os
from dotenv import load_dotenv
import time

load_dotenv()

URL = "https://www.instagram.com/"
SUGGERITI_URL = "https://www.instagram.com/explore/people/"
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
MAX_FOLLOW = 20  # Numero massimo di account da seguire per sessione


def login_instagram(page):
    # Vai alla home / pagina di login
    page.goto(URL, timeout=60000)

    # Aspetta che compaiano i campi
    page.wait_for_timeout(5000)

    # Compila username
    page.locator("input[name='username']").fill(USERNAME)

    # Compila password
    page.locator("input[name='password']").fill(PASSWORD)

    # Clicca il bottone Log In
    page.locator("button[type='submit']").click()

    # Aspetta che il login si completi
    page.wait_for_timeout(10000)
    print("Login completato.")


def segui_account_suggeriti(page):
    print("Navigo sulla pagina degli account suggeriti...")
    page.goto(SUGGERITI_URL, timeout=60000)
    page.wait_for_timeout(5000)

    seguiti = 0

    for i in range(MAX_FOLLOW):
        try:
            # Cerca tutti i bottoni 'Segui' visibili sulla pagina
            bottoni = page.locator("button", has_text="Segui").all()

            if not bottoni:
                # Prova anche in inglese nel caso la lingua sia diversa
                bottoni = page.locator("button", has_text="Follow").all()

            if not bottoni:
                print("Nessun bottone Segui trovato. Uscita.")
                break

            # Clicca il primo bottone disponibile
            bottone = bottoni[0]
            bottone.scroll_into_view_if_needed()
            bottone.click()
            seguiti += 1
            print(f"Seguito account {seguiti}/{MAX_FOLLOW}")

            # Pausa tra un follow e l'altro per evitare blocchi
            time.sleep(3)

            # Ricarica la lista ogni 5 follow per avere nuovi suggerimenti
            if seguiti % 5 == 0:
                page.reload()
                page.wait_for_timeout(4000)

        except Exception as e:
            print(f"Errore durante il follow: {e}")
            break

    print(f"Operazione completata. Account seguiti: {seguiti}")


def main():
    if not USERNAME or not PASSWORD:
        print("Errore: credenziali non trovate (INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD).")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            login_instagram(page)
            segui_account_suggeriti(page)

            browser.close()

    except PWTimeoutError:
        print("Timeout durante il login a Instagram.")
    except Exception as e:
        print(f"Errore imprevisto: {e}")


if __name__ == "__main__":
    main()
