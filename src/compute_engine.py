import pandas as pd
import numpy as np

def compute_daily_report(transactions, prices, jours_marche, capital_initial, taux_cash=0.03):
    jours_marche = jours_marche.sort_values("Date").reset_index(drop=True)
    prices_pivot = prices.pivot(index="Date", columns="Ticker", values="Prix")

    tickers = transactions["Ticker"].unique()
    positions = {ticker: 0 for ticker in tickers}
    cash = capital_initial

    records = []

    for _, row in jours_marche.iterrows():
        date = row["Date"]
        daily_data = {
            "Date": date,
            "Nombre d'Achats": 0,
            "Nombre de Ventes": 0,
            "Nombre de Shorts": 0,
            "Nombre de Rachats": 0,
            "Frais": 0.0,
            "Montant_Investi": 0.0,
            "Montant_Recupere": 0.0,
            "Valeur_Titres": 0.0,
            "Cash": 0.0,
            "Valeur Liquidative": 0.0,
            "Positions": {}  # snapshot des positions du jour
        }

        # Rémunération du cash (252 jours ouvrés/an)
        cash *= (1 + taux_cash / 252)

        tx_jour = transactions[transactions["Date"] == date]
        for _, tx in tx_jour.iterrows():
            ticker = tx["Ticker"]
            nb = tx["Nb actions"]
            prix = tx["Prix local unitaire"]
            frais = tx["Frais"]
            montant = prix * nb + frais
            type_op = tx["Type"].lower()

            if type_op == "achat":
                positions[ticker] += nb
                cash -= montant
                daily_data["Nombre d'Achats"] += 1
                daily_data["Montant_Investi"] += montant

            elif type_op == "vente":
                positions[ticker] -= nb
                cash += prix * nb - frais
                daily_data["Nombre de Ventes"] += 1
                daily_data["Montant_Recupere"] += prix * nb

            elif type_op == "short":
                positions[ticker] -= nb
                cash += prix * nb - frais
                daily_data["Nombre de Shorts"] += 1
                daily_data["Montant_Recupere"] += prix * nb

            elif type_op == "rachat":
                positions[ticker] += nb
                cash -= montant
                daily_data["Nombre de Rachats"] += 1
                daily_data["Montant_Investi"] += montant

            daily_data["Frais"] += frais

        # Valorisation des titres
        prix_jour = prices_pivot.loc[date] if date in prices_pivot.index else {}
        valeur_titres = 0.0
        for ticker, nb_actions in positions.items():
            prix = prix_jour.get(ticker, np.nan)
            if not np.isnan(prix):
                valeur_titres += nb_actions * prix

        daily_data["Valeur_Titres"] = valeur_titres
        daily_data["Cash"] = cash
        daily_data["Valeur Liquidative"] = valeur_titres + cash
        daily_data["Positions"] = positions.copy()  # très important : snapshot

        records.append(daily_data)

    df_report = pd.DataFrame(records)
    return df_report
