"""
Comparateur d'arbitrage triangulaire MULTI-PLATEFORMES
=======================================================

Né d'un retour terrain : « faut voir les plateformes et les frais aussi ».

Ce scanner répond précisément à ces deux points :
  1. LES FRAIS : au lieu de deviner, il récupère les VRAIS frais de chaque exchange
     via CCXT (taker/maker), et permet de les surcharger avec ton taux réel
     (réduction token maison, gros volume...).
  2. LES PLATEFORMES : il évalue le meilleur triangle sur PLUSIEURS exchanges et
     les classe, pour voir laquelle offre les conditions les plus favorables.

Pourquoi c'est crucial :
  Le "plancher" de rentabilité d'un triangle = 3 × frais par ordre.
    - À 0.10 % de frais -> plancher à -0.30 % (dur à battre)
    - À 0.02 % de frais -> plancher à -0.06 % (des opportunités deviennent possibles)
  => Le choix de la plateforme et l'optimisation des frais changent TOUT.

⚠️ Lecture publique uniquement. Aucun ordre, aucun argent engagé.
"""

import ccxt

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

BASE = "USDT"
MONTANT_DEPART = 1000.0

# "taker" = ordre au marché (réaliste pour l'arbitrage rapide)
# "maker" = ordre limite (frais plus bas, mais exécution non garantie)
MODE_FRAIS = "taker"

EXCHANGES = ["kucoin", "bybit", "binance", "okx", "gate", "kraken"]

# Surcharge optionnelle des frais réels (mets TON vrai taux si tu en as un).
# Exemple : Kucoin -20 % en payant les frais en KCS -> 0.0008 au lieu de 0.001.
FRAIS_PERSO = {
    # "kucoin": 0.0008,
    # "binance": 0.00075,   # -25 % en payant en BNB
}

INTERMEDIAIRES = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE",
    "LTC", "TRX", "BNB", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
]


# --------------------------------------------------------------------------
# LOGIQUE TRIANGULAIRE
# --------------------------------------------------------------------------

def paire_existe(a, b, marches):
    return f"{a}/{b}" in marches or f"{b}/{a}" in marches


def construire_triangles(marches):
    triangles = []
    for x in INTERMEDIAIRES:
        for y in INTERMEDIAIRES:
            if x == y:
                continue
            if (paire_existe(BASE, x, marches)
                    and paire_existe(x, y, marches)
                    and paire_existe(y, BASE, marches)):
                triangles.append((BASE, x, y))
    return triangles


def convertir(montant, de, vers, marches, tickers, fee):
    sym_achat = f"{vers}/{de}"
    sym_vente = f"{de}/{vers}"
    if sym_achat in marches:
        t = tickers.get(sym_achat)
        if not t or not t.get("ask"):
            return None
        return (montant / t["ask"]) * (1 - fee)
    if sym_vente in marches:
        t = tickers.get(sym_vente)
        if not t or not t.get("bid"):
            return None
        return (montant * t["bid"]) * (1 - fee)
    return None


def evaluer_triangle(triangle, marches, tickers, fee):
    base, x, y = triangle
    m1 = convertir(MONTANT_DEPART, base, x, marches, tickers, fee)
    if m1 is None:
        return None
    m2 = convertir(m1, x, y, marches, tickers, fee)
    if m2 is None:
        return None
    m3 = convertir(m2, y, base, marches, tickers, fee)
    if m3 is None:
        return None
    return (m3 - MONTANT_DEPART) / MONTANT_DEPART * 100


def frais_de(exchange, nom):
    """Frais par ordre : ton taux perso s'il existe, sinon le VRAI taux de l'exchange."""
    if nom in FRAIS_PERSO:
        return FRAIS_PERSO[nom], "perso"
    marche = exchange.markets.get("ETH/USDT")
    fee = (marche or {}).get(MODE_FRAIS)
    if fee is None:  # secours : frais par défaut de l'exchange
        fee = exchange.fees.get("trading", {}).get(MODE_FRAIS, 0.001)
    return fee, MODE_FRAIS


# --------------------------------------------------------------------------
# COMPARAISON
# --------------------------------------------------------------------------

def main():
    print(f"Comparaison multi-plateformes (mode frais : {MODE_FRAIS})\n")

    resultats = []
    for nom in EXCHANGES:
        try:
            exchange = getattr(ccxt, nom)({"enableRateLimit": True})
            exchange.load_markets()
            fee, source = frais_de(exchange, nom)
            triangles = construire_triangles(exchange.markets)
            tickers = exchange.fetch_tickers()

            meilleur = None
            for tri in triangles:
                profit = evaluer_triangle(tri, exchange.markets, tickers, fee)
                if profit is not None and (meilleur is None or profit > meilleur[1]):
                    meilleur = (tri, profit)

            if meilleur:
                resultats.append((nom, fee, source, meilleur))
                print(f"  ✓ {nom} : {len(triangles)} triangles, frais {fee*100:.3f}% ({source})")
        except Exception as e:
            print(f"  ✗ {nom} : indisponible ({type(e).__name__})")

    resultats.sort(key=lambda r: r[3][1], reverse=True)

    print(f"\n{'Plateforme':<11}{'Frais/ordre':>12}{'Plancher (3x)':>14}   Meilleur triangle")
    print("-" * 78)
    for nom, fee, source, (tri, profit) in resultats:
        base, x, y = tri
        plancher = -3 * fee * 100
        verdict = "  ✅ RENTABLE" if profit > 0 else ""
        print(f"{nom:<11}{fee*100:>10.3f}%{plancher:>12.2f}%    "
              f"{base}->{x}->{y}->{base}  {profit:+.4f}%{verdict}")

    print("\nLecture :")
    print("  • Frais/ordre = vrai taux de la plateforme (ou ton taux perso si défini)")
    print("  • Plancher (3x) = -3 × frais : le profit brut doit dépasser ça pour être rentable")
    print("  • Le meilleur triangle est rarement positif -> marchés efficients")
    print("  • Conclusion : baisser ses frais (maker, token maison, volume) est le vrai levier.")


if __name__ == "__main__":
    main()
