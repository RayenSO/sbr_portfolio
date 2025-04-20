import streamlit as st
from src.data_loader import load_data

st.title("🧪 Test du chargement des données")

data = load_data()

# Helper pour affichage formaté
def format_dates(df, date_columns):
    df_copy = df.copy()
    for col in date_columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].dt.strftime('%d/%m/%Y')
    return df_copy

st.subheader("Transactions")
st.dataframe(format_dates(data["transactions"], ["Date"]))

st.subheader("Prix des titres (long format)")
st.dataframe(format_dates(data["prices"], ["Date"]))

st.subheader("Benchmark")
st.dataframe(format_dates(data["benchmark"], ["Date"]))

st.subheader("Jours de marché")
st.dataframe(format_dates(data["jours_marche"], ["Date"]))
