import streamlit as st
import pandas as pd
import plotly.express as px
from utils import muotoile_luku, laske_painotettu_neliohinta

def render_kartta(df: pd.DataFrame, alueet_df: pd.DataFrame):
    st.write("Tarkastele koko Suomen alueita ja hintajakaumaa interaktiivisella kartalla.")
    
    df_2025 = df[df["year"] == 2025]
    tilastot_2025 = []
    for koodi, ryhma in df_2025.groupby("code"):
        tilastot_2025.append({
            "code": koodi,
            "price": laske_painotettu_neliohinta(ryhma),
            "trades": ryhma["trades"].sum()
        })
    df_tilastot = pd.DataFrame(tilastot_2025)

    karttadata = alueet_df[["label", "city", "lat", "lon"]].merge(df_tilastot, on="code").dropna(subset=["price"])

    hakusana = st.text_input("Hae aluetta tai kaupunkia:", placeholder="Kirjoita esim. Mikkeli, 50100, Tampere...")
    if hakusana:
        karttadata = karttadata[
            karttadata["label"].str.contains(hakusana, case=False, na=False) |
            karttadata["city"].str.contains(hakusana, case=False, na=False)
        ]

    fig_kartta = px.scatter_map(
        karttadata,
        lat="lat",
        lon="lon",
        color="price",
        size="trades",
        hover_name="label",
        hover_data={"price": ":.0f", "trades": True, "lat": False, "lon": False},
        color_continuous_scale="Teal",
        map_style="carto-positron",
        zoom=4.5,
        height=620
    )
    st.plotly_chart(fig_kartta, use_container_width=True)

    if not karttadata.empty:
        kallein_idx = karttadata["price"].idxmax()
        halvin_idx = karttadata["price"].idxmin()

        hk1, hk2 = st.columns(2)
        hk1.metric("Korkein neliöhinta", f"{muotoile_luku(karttadata.loc[kallein_idx, 'price'])} €/m²", karttadata.loc[kallein_idx, 'label'])
        hk2.metric("Edullisin neliöhinta", f"{muotoile_luku(karttadata.loc[halvin_idx, 'price'])} €/m²", karttadata.loc[halvin_idx, 'label'])

    taulukko_nakyma = karttadata[["label", "price", "trades"]].sort_values("price", ascending=False).rename(
        columns={"label": "Postinumeroalue", "price": "Neliöhinta (€/m²)", "trades": "Kaupat (2025)"}
    )
    st.dataframe(taulukko_nakyma, hide_index=True, use_container_width=True)