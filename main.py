import re

SOGLIA_FOLLOWER_COMUNI = 7

def segui_account_con_follower_comuni(page):
    """
    Scorre le card dei suggeriti e segue solo gli account
    che hanno almeno SOGLIA_FOLLOWER_COMUNI follower in comune.
    """
    seguiti = 0
    tentativi_falliti = 0
    max_tentativi_falliti = 10

    while seguiti < MAX_FOLLOW:
        try:
            chiudi_popup(page)

            # prendi tutte le card utente (il contenitore grande)
            cards = page.locator("div[role='button'] div[style*='display: flex']").all()

            if not cards:
                print("Nessuna card trovata, ricarico pagina...")
                page.goto(SUGGERITI_URL, timeout=60000)
                page.wait_for_timeout(4000)
                tentativi_falliti += 1
                if tentativi_falliti >= max_tentativi_falliti:
                    print("Troppi tentativi falliti. Uscita.")
                    break
                continue

            cliccato_qualcosa = False

            for card in cards:
                try:
                    chiudi_popup(page)

                    # testo con i follower in comune (es. "Follower: xxx + altri 4")
                    follower_text = card.locator("span:has-text('Follower')").first.inner_text(timeout=3000)
                    print("DEBUG follower_text:", follower_text)

                    # cerco l'ultimo numero nel testo (es. 4 in "+ altri 4")
                    numeri = re.findall(r"\d+", follower_text)
                    if not numeri:
                        continue
                    follower_comuni = int(numeri[-1])

                    if follower_comuni < SOGLIA_FOLLOWER_COMUNI:
                        continue  # salta se meno di 7

                    # bottone Segui dentro la stessa card
                    bottone = card.locator("button:has-text('Segui')").first
                    if not bottone.is_visible():
                        continue

                    bottone.scroll_into_view_if_needed()
                    bottone.click(timeout=3000, force=True)
                    page.wait_for_timeout(1000)

                    seguiti += 1
                    tentativi_falliti = 0
                    cliccato_qualcosa = True
                    print(f"Seguito account {seguiti}/{MAX_FOLLOW} (follower comuni: {follower_comuni})")

                    time.sleep(2)

                    if seguiti % 5 == 0:
                        page.reload()
                        page.wait_for_timeout(4000)

                    if seguiti >= MAX_FOLLOW:
                        break

                except Exception as e:
                    print(f"Errore sulla card: {e}")
                    chiudi_popup(page)
                    continue

            if not cliccato_qualcosa:
                tentativi_falliti += 1
                print(f"Nessun account con almeno {SOGLIA_FOLLOWER_COMUNI} follower in comune (tentativo {tentativi_falliti})")
                page.keyboard.press("End")
                time.sleep(2)
                if tentativi_falliti >= max_tentativi_falliti:
                    page.goto(SUGGERITI_URL, timeout=60000)
                    page.wait_for_timeout(4000)
                    tentativi_falliti = 0

        except Exception as e:
            print(f"Errore nel loop principale (follower comuni): {e}")
            tentativi_falliti += 1
            time.sleep(2)
            continue

    print(f"Operazione completata. Account seguiti oggi: {seguiti}")
