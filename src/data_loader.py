import pandas as pd
import streamlit as st

@st.cache_data
def load_data(filepath: str = "data/data.xlsx") -> dict:
    try:
        # Chargement des feuilles
        transactions = pd.read_excel(filepath, sheet_name="Transactions")
        benchmark = pd.read_excel(filepath, sheet_name="Benchmark")
        prices = pd.read_excel(filepath, sheet_name="Prix_Titres")
        jours_marche = pd.read_excel(filepath, sheet_name="Jour_Marche")

        # Nettoyage de base
        transactions["Date"] = pd.to_datetime(transactions["Date"])
        benchmark["Date"] = pd.to_datetime(benchmark["Date"])
        prices["Date"] = pd.to_datetime(prices["Date"])
        jours_marche["Date"] = pd.to_datetime(jours_marche["Date"])

        # Format long pour les prix
        prices_long = prices.melt(id_vars=["Date"], var_name="Ticker", value_name="Prix")

        return {
            "transactions": transactions,
            "benchmark": benchmark,
            "prices": prices_long,
            "jours_marche": jours_marche
        }

    except FileNotFoundError:
        st.error("Fichier `data.xlsx` non trouvé dans le dossier `data/`.")
        st.stop()
    except ValueError as e:
        st.error(f"Erreur lors du chargement des feuilles Excel : {e}")
        st.stop()
