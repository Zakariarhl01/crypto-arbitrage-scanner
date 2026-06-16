"""
Scanner d'arbitrage crypto — Étapes 1 & 2
==========================================

Ce que fait ce script (et RIEN de plus pour l'instant) :
  1. Se connecte à plusieurs exchanges crypto (lecture publique, AUCUNE clé API)
  2. Lit les prix de BTC, ETH, SOL en temps réel
  3. Compare les prix entre exchanges
  4. Calcule l'écart APRÈS frais (le seul chiffre qui compte vraiment)
  5. Affiche les opportunités d'arbitrage détectées

⚠️  Il ne passe AUCUN ordre. Aucun argent réel n'est engagé. C'est un observateur.

Concept clé à comprendre :
  - On n'achète JAMAIS au "prix affiché". On achète au ASK (prix demandé par les vendeurs)
    et on vend au BID (prix proposé par les acheteurs).
  - Donc un vrai arbitrage = acheter au ASK le plus bas, vendre au BID le plus haut,
    sur deux exchanges différents, et vérifier que l'écart couvre les frais des DEUX côtés.
"""

import ccxt  # la librairie qui parle à ~100 exchanges avec le même code

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

# Les exchanges qu'on interroge. Tous accessibles en lecture publique depuis la France.
# On donne aussi leur frais "taker" (frais quand on prend un ordre immédiat = arbitrage).
# Ces frais sont approximatifs — à ajuster selon ton vrai niveau de compte.
EXCHANGES = {
    "kraken": {"taker_fee": 0.0026},   # 0.26 %
    "kucoin": {"taker_fee": 0.0010},   # 0.10 %
    "bybit":  {"taker_fee": 0.0010},   # 0.10 %
}

# Les paires qu'on surveille. Format unifié par CCXT : BASE/QUOTE
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]


# --------------------------------------------------------------------------
# ÉTAPE 1 : récupérer les prix (bid/ask) de chaque exchange
# --------------------------------------------------------------------------

def recuperer_prix():
    """
    Retourne un dictionnaire de la forme :
        { "BTC/USDT": { "kraken": {"bid": ..., "ask": ...}, "kucoin": {...} }, ... }
    Si un exchange ou un symbole échoue, on le saute proprement.
    """
    resultats = {symbole: {} for symbole in SYMBOLS}

    for nom_exchange, config in EXCHANGES.items():
        # ccxt.kraken(), ccxt.kucoin(), etc. — on instancie dynamiquement
        classe_exchange = getattr(ccxt, nom_exchange)
        exchange = classe_exchange({"enableRateLimit": True})  # respecte les limites d'appels

        for symbole in SYMBOLS:
            try:
                ticker = exchange.fetch_ticker(symbole)  # 1 appel API public
                resultats[symbole][nom_exchange] = {
                    "bid": ticker["bid"],   # meilleur prix d'achat proposé (là où TU vends)
                    "ask": ticker["ask"],   # meilleur prix de vente proposé (là où TU achètes)
                }
            except Exception as e:
                # Symbole absent sur cet exchange, ou souci réseau : on ignore et on continue
                print(f"  ⚠️  {nom_exchange} / {symbole} : indisponible ({type(e).__name__})")

    return resultats


# --------------------------------------------------------------------------
# ÉTAPE 2 : comparer et calculer l'écart APRÈS frais
# --------------------------------------------------------------------------

def analyser(prix_par_symbole):
    """
    Pour chaque symbole, trouve le meilleur achat et la meilleure vente,
    puis calcule le profit net en % une fois les frais des deux côtés déduits.
    """
    for symbole, prix_exchanges in prix_par_symbole.items():
        print(f"\n=== {symbole} ===")

        # On garde seulement les exchanges qui ont renvoyé un bid ET un ask valides
        valides = {
            ex: p for ex, p in prix_exchanges.items()
            if p["bid"] is not None and p["ask"] is not None
        }

        if len(valides) < 2:
            print("  Pas assez d'exchanges pour comparer.")
            continue

        # Affiche les prix bruts de chaque exchange
        for ex, p in valides.items():
            print(f"  {ex:8s} | bid (vente) {p['bid']:>12,.2f} | ask (achat) {p['ask']:>12,.2f}")

        # Où acheter le moins cher ? -> le ASK le plus bas
        exchange_achat = min(valides, key=lambda ex: valides[ex]["ask"])
        # Où vendre le plus cher ?   -> le BID le plus haut
        exchange_vente = max(valides, key=lambda ex: valides[ex]["bid"])

        prix_achat = valides[exchange_achat]["ask"]
        prix_vente = valides[exchange_vente]["bid"]

        # Écart BRUT (l'illusion du débutant)
        ecart_brut_pct = (prix_vente - prix_achat) / prix_achat * 100

        # Écart NET (la réalité) : on paie des frais à l'achat ET à la vente
        frais_achat = EXCHANGES[exchange_achat]["taker_fee"]
        frais_vente = EXCHANGES[exchange_vente]["taker_fee"]

        cout_total   = prix_achat * (1 + frais_achat)   # ce que ça coûte vraiment d'acheter
        revenu_total = prix_vente * (1 - frais_vente)    # ce qu'on récupère vraiment en vendant
        ecart_net_pct = (revenu_total - cout_total) / cout_total * 100

        # Verdict
        if exchange_achat == exchange_vente:
            print("  → Achat et vente sur le même exchange : pas d'arbitrage inter-exchange.")
            continue

        print(f"  → Acheter sur {exchange_achat} @ {prix_achat:,.2f}, "
              f"vendre sur {exchange_vente} @ {prix_vente:,.2f}")
        print(f"     Écart brut : {ecart_brut_pct:+.3f} %   |   "
              f"Écart NET (après frais) : {ecart_net_pct:+.3f} %")

        if ecart_net_pct > 0:
            print(f"  ✅ OPPORTUNITÉ : +{ecart_net_pct:.3f} % net")
        else:
            print(f"  ❌ Non rentable : les frais mangent l'écart.")


# --------------------------------------------------------------------------
# POINT D'ENTRÉE
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("Scanner d'arbitrage — lecture des prix en cours...\n")
    prix = recuperer_prix()
    analyser(prix)
    print("\nTerminé. (Aucun ordre passé, aucun argent engagé.)")
