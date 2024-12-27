from pathlib import Path
import json
import time
from playwright.sync_api import sync_playwright

# ==========================
# 📁 Configuration
# ==========================
COOKIES_FILE = Path("cookies.json").resolve()
NOTIFICATIONS_URL = "https://www.vinted.fr/member/notifications"

# ==========================
# 🍪 Gestion des Cookies
# ==========================
def charger_cookies():
    """Charge les cookies depuis le fichier JSON."""
    try:
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
            print(f"✅ Cookies chargés depuis le fichier JSON : {COOKIES_FILE}")
            return cookies
    except FileNotFoundError:
        print("❌ Fichier JSON non trouvé.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de lecture du JSON : {e}")
        return []

def sauvegarder_cookies(cookies):
    """Enregistre les cookies dans le fichier JSON."""
    try:
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=4)
        print(f"✅ Cookies sauvegardés dans le fichier JSON : {COOKIES_FILE}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des cookies : {e}")

def verifier_cookies(cookies):
    """Vérifie que les cookies requis sont présents."""
    noms_cookies = {cookie.get('name') for cookie in cookies}
    requis = ["refresh_token_web", "v_sid", "v_uid"]
    manquants = [cookie for cookie in requis if cookie not in noms_cookies]

    if manquants:
        print(f"❌ Cookies manquants : {', '.join(manquants)}")
        return False
    print("✅ Tous les cookies requis sont présents.")
    return True

def verifier_et_mettre_a_jour_refresh_token(cookies, anciens_cookies):
    """Vérifie si le refresh_token_web a changé et met à jour si nécessaire."""
    nouveau_token = next((cookie['value'] for cookie in cookies if cookie['name'] == 'refresh_token_web'), None)
    ancien_token = next((cookie['value'] for cookie in anciens_cookies if cookie['name'] == 'refresh_token_web'), None)

    if nouveau_token and nouveau_token != ancien_token:
        print("🔄 Nouveau refresh_token détecté. Mise à jour des cookies...")
        sauvegarder_cookies(cookies)
        return True
    return False

# ==========================
# 🖱️ Clic sur le Bouton "Tout Refuser"
# ==========================
def cliquer_sur_tout_refuser(page):
    """Clique sur le bouton 'Tout Refuser' si présent."""
    try:
        if page.is_visible("#onetrust-reject-all-handler"):
            page.click("#onetrust-reject-all-handler")
            print("✅ Bouton 'Tout Refuser' cliqué avec succès.")
        else:
            print("⚠️ Bouton 'Tout Refuser' non trouvé.")
    except Exception as e:
        print(f"❌ Erreur lors du clic sur 'Tout Refuser' : {e}")

# ==========================
# 🌐 Automatisation avec Playwright
# ==========================
def connecter_aux_notifications(intervalle=60):
    """Connexion à la page des notifications avec les cookies."""
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="vinted_session",
                headless=False,
                ignore_https_errors=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=SameSiteByDefaultCookies",
                    "--disable-extensions",
                    "--disable-translate",
                    "--disable-sync"
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            context = browser
            cookies = charger_cookies()
            anciens_cookies = cookies.copy()

            if verifier_cookies(cookies):
                try:
                    context.add_cookies(cookies)
                    print("✅ Cookies ajoutés au contexte.")
                except Exception as e:
                    print(f"❌ Erreur lors de l'ajout des cookies : {e}")
                    return
            else:
                print("⚠️ Cookies invalides. Vérifiez `cookies.json`.")
                return

            # Accéder à la page de notifications directement
            page = context.new_page()
            try:
                page.goto(NOTIFICATIONS_URL, wait_until="domcontentloaded", timeout=60000)
                print(f"✅ Navigation réussie vers les notifications : {NOTIFICATIONS_URL}")
                cliquer_sur_tout_refuser(page)
            except Exception as e:
                print(f"❌ Erreur lors de la navigation : {e}")
                print("🔍 Contenu de la page après erreur :")
                print(page.content())
                return

            # Récupération périodique des cookies
            while True:
                try:
                    print("🔄 Récupération des cookies...")
                    nouveaux_cookies = context.cookies(NOTIFICATIONS_URL)
                    if verifier_et_mettre_a_jour_refresh_token(nouveaux_cookies, anciens_cookies):
                        anciens_cookies = nouveaux_cookies.copy()
                        print("✅ Les cookies ont été mis à jour avec succès.")
                    else:
                        print("✅ Aucun changement détecté dans les cookies.")

                    print(f"⏸️ Pause de {intervalle} secondes avant la prochaine récupération.")
                    time.sleep(intervalle)
                except KeyboardInterrupt:
                    print("🛑 Interruption par l'utilisateur.")
                    break
        except Exception as e:
            print(f"❌ Erreur générale : {e}")
        finally:
            if 'browser' in locals():
                browser.close()
                print("✅ Fermeture du navigateur.")

# ==========================
# 🏁 Exécution Principale
# ==========================
if __name__ == "__main__":
    if not COOKIES_FILE.exists():
        print("❌ Le fichier cookies.json n'existe pas. Ajoutez des cookies valides avant de continuer.")
    else:
        connecter_aux_notifications(intervalle=60)
