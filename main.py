print("BYNIGHTS main.py caricato")
...
def main():
    print("BYNIGHTS main() avviato")
    ...


def segui_account_suggeriti(page):
    """Naviga sulla pagina dei suggeriti e segue gli account con abbastanza follower in comune."""
    print("Navigo sulla pagina degli account suggeriti...")
    page.goto(SUGGERITI_URL, timeout=60000)
    page.wait_for_timeout(5000)

    if "accounts/login" in page.url:
        print("Errore: non loggato. I cookie potrebbero essere scaduti.")
        return

    print("Login confermato tramite cookie. Inizio follow con soglia mutual =", SOGLIA_MUTUAL)
    seguiti = 0
    tentativi_falliti = 0
    max_tentativi_falliti = 10

    while seguiti < MAX_FOLLOW:
        try:
            chiudi_popup(page)

            # trova tutti gli span che contengono "Follower:"
            span_list = page.locator("span:has-text('Follower:')").all()
            print("Span Follower trovati:", len(span_list))

            if not span_list:
                print("Nessuno span Follower trovato. Ricarico la pagina...")
                page.goto(SUGGERITI_URL, timeout=60000)
                page.wait_for_timeout(4000)
                tentativi_falliti += 1
                if tentativi_falliti >= max_tentativi_falliti:
                    print("Troppi tentativi falliti. Uscita.")
                    break
                continue

            cliccato = False

            for span in span_list:
                try:
                    if not span.is_visible():
                        continue

                    testo = span.inner_text()
                    # es: "Follower: _matteomacchi___ + altri 8"
                    if "altri" not in testo:
                        continue

                    num_str = testo.split("altri")[-1].strip()
                    num = int("".join(ch for ch in num_str if ch.isdigit()))
                    print("Follower in comune trovati:", num)

                    if num < SOGLIA_MUTUAL:
                        continue

                    # risali al contenitore (card) e al bottone Segui
                    card = span.locator("xpath=ancestor::div[1]")
                    bottone = card.locator("button:has(div:has-text('Segui'))").first
                    if not bottone.is_visible():
                        continue

                    chiudi_popup(page)
                    bottone.scroll_into_view_if_needed()
                    bottone.click(timeout=3000, force=True)
                    page.wait_for_timeout(1000)

                    seguiti += 1
                    tentativi_falliti = 0
                    print(f"Seguito account {seguiti}/{MAX_FOLLOW} (mutual {num})")
                    cliccato = True

                    time.sleep(2)

                    if seguiti % 5 == 0:
                        page.reload()
                        page.wait_for_timeout(4000)

                    break  # torna al while per aggiornare

                except Exception as e:
                    print(f"Errore su span/card: {e}")
                    chiudi_popup(page)
                    continue

            if not cliccato:
                tentativi_falliti += 1
                print(f"Nessun account con >= {SOGLIA_MUTUAL} mutual cliccabile (tentativo {tentativi_falliti})")
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

    print(f"Operazione completata. Account seguiti oggi: {seguiti}")
