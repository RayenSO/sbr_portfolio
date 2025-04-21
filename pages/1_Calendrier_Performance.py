import streamlit as st
import pandas as pd
import numpy as np
from src.data_loader import load_data
from src.compute_engine import compute_daily_report

st.title("📆 Tableau de Bord Mensuel")

# --- Chargement des données ---
data = load_data()
report = compute_daily_report(
    transactions=data["transactions"],
    prices=data["prices"],
    jours_marche=data["jours_marche"],
    capital_initial=100_000,
    taux_cash=0.03
)

benchmark = data["benchmark"].copy()
benchmark["Mois"] = benchmark["Date"].dt.to_period("M")

report["Mois"] = report["Date"].dt.to_period("M")

# --- Calcul perf mensuelle portefeuille ---
perf_ptf = (
    report.groupby("Mois")["Valeur Liquidative"]
    .agg(["first", "last"])
    .assign(Perf_Ptf=lambda df: (df["last"] / df["first"] - 1).round(4))
    .reset_index()[["Mois", "Perf_Ptf"]]
)

# --- Calcul perf mensuelle benchmark ---
perf_bench = (
    benchmark.groupby("Mois")["Prix"]
    .agg(["first", "last"])
    .assign(Perf_Bench=lambda df: (df["last"] / df["first"] - 1).round(4))
    .reset_index()[["Mois", "Perf_Bench"]]
)

# --- Fusion des deux performances ---
perf_mois = pd.merge(perf_ptf, perf_bench, on="Mois", how="outer").dropna()
perf_mois["Année"] = perf_mois["Mois"].dt.year
perf_mois["Mois_Num"] = perf_mois["Mois"].dt.month
perf_mois["Mois_Nom"] = perf_mois["Mois"].dt.strftime("%b")

# --- Construction tableau type calendrier ---
mois_ordre = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

table_rows = []
for annee in sorted(perf_mois["Année"].unique()):
    ligne_ptf = {"Année": f"{annee} - Ptf"}
    ligne_bench = {"Année": f"{annee} - Bench"}
    for mois in mois_ordre:
        perf_row = perf_mois[(perf_mois["Année"] == annee) & (perf_mois["Mois_Nom"] == mois)]
        if not perf_row.empty:
            ligne_ptf[mois] = perf_row["Perf_Ptf"].values[0]
            ligne_bench[mois] = perf_row["Perf_Bench"].values[0]
        else:
            ligne_ptf[mois] = ""
            ligne_bench[mois] = ""
    table_rows.extend([ligne_ptf, ligne_bench])

df_perf = pd.DataFrame(table_rows).set_index("Année")
df_perf_clean = df_perf.replace("", np.nan)

# --- Fonction de coloration conditionnelle ---
def color_perf(val):
    if isinstance(val, float):
        return "color: green" if val > 0 else "color: red"
    return ""

# --- Affichage ---
st.markdown("### 📊 Performance mensuelle")
st.markdown("### SBR US BALANCED POWER vs S&P500 exFinancials & Real Estate")
st.dataframe(
    df_perf_clean.style
        .format("{:.2%}")
        .applymap(color_perf),
    use_container_width=True)

