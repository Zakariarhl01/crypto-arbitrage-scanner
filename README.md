# 🔍 Crypto Arbitrage Scanner

Un projet d'exploration des **3 grands types d'arbitrage crypto**, construit pour
comprendre comment fonctionnent (et pourquoi sont *difficiles*) les bots de trading
d'arbitrage. Les scanners **lisent les prix publics** de plusieurs exchanges et
calculent la rentabilité réelle — **aucun ordre n'est passé, aucun argent engagé**.

## 🎯 Objectif

Répondre à une vraie question avec des données réelles, pas des promesses :
> « Peut-on gagner de l'argent avec un bot d'arbitrage crypto quand on est seul ? »

La réponse courte, démontrée par le code : **techniquement oui, financièrement très
difficile** — les frais et la concurrence des bots professionnels effacent la
quasi-totalité des écarts.

## 📦 Contenu

| Fichier | Type d'arbitrage | Ce qu'il démontre |
|---|---|---|
| `scanner_inter_exchange.py` | Inter-exchange (gros caps) | Les écarts BTC/ETH/SOL sont minuscules ; les frais les annulent |
| `scanner_petites_cryptos.py` | Inter-exchange (small caps) + liquidité | Le **slippage** : un écart « au prix affiché » disparaît quand on simule un vrai trade en marchant dans le carnet d'ordres |
| `scanner_triangulaire.py` | Triangulaire (intra-exchange) | Une boucle `USDT→X→Y→USDT` sur un seul exchange ; les 3× frais (~0.30 %) forment un plancher difficile à battre |

## 🧠 Concepts techniques couverts

- **CCXT** : connexion unifiée à ~100 exchanges
- **bid / ask** : on achète au *ask*, on vend au *bid* (jamais au « prix »)
- **Carnet d'ordres & slippage** : « marcher dans le carnet » pour estimer le prix réel d'un trade
- **Frais maker / taker** : leur impact décisif sur la rentabilité
- **Arbitrage triangulaire** : découverte automatique des triangles disponibles
- **Programmation** : gestion d'erreurs réseau, scan en boucle, calculs de rentabilité

## 🚀 Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scanner_inter_exchange.py
python scanner_petites_cryptos.py
python scanner_triangulaire.py        # 5 scans de démonstration
```

## 📊 Exemple de résultat (triangulaire)

```
USDT->XRP->BTC->USDT   -0.2626 %
USDT->BNB->BTC->USDT   -0.2953 %
USDT->ETH->BTC->USDT   -0.2956 %
```

Les meilleurs triangles se collent au plancher des frais (~-0.30 %) : le marché est
**efficient**. C'est exactement la leçon que ce projet met en évidence.

## ⚠️ Avertissement

Projet **éducatif**. Ce n'est pas un conseil financier. L'arbitrage rentable est
dominé par des acteurs disposant d'infrastructures à très basse latence et de frais
quasi nuls. À utiliser pour apprendre, pas pour « devenir riche ».
