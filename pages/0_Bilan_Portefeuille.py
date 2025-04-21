import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px
from src.data_loader import load_data
from src.compute_engine import compute_daily_report

st.title("📘 Bilan Global du Portefeuille (Depuis l'inception)")

# --- Chargement des données ---
data = load_data()
report = compute_daily_report(
    transactions=data["transactions"],
    prices=data["prices"],
    jours_marche=data["jours_marche"],
    capital_initial=100_000,
    taux_cash=0.03
)

# --- Préparation des données (depuis 16 janvier 2024) ---
report = report.sort_values("Date")
vl_series = report[["Date", "Valeur Liquidative"]].copy()
vl_series["Rendement_Ptf"] = vl_series["Valeur Liquidative"].pct_change()

benchmark = data["benchmark"].copy()
benchmark = benchmark.sort_values("Date")
benchmark["Rendement_Benchmark"] = benchmark["Prix"].pct_change()

# --- Fusion des rendements ---
merged = pd.merge(
    vl_series[["Date", "Rendement_Ptf"]],
    benchmark[["Date", "Rendement_Benchmark"]],
    on="Date",
    how="inner"
).dropna()

# --- Calcul des KPIs ---
perf_ptf = vl_series["Valeur Liquidative"].iloc[-1] / vl_series["Valeur Liquidative"].iloc[0] - 1
perf_bench = benchmark["Prix"].iloc[-1] / benchmark["Prix"].iloc[0] - 1

vol_ptf = merged["Rendement_Ptf"].std() * np.sqrt(252)
vol_bench = merged["Rendement_Benchmark"].std() * np.sqrt(252)
sharpe_ptf = merged["Rendement_Ptf"].mean() / merged["Rendement_Ptf"].std()

# Sortino
downside = merged["Rendement_Ptf"][merged["Rendement_Ptf"] < 0]
downside_risk = downside.std() * np.sqrt(252)
sortino = merged["Rendement_Ptf"].mean() / downside_risk if downside_risk != 0 else np.nan

# Treynor & Beta & R²
X = merged["Rendement_Benchmark"].values.reshape(-1, 1)
y = merged["Rendement_Ptf"].values
reg = LinearRegression().fit(X, y)
beta = reg.coef_[0]
r_squared = reg.score(X, y)
treynor = merged["Rendement_Ptf"].mean() / beta if beta != 0 else np.nan

# Corrélation
correlation = merged["Rendement_Ptf"].corr(merged["Rendement_Benchmark"])

# Tracking Error + Info Ratio
tracking_error = (merged["Rendement_Ptf"] - merged["Rendement_Benchmark"]).std() * np.sqrt(252)
info_ratio = (perf_ptf - perf_bench) / tracking_error if tracking_error != 0 else np.nan

# Max Drawdown
rolling_max = vl_series["Valeur Liquidative"].cummax()
drawdowns = vl_series["Valeur Liquidative"] / rolling_max - 1
max_drawdown = drawdowns.min()

# --- Affichage métriques compact ---
def custom_metric(label, value):
    return f"<div style='font-size:13px; line-height:1.4'><b>{label}</b><br><span style='font-size:15px'>{value}</span></div>"

st.markdown("### 📊 Indicateurs de Performance Depuis le 16 janvier 2024")
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
    st.markdown(custom_metric("Tracking Error", f"{tracking_error:.2%}"), unsafe_allow_html=True)

# --- Graphique VL vs Benchmark ---
st.markdown("### 📈 Évolution VL vs Benchmark (normalisée)")

# Normalisation à 100
vl_series["VL Normalisée"] = vl_series["Valeur Liquidative"] / vl_series["Valeur Liquidative"].iloc[0] * 100
benchmark["Benchmark Normalisé"] = benchmark["Prix"] / benchmark["Prix"].iloc[0] * 100

df_plot = pd.merge(
    vl_series[["Date", "VL Normalisée"]],
    benchmark[["Date", "Benchmark Normalisé"]],
    on="Date",
    how="inner"
)

fig = px.line(df_plot, x="Date", y=["VL Normalisée", "Benchmark Normalisé"],
              labels={"value": "Valeur (base 100)", "Date": "Date"},
              title="Évolution comparée VL vs Benchmark")
st.plotly_chart(fig, use_container_width=True)
