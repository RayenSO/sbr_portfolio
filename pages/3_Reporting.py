import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.compute_engine import compute_daily_report
from sklearn.linear_model import LinearRegression
import numpy as np
import plotly.express as px


st.title("📅 Reporting Mensuel du Portefeuille")

# Charger les données
data = load_data()
tickers_info = data["transactions"].drop_duplicates(subset=["Ticker"]).set_index("Ticker")["GICS Class"]
report = compute_daily_report(
    transactions=data["transactions"],
    prices=data["prices"],
    jours_marche=data["jours_marche"],
    capital_initial=100_000,
    taux_cash=0.03
)

def custom_metric(label, value):
    return f"<div style='font-size:13px; line-height:1.4'><b>{label}</b><br><span style='font-size:15px'>{value}</span></div>"

# Créer la liste des mois disponibles (périodes)
report["Mois"] = report["Date"].dt.to_period("M")
mois_disponibles = sorted(report["Mois"].unique(), reverse=True)

# Sélecteur du mois
selected_period = st.selectbox("📆 Sélectionnez un mois :", mois_disponibles)
selected_month = selected_period.to_timestamp()  # Date du 1er jour du mois

# Filtrer les données du mois
report_mois = report[report["Mois"] == selected_period]
if report_mois.empty:
    st.warning("Aucune donnée disponible pour ce mois.")
    st.stop()

# Dernier jour de marché du mois
dernier_jour = report_mois["Date"].max()
st.markdown(f"### 🔎 Analyse du mois : **{selected_period.strftime('%B %Y')}**")
st.markdown(f"- 🗓️ Dernier jour de marché du mois : **{dernier_jour.strftime('%d/%m/%Y')}**")


vl_series = report_mois["Valeur Liquidative"]
rolling_max = vl_series.cummax()
drawdowns = (vl_series / rolling_max) - 1
max_drawdown = drawdowns.min()

def get_position_a_date(report, prices, date):
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

    valeur_totale = df["Valeur"].sum()
    df["Poids %"] = (df["Valeur"] / valeur_totale * 100).round(2)

    df = df.reset_index().rename(columns={"index": "Ticker"})
    df = df[["Ticker", "Nombre de Titres", "Prix", "Valeur", "Poids %"]]
    return df[df["Nombre de Titres"] != 0]

st.markdown("### 🧾 Position du portefeuille à la fin du mois")

position_fin_mois = get_position_a_date(
    report=report,
    prices=data["prices"],
    date=dernier_jour
)
position_fin_mois["GICS"] = position_fin_mois["Ticker"].map(tickers_info)
repartition_gics = position_fin_mois.groupby("GICS")["Poids %"].sum().reset_index()


st.dataframe(
    position_fin_mois.style.format({
        "Prix": "{:.2f}",
        "Valeur": "{:.2f}",
        "Poids %": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# Préparation des rendements journaliers
report_mois = report_mois.sort_values("Date")
report_mois["Rendement_Ptf"] = report_mois["Valeur Liquidative"].pct_change()

benchmark_mois = data["benchmark"]
benchmark_mois["Mois"] = benchmark_mois["Date"].dt.to_period("M")
benchmark_mois = benchmark_mois[benchmark_mois["Mois"] == selected_period].copy()
benchmark_mois = benchmark_mois.sort_values("Date")
benchmark_mois["Rendement_Benchmark"] = benchmark_mois["Prix"].pct_change()

merged = pd.merge(
    report_mois[["Date", "Rendement_Ptf"]],
    benchmark_mois[["Date", "Rendement_Benchmark"]],
    on="Date",
    how="inner"
).dropna()

perf_ptf = (report_mois["Valeur Liquidative"].iloc[-1] / report_mois["Valeur Liquidative"].iloc[0]) - 1
perf_bench = (benchmark_mois["Prix"].iloc[-1] / benchmark_mois["Prix"].iloc[0]) - 1

vol_ptf = merged["Rendement_Ptf"].std() * np.sqrt(252)
vol_bench = merged["Rendement_Benchmark"].std() * np.sqrt(252)

sharpe_ptf = (merged["Rendement_Ptf"].mean() - 0.0475)/ merged["Rendement_Ptf"].std()

# Régression pour Beta et R²
X = merged["Rendement_Benchmark"].values.reshape(-1, 1)
y = merged["Rendement_Ptf"].values
reg = LinearRegression().fit(X, y)
beta = reg.coef_[0]
r_squared = reg.score(X, y)
correlation = merged["Rendement_Ptf"].corr(merged["Rendement_Benchmark"])
# Sortino ratio
downside = merged["Rendement_Ptf"][merged["Rendement_Ptf"] < 0]
downside_risk = downside.std() * np.sqrt(252)
sortino = merged["Rendement_Ptf"].mean() / downside_risk if downside_risk != 0 else np.nan

# Treynor ratio (rf = 0 ici)
treynor = merged["Rendement_Ptf"].mean() / beta if beta != 0 else np.nan

# Tracking error
diff = merged["Rendement_Ptf"] - merged["Rendement_Benchmark"]
tracking_error = diff.std() * np.sqrt(252)

# Information ratio
info_ratio = (perf_ptf - perf_bench) / tracking_error if tracking_error != 0 else np.nan
st.markdown("### 📊 Indicateurs de performance")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(custom_metric("Perf. Portefeuille", f"{perf_ptf:.2%}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Volatilité Ptf", f"{vol_ptf:.2%}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Sharpe", f"{sharpe_ptf:.2f}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Sortino", f"{sortino:.2f}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Max Drawdown", f"{max_drawdown:.2%}"), unsafe_allow_html=True)

with col2:
    st.markdown(custom_metric("Perf. Benchmark", f"{perf_bench:.2%}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Volatilité Bench", f"{vol_bench:.2%}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Bêta", f"{beta:.2f}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Corrélation", f"{correlation:.2f}"), unsafe_allow_html=True)
    st.markdown(custom_metric("R²", f"{r_squared:.2f}"), unsafe_allow_html=True)

with col3:
    st.markdown(custom_metric("Treynor", f"{treynor:.2f}"), unsafe_allow_html=True)
    st.markdown(custom_metric("Info Ratio", f"{info_ratio:.2f}"), unsafe_allow_html=True)

st.markdown("### 🧩 Répartition du portefeuille")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Par Ticker**")
    fig1 = px.pie(
        position_fin_mois,
        names="Ticker",
        values="Poids %",
        hole=0.3
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("**Par GICS Class**")
    fig2 = px.pie(
        repartition_gics,
        names="GICS",
        values="Poids %",
        hole=0.3
    )
    st.plotly_chart(fig2, use_container_width=True)


st.markdown("### 📈 Évolution SBR US BALANCED POWER vs S&P500 exFinancials & Real Estate")

# Préparer les deux séries
vl_norm = report_mois[["Date", "Valeur Liquidative"]].copy()
benchmark_norm = benchmark_mois[["Date", "Prix"]].copy()

if not vl_norm.empty and not benchmark_norm.empty:
    base_vl = vl_norm["Valeur Liquidative"].iloc[0]
    base_bench = benchmark_norm["Prix"].iloc[0]

    vl_norm["VL normalisée"] = vl_norm["Valeur Liquidative"] / base_vl * 100
    benchmark_norm["Benchmark normalisé"] = benchmark_norm["Prix"] / base_bench * 100

    df_plot = pd.merge(
        vl_norm[["Date", "VL normalisée"]],
        benchmark_norm[["Date", "Benchmark normalisé"]],
        on="Date",
        how="inner"
    )

    fig = px.line(df_plot, x="Date", y=["VL normalisée", "Benchmark normalisé"],
                  labels={"value": "Valeur $ (base 100)", "Date": "Date"},
                  title="Évolution comparée VL vs Benchmark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Pas assez de données pour tracer les courbes.")
