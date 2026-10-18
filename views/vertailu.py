import streamlit as st
import pandas as pd
import plotly.express as px
from utils import TALOTYYPIT, muotoile_luku, laske_vuosittainen_sarja

def render_vertailu(df: pd.DataFrame, postinumerot: list, aluelabelit: dict):
    v1, v2, v3 = st.columns(3)
    alue_a = v1.selectbox("Alue A", postinumerot, postinumerot.index("00530") if "00530" in postinumerot else 0, format_func=aluelabelit.get)
    alue_b = v2.selectbox("Alue B", postinumerot, postinumerot.index("33100") if "33100" in postinumerot else 1, format_func=aluelabelit.get)
    valittu_t = v3.selectbox("Talotyyppi", list(TALOTYYPIT.keys()), 1, format_func=TALOTYYPIT.get)

    trendit = pd.DataFrame({
        aluelabelit[alue_a]: laske_vuosittainen_sarja(df[(df["code"] == alue_a) & (df["type"] == valittu_t)]),
        aluelabelit[alue_b]: laske_vuosittainen_sarja(df[(df["code"] == alue_b) & (df["type"] == valittu_t)])
    })

    hinta_a = trendit[aluelabelit[alue_a]].get(2025)
    hinta_b = trendit[aluelabelit[alue_b]].get(2025)

    m1, m2 = st.columns(2)
    ero_pros = ((hinta_a - hinta_b) / hinta_b * 100) if hinta_a and hinta_b else None
    m1.metric(aluelabelit[alue_a], f"{muotoile_luku(hinta_a)} €/m²", f"{muotoile_luku(ero_pros, 1)} % vs. Alue B" if ero_pros else None)
    
    ero_pros_b = ((hinta_b - hinta_a) / hinta_a * 100) if hinta_a and hinta_b else None
    m2.metric(aluelabelit[alue_b], f"{muotoile_luku(hinta_b)} €/m²", f"{muotoile_luku(ero_pros_b, 1)} % vs. Alue A" if ero_pros_b else None)

    fig_vertailu = px.line(
        trendit, 
        markers=True, 
        title=f"Historiallinen hintatrendi: {TALOTYYPIT[valittu_t]}",
        labels={"index": "Vuosi", "value": "Neliöhinta (€/m²)", "variable": "Alue"}
    )
    st.plotly_chart(fig_vertailu, use_container_width=True)