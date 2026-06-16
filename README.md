# 🔍 Crypto Arbitrage Scanner

> Projet d'exploration : **« Peut-on, seul, gagner de l'argent avec un bot d'arbitrage crypto ? »**
> Réponse construite avec du **code réel** et des **données de marché réelles** — pas des promesses.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![CCXT](https://img.shields.io/badge/CCXT-4.5+-green)
![License](https://img.shields.io/badge/usage-éducatif-orange)
![Trading](https://img.shields.io/badge/orders-aucun%20(read--only)-lightgrey)

---

## 🎯 Le problème

L'arbitrage crypto est partout présenté comme une « machine à imprimer de l'argent » :
acheter un actif moins cher sur une plateforme, le revendre plus cher sur une autre,
empocher la différence. Sur le papier, c'est simple. **Mais est-ce vrai en pratique
pour un développeur seul ?**

Plutôt que de croire les promesses, j'ai construit **trois scanners** pour mesurer la
réalité des écarts de prix sur des exchanges réels, frais et liquidité inclus.

## 🧪 TL;DR — Les résultats

| Question | Réponse mesurée |
|---|---|
| Y a-t-il des écarts de prix ? | Oui, mais **minuscules** (souvent < 0.05 %) |
| Survivent-ils aux frais ? | **Non** — les frais (0.1–0.26 % par ordre) les effacent |
| Les petites cryptos sont-elles une niche ? | **Pas sur les gros exchanges** : déjà arbitrées, et le slippage tue les gros trades |
| Le triangulaire (1 exchange) est-il rentable ? | Plancher à ~**-0.30 %** (3× les frais) : marché efficient |

> **Conclusion honnête : techniquement faisable, financièrement très difficile pour un
> particulier.** L'arbitrage rentable est dominé par des sociétés à infrastructure
> ultra-rapide et frais quasi nuls. Ce projet le *prouve* avec des chiffres.

---

## 🧰 Les trois scanners

### 1. `scanner_inter_exchange.py` — Arbitrage entre plateformes
Compare le prix de **BTC / ETH / SOL** sur Kraken, Kucoin et Bybit.
Démontre la différence cruciale entre **écart brut** (illusion) et **écart net après
frais** (réalité).

```
=== BTC/USDT ===
  → Acheter sur kucoin, vendre sur kraken
     Écart brut : +0.009 %   |   Écart NET (après frais) : -0.350 %
  ❌ Non rentable : les frais mangent l'écart.
```

### 2. `scanner_petites_cryptos.py` — Petites cryptos + liquidité
Teste ~20 cryptos petites/moyennes et **« marche dans le carnet d'ordres »** pour
simuler un vrai trade de 500 USDT. Révèle le **slippage** : un écart séduisant « au
prix affiché » s'effondre dès qu'on trade un vrai volume.

```
Crypto      Achat    Vente     Écart naïf  Écart réel   Verdict
GMT/USDT    kucoin   bybit        -0.319%     -0.654%   ❌ frais/slippage
```
*(le slippage double parfois la perte entre l'écart « naïf » et l'écart « réel »)*

### 3. `scanner_triangulaire.py` — Arbitrage triangulaire (intra-exchange)
**Découvre automatiquement** tous les triangles possibles (ex: `USDT→BTC→ETH→USDT`)
sur un seul exchange, et calcule si la boucle est gagnante. Avantage : pas de frais
de retrait ni de transfert entre plateformes.

```
USDT->XRP->BTC->USDT   -0.2626 %
USDT->BNB->BTC->USDT   -0.2953 %
USDT->ETH->BTC->USDT   -0.2956 %
```
*(les meilleurs triangles se collent au plancher des 3× frais ≈ -0.30 % → marché efficient)*

### 4. `scanner_multi_plateformes.py` — Comparateur frais & plateformes
Ajouté suite à un **retour terrain** (« faut voir les plateformes et les frais aussi »).
Récupère les **vrais frais** de chaque exchange via CCXT et compare le meilleur triangle
sur 5-6 plateformes. Met en évidence que le plancher de rentabilité = **3 × frais**, et
que le bon choix combine **frais bas** ET **paires encore peu arbitrées**.

```
Plateforme  Frais/ordre  Plancher (3x)   Meilleur triangle
gate           0.200%       -0.60%       USDT->ADA->BTC->USDT  -0.2294%   ← frais + hauts, mais meilleur triangle
binance        0.100%       -0.30%       USDT->BTC->XRP->USDT  -0.2950%
kraken         0.400%       -1.20%       USDT->BTC->LTC->USDT  -1.1700%   ← frais élevés = rédhibitoire
```

---

## 🏗️ Démarche

1. **Hypothèse** : « il existe des écarts exploitables ».
2. **Mesure inter-exchange** → écarts réels < frais. Hypothèse invalidée pour les gros caps.
3. **Hypothèse affinée** : « les petites cryptos sont une niche moins concurrencée ».
4. **Mesure avec liquidité** → le slippage tue l'avantage. Invalidée sur gros exchanges.
5. **Dernier angle** : le triangulaire élimine frais de retrait et transferts.
6. **Mesure** → plancher des frais incompressible. Conclusion documentée.

> Cette boucle *hypothèse → mesure → conclusion* est le vrai cœur du projet :
> une démarche d'ingénieur, pas un pari.

## 🛠️ Stack & concepts techniques

- **Python 3.9+** · **CCXT** (connexion unifiée à ~100 exchanges)
- **bid / ask** : on achète au *ask*, on vend au *bid* — jamais au « prix »
- **Carnet d'ordres & slippage** : simulation de trade en « marchant dans le carnet »
- **Frais maker / taker** et leur impact décisif
- **Arbitrage triangulaire** : découverte automatique de cycles dans un graphe de paires
- **Robustesse** : gestion d'erreurs réseau, scan en boucle, rate limiting

## 📂 Structure

```
.
├── scanner_inter_exchange.py     # arbitrage entre plateformes (gros caps)
├── scanner_petites_cryptos.py    # petites cryptos + mesure de liquidité/slippage
├── scanner_triangulaire.py       # triangulaire intra-exchange (découverte auto)
├── scanner_multi_plateformes.py  # comparateur frais réels & plateformes (v2, retour terrain)
├── requirements.txt
└── README.md
```

## 🚀 Installation & lancement

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python scanner_inter_exchange.py
python scanner_petites_cryptos.py
python scanner_triangulaire.py    # 5 scans de démonstration
```
Aucune clé API requise : tout est en **lecture publique**.

## 🎓 Ce que j'ai appris

- Manipuler une **API financière temps réel** et raisonner sur des données de marché.
- L'écart entre la **théorie** (prix affiché) et la **réalité** (frais + slippage + liquidité).
- Pourquoi **l'efficience de marché** existe et qui capte réellement les opportunités.
- Structurer un projet **proprement et en sécurité** (séparation code public / privé,
  secrets dans des variables d'environnement, jamais dans le code).

## ⚠️ Avertissement

Projet **strictement éducatif**, ce n'est pas un conseil financier. Les scanners ne
passent **aucun ordre** et n'engagent **aucun argent**. L'arbitrage rentable demande
des moyens (capital, infrastructure basse latence) hors de portée d'un particulier.
À utiliser pour **apprendre**, pas pour spéculer.

---

*Construit par [Zakaria Rahal](https://github.com/Zakariarhl01) — étudiant Dev IA & Data.*
