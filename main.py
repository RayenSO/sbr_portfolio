import streamlit as st

st.set_page_config(page_title="Accueil - SBR US BALANCED Power", layout="wide")

# --- Logo ou image d'en-tête ---
st.image("images/sbr_fund_banner.png", use_container_width=True)

# --- Titre / Présentation ---
st.title("💼 SBR US BALANCED Power")
st.markdown("""
Bienvenue sur le tableau de bord du fonds **SBR US BALANCED Power**, un portefeuille diversifié basé sur des actions américaines avec une approche équilibrée entre **croissance et prudence**.

L’objectif est de **suivre et piloter finement les performances** du portefeuille au quotidien, mois par mois, et sur l'ensemble de sa vie depuis son lancement (16 janvier 2024).
""")

st.markdown("### 📂 Navigation")

# --- Liens vers les autres pages ---
col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/2_Portfolio_Daily.py", label="📆 Vue quotidienne")
    st.page_link("pages/3_Reporting.py", label="📊 Reporting mensuel")

with col2:
    st.page_link("pages/0_Bilan_Portefeuille.py", label="📘 Bilan global")
    st.page_link("pages/1_Calendrier_Performance.py", label="📈 Calendrier des performances")
