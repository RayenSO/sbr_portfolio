import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.compute_engine import compute_daily_report

st.title("📆 Vue Quotidienne du Portefeuille")

data = load_data()
report = compute_daily_report(
    transactions=data["transactions"],
    prices=data["prices"],
    jours_marche=data["jours_marche"],
    capital_initial=100_000,
    taux_cash=0.03
)

# Sélecteur de date
dates_disponibles = report["Date"].dt.strftime("%d/%m/%Y").tolist()
selected_str = st.selectbox("📅 Choisissez une date", dates_disponibles[::-1])  # ordre décroissant
selected_date = pd.to_datetime(selected_str, format="%d/%m/%Y")

# Données du jour sélectionné
row = report[report["Date"] == selected_date].iloc[0]
st.markdown("### 📊 Résumé du jour")
st.markdown(f"""
- 🟢 **Achats** : {row["Nombre d'Achats"]}
- 🔴 **Ventes** : {row["Nombre de Ventes"]}
- 🟠 **Shorts** : {row["Nombre de Shorts"]}
- 🟣 **Rachats** : {row["Nombre de Rachats"]}
- 💸 **Frais** : {row['Frais']:.2f} USD
- 💰 **Cash** : {row['Cash']:.2f} USD
- 📈 **Valeur Liquidative (VL)** : **{row['Valeur Liquidative']:.2f} USD**
""")

# Helper pour affichage formaté (Performance du titre en vert, Souss-performance en rouge)
def get_variation_colors(col):
    return [
        "color: green" if isinstance(val, float) and val > 0
        else "color: red" if isinstance(val, float) and val < 0
        else ""
        for val in col
    ]


# Composition du portefeuille
def get_portfolio_compo(report, prices, jours_marche, date):
    row = report[report["Date"] == date]
    if row.empty:
        return pd.DataFrame()

    positions = row.iloc[0]["Positions"]
    if not positions:
        return pd.DataFrame()

    net_position = pd.Series(positions)
    prix_date = prices[prices["Date"] == date].set_index("Ticker")["Prix"]
    df = net_position.to_frame("Nombre de Titres").join(prix_date, how="left")
    df["Valeur"] = df["Nombre de Titres"] * df["Prix"]

    # Variation par rapport à la veille
    veille = jours_marche[jours_marche["Date"] < date]["Date"].max()
    if pd.isna(veille):
        df["Variation vs veille"] = "N/A"
    else:
        prix_veille = prices[prices["Date"] == veille].set_index("Ticker")["Prix"]
        df["Variation vs veille"] = (
            (df["Prix"] - prix_veille) / prix_veille * 100
        ).round(2).fillna("N/A")


    # 🔧 Corriger ici
    df = df.reset_index().rename(columns={"index": "Ticker"})
    df = df[["Ticker", "Nombre de Titres", "Prix", "Valeur", "Variation vs veille"]]
    return df[df["Nombre de Titres"] != 0]


st.markdown("### 🧾 Composition du portefeuille")
compo = get_portfolio_compo(
    report=report,
    prices=data["prices"],
    jours_marche=data["jours_marche"],
    date=selected_date
)
st.dataframe(
    compo.style
        .format({
            "Prix": "{:.2f}",
            "Valeur": "{:.2f}",
            "Variation vs veille": lambda x: f"{x}%" if isinstance(x, float) else x
        })
        .apply(get_variation_colors, subset=["Variation vs veille"]),
            hide_index=True
)
