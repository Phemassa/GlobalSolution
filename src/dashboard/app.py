import streamlit as st

st.set_page_config(page_title="GS Climate Monitor", layout="wide")

st.title("Global Solution 2026.1")
st.subheader("Monitoramento Climatico Espacial - MVP")

col1, col2, col3 = st.columns(3)
col1.metric("Status pipeline", "Bootstrapped")
col2.metric("Modelo ML", "Pending")
col3.metric("Modulo CV", "Pending")

st.info("Scaffold inicial pronto. Proximo passo: conectar dados e modelo baseline.")
