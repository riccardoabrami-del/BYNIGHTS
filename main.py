from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import os
from dotenv import load_dotenv
import time

load_dotenv()

URL = "https://www.instagram.com/"
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


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

    # Aspetta un po' che faccia il login
    page.wait_for_timeout(10000)


def main():
    if not USERNAME or not PASSWORD:
        print("Errore: credenziali non trovate (INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD).")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # headless=True per GitHub Actions
            page = browser.new_page()

            login_instagram(page)

            # Qui puoi aggiungere altri step dopo il login
            print("Login eseguito (se le credenziali sono corrette e Instagram non blocca l’accesso).")

            browser.close()
    except PWTimeoutError:
        print("Timeout durante il login a Instagram.")
    except Exception as e:
        print(f"Errore imprevisto: {e}")


if __name__ == "__main__":
    main()
