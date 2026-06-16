"""
Scanner d'arbitrage TRIANGULAIRE (version démonstration)
=========================================================

Reste sur UN SEUL exchange et teste des boucles à 3 conversions :
    USDT -> BTC -> ETH -> USDT
On part d'un capital simulé et on regarde si on revient avec plus (frais inclus).

Avantage du triangulaire : tout se passe sur un seul exchange, donc PAS de frais
de retrait ni de temps de transfert entre plateformes.

Cette version (publique) ne fait que SCANNER et AFFICHER. Aucune alerte, aucun
secret, aucun ordre. C'est la version pédagogique du projet.

Usage :
    python scanner_triangulaire.py          # 5 scans (démo)
    python scanner_triangulaire.py 20 10     # 20 scans, toutes les 10s
"""

import ccxt
import sys
import time
from datetime import datetime

EXCHANGE = "kucoin"
BASE = "USDT"
TAKER_FEE = 0.0010
MONTANT_DEPART = 1000.0

INTERMEDIAIRES = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE",
    "LTC", "TRX", "BNB", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
]


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


def convertir(montant, de, vers, marches, tickers):
    """Convertit `montant` de `de` vers `vers`, frais inclus. None si prix manquant."""
    sym_achat = f"{vers}/{de}"   # on achète 'vers' -> on paie le ask
    sym_vente = f"{de}/{vers}"   # on vend 'de'     -> on touche le bid
    if sym_achat in marches:
        t = tickers.get(sym_achat)
        if not t or not t.get("ask"):
            return None
        return (montant / t["ask"]) * (1 - TAKER_FEE)
    if sym_vente in marches:
        t = tickers.get(sym_vente)
        if not t or not t.get("bid"):
            return None
        return (montant * t["bid"]) * (1 - TAKER_FEE)
    return None


def evaluer_triangle(triangle, marches, tickers):
    base, x, y = triangle
    m1 = convertir(MONTANT_DEPART, base, x, marches, tickers)
    if m1 is None:
        return None
    m2 = convertir(m1, x, y, marches, tickers)
    if m2 is None:
        return None
    m3 = convertir(m2, y, base, marches, tickers)
    if m3 is None:
        return None
    return (m3 - MONTANT_DEPART) / MONTANT_DEPART * 100


def main():
    max_scans = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    intervalle = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    exchange = getattr(ccxt, EXCHANGE)({"enableRateLimit": True})
    print(f"Chargement des marchés de {EXCHANGE}...")
    exchange.load_markets()

    triangles = construire_triangles(exchange.markets)
    print(f"{len(triangles)} triangles découverts à partir de {BASE}.\n")

    for scan in range(1, max_scans + 1):
        horodatage = datetime.now().strftime("%H:%M:%S")
        try:
            tickers = exchange.fetch_tickers()
        except Exception as e:
            print(f"[{horodatage}] Erreur réseau ({type(e).__name__}), on réessaie...")
            time.sleep(intervalle)
            continue

        resultats = []
        for tri in triangles:
            profit = evaluer_triangle(tri, exchange.markets, tickers)
            if profit is not None:
                resultats.append((tri, profit))
        resultats.sort(key=lambda r: r[1], reverse=True)

        print(f"[{horodatage}] Scan #{scan} — Top 3 :")
        for (base, x, y), profit in resultats[:3]:
            marqueur = "  ✅ RENTABLE" if profit > 0 else ""
            print(f"    {base}->{x}->{y}->{base:<5}  {profit:+.4f} %{marqueur}")

        if scan < max_scans:
            time.sleep(intervalle)

    print("\nTerminé. (Démonstration : aucun ordre passé, aucun argent engagé.)")


if __name__ == "__main__":
    main()
