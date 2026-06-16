"""
Scanner d'arbitrage — Chasseur de petites cryptos + mesure de liquidité
========================================================================

Différence avec scanner.py :
  - On ne regarde plus seulement BTC/ETH/SOL, mais une liste de cryptos
    petites/moyennes (là où les gros bots ne se fatiguent pas).
  - SURTOUT : on ne se fie plus au prix du dessus du carnet. On "marche
    dans le carnet d'ordres" pour simuler un VRAI achat d'une certaine taille
    (ex: 500 USDT) et calculer le prix moyen réellement obtenu.

  => Ça révèle la différence entre :
       • l'écart "naïf"  (prix du dessus) -> ce qui a l'air rentable
       • l'écart "réel"  (après slippage) -> ce qui est vraiment exploitable

⚠️  Toujours AUCUN ordre passé. Lecture publique uniquement. Zéro argent engagé.
"""

import ccxt

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

EXCHANGES = {
    "kraken": {"taker_fee": 0.0026},
    "kucoin": {"taker_fee": 0.0010},
    "bybit":  {"taker_fee": 0.0010},
}

# Cryptos petites/moyennes à tester (toutes en paire /USDT).
# Le script vérifiera automatiquement lesquelles existent sur >= 2 exchanges.
CANDIDATS = [
    "INJ/USDT", "FET/USDT", "RNDR/USDT", "ARB/USDT", "OP/USDT",
    "SUI/USDT", "SEI/USDT", "TIA/USDT", "JUP/USDT", "WIF/USDT",
    "PYTH/USDT", "JTO/USDT", "ONDO/USDT", "ENA/USDT", "W/USDT",
    "ALGO/USDT", "GALA/USDT", "AR/USDT", "GMT/USDT", "DYDX/USDT",
]

# Taille du trade simulé. C'est LE paramètre clé : un écart peut être rentable
# pour 100 USDT et catastrophique pour 2000 USDT (carnet trop fin).
TRADE_SIZE_USDT = 500.0


# --------------------------------------------------------------------------
# OUTILS : "marcher dans le carnet d'ordres"
# --------------------------------------------------------------------------

def simuler_achat(asks, montant_usdt):
    """
    Simule l'achat pour `montant_usdt` en consommant les ordres de vente (asks),
    du moins cher au plus cher.
    Retourne : (quantite_obtenue, usdt_reellement_depenses).
    Si le carnet est trop fin, usdt_depenses sera < montant_usdt (on signale ça après).
    """
    depense = 0.0
    quantite = 0.0
    for prix, volume in asks:               # asks triés du prix le plus bas au plus haut
        cout_niveau = prix * volume
        if depense + cout_niveau >= montant_usdt:
            reste = montant_usdt - depense  # il ne reste qu'à acheter une fraction de ce niveau
            quantite += reste / prix
            depense = montant_usdt
            break
        depense += cout_niveau              # on "mange" tout ce niveau et on continue
        quantite += volume
    return quantite, depense


def simuler_vente(bids, quantite):
    """
    Simule la vente de `quantite` en consommant les ordres d'achat (bids),
    du plus cher au moins cher.
    Retourne : (usdt_recus, quantite_non_vendue).
    Si quantite_non_vendue > 0, le carnet n'était pas assez profond.
    """
    recu = 0.0
    restant = quantite
    for prix, volume in bids:               # bids triés du prix le plus haut au plus bas
        if volume >= restant:
            recu += restant * prix
            restant = 0.0
            break
        recu += volume * prix
        restant -= volume
    return recu, restant


# --------------------------------------------------------------------------
# RÉCUPÉRATION DES CARNETS D'ORDRES
# --------------------------------------------------------------------------

def charger_exchanges():
    """Instancie les exchanges et charge la liste de leurs marchés disponibles."""
    instances = {}
    for nom in EXCHANGES:
        ex = getattr(ccxt, nom)({"enableRateLimit": True})
        try:
            ex.load_markets()
            instances[nom] = ex
        except Exception as e:
            print(f"⚠️  Impossible de charger {nom} : {type(e).__name__}")
    return instances


def recuperer_carnets(instances):
    """
    Pour chaque candidat présent sur au moins 2 exchanges, récupère le carnet d'ordres.
    Retourne : { symbole: { exchange: {"bids": [...], "asks": [...]} } }
    """
    resultats = {}
    for symbole in CANDIDATS:
        # Quels exchanges proposent ce symbole ?
        dispo = [nom for nom, ex in instances.items() if symbole in ex.markets]
        if len(dispo) < 2:
            continue  # pas comparable, on saute

        carnets = {}
        for nom in dispo:
            try:
                ob = instances[nom].fetch_order_book(symbole, limit=20)  # 20 niveaux suffisent
                if ob["bids"] and ob["asks"]:
                    carnets[nom] = {"bids": ob["bids"], "asks": ob["asks"]}
            except Exception as e:
                print(f"  ⚠️  {nom} / {symbole} : {type(e).__name__}")
        if len(carnets) >= 2:
            resultats[symbole] = carnets
    return resultats


# --------------------------------------------------------------------------
# ANALYSE
# --------------------------------------------------------------------------

def analyser(carnets_par_symbole):
    opportunites = []

    for symbole, carnets in carnets_par_symbole.items():
        # Meilleur prix d'achat = ask le plus bas ; meilleure vente = bid le plus haut
        ex_achat = min(carnets, key=lambda n: carnets[n]["asks"][0][0])
        ex_vente = max(carnets, key=lambda n: carnets[n]["bids"][0][0])
        if ex_achat == ex_vente:
            continue

        ask_top = carnets[ex_achat]["asks"][0][0]
        bid_top = carnets[ex_vente]["bids"][0][0]

        # --- Écart NAÏF (prix du dessus, après frais) : l'illusion ---
        f_achat = EXCHANGES[ex_achat]["taker_fee"]
        f_vente = EXCHANGES[ex_vente]["taker_fee"]
        cout_naif   = ask_top * (1 + f_achat)
        revenu_naif = bid_top * (1 - f_vente)
        ecart_naif_pct = (revenu_naif - cout_naif) / cout_naif * 100

        # --- Écart RÉEL (on marche dans le carnet pour TRADE_SIZE_USDT) : la vérité ---
        qte, depense = simuler_achat(carnets[ex_achat]["asks"], TRADE_SIZE_USDT)
        qte_nette = qte * (1 - f_achat)  # les frais réduisent la quantité reçue
        usdt_recus, non_vendu = simuler_vente(carnets[ex_vente]["bids"], qte_nette)
        usdt_recus_net = usdt_recus * (1 - f_vente)

        carnet_trop_fin = (depense < TRADE_SIZE_USDT - 0.01) or (non_vendu > 0)
        ecart_reel_pct = (usdt_recus_net - depense) / depense * 100 if depense > 0 else 0.0

        opportunites.append({
            "symbole": symbole,
            "ex_achat": ex_achat,
            "ex_vente": ex_vente,
            "naif": ecart_naif_pct,
            "reel": ecart_reel_pct,
            "fin": carnet_trop_fin,
        })

    # Tri : les meilleurs écarts RÉELS en haut
    opportunites.sort(key=lambda o: o["reel"], reverse=True)

    # Affichage
    print(f"\n{'Crypto':<11} {'Achat':<8} {'Vente':<8} "
          f"{'Écart naïf':>11} {'Écart réel':>11}   Verdict (pour {TRADE_SIZE_USDT:.0f} USDT)")
    print("-" * 78)
    for o in opportunites:
        if o["fin"]:
            verdict = "⚠️  carnet trop fin (mirage)"
        elif o["reel"] > 0:
            verdict = f"✅ RENTABLE +{o['reel']:.3f}%"
        else:
            verdict = "❌ frais/slippage"
        print(f"{o['symbole']:<11} {o['ex_achat']:<8} {o['ex_vente']:<8} "
              f"{o['naif']:>+10.3f}% {o['reel']:>+10.3f}%   {verdict}")

    print("\nLecture :")
    print("  • Écart naïf = au prix du dessus du carnet (ce qui a l'air rentable)")
    print(f"  • Écart réel = après avoir vraiment acheté/vendu pour {TRADE_SIZE_USDT:.0f} USDT (slippage inclus)")
    print("  • 'carnet trop fin' = pas assez d'ordres pour absorber le trade -> l'écart est un mirage")
    print("  ⚠️  Non inclus : frais de retrait, temps de transfert, risque d'exécution.")


# --------------------------------------------------------------------------
# POINT D'ENTRÉE
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("Chasseur de petites cryptos — chargement des marchés...")
    instances = charger_exchanges()
    print("Récupération des carnets d'ordres (peut prendre ~30s)...")
    carnets = recuperer_carnets(instances)
    print(f"{len(carnets)} cryptos comparables trouvées.")
    analyser(carnets)
    print("\nTerminé. (Aucun ordre passé, aucun argent engagé.)")
