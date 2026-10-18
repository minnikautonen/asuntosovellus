import streamlit as st
import pandas as pd
import plotly.express as px
from utils import muotoile_luku

def render_laskuri():
    st.write("Laske asuntosijoituksen tuotto-odotus, kassavirta ja kokonaisarvonnousu.")
    
    c1, c2, c3 = st.columns(3)
    ostohinta = c1.number_input("Asunnon ostohinta (€)", min_value=10_000, value=150_000, step=5_000)
    vuokra_kk = c2.number_input("Vuokra (€/kk)", min_value=100, value=750, step=25)
    vastike_kk = c3.number_input("Hoitovastike (€/kk)", min_value=0, value=180, step=10)

    c_aika1, c_aika2 = st.columns(2)
    pitoaika_vuotta = c_aika1.number_input("Omistusaika (vuotta)", min_value=1, max_value=40, value=10)
    oletettu_kasvu = c_aika2.number_input(
        "Vuotuinen arvonnousu (%/v)", 
        value=float(round(st.session_state.get("growth", 1.5), 1)), 
        step=0.1
    )
    st.caption(f"Arvonnousuoletus esitäytetty alueen {st.session_state.get('area', '')} toteutuneesta hintakehityksestä.")

    vuosikassavirta = (vuokra_kk - vastike_kk) * 12
    tuleva_arvo = ostohinta * ((1 + oletettu_kasvu / 100) ** pitoaika_vuotta)
    arvonnousu_yht = tuleva_arvo - ostohinta
    kokonaistuotto = arvonnousu_yht + (vuosikassavirta * pitoaika_vuotta)

    bruttotuotto = (vuokra_kk * 12 / ostohinta) * 100 if ostohinta > 0 else 0
    nettotuotto = (vuosikassavirta / ostohinta) * 100 if ostohinta > 0 else 0

    met1, met2, met3, met4 = st.columns(4)
    met1.metric("Bruttovuokratuotto", f"{muotoile_luku(bruttotuotto, 1)} %")
    met2.metric("Nettovuokratuotto", f"{muotoile_luku(nettotuotto, 1)} %")
    met3.metric("Arvonnousu", f"{muotoile_luku(arvonnousu_yht)} €")
    met4.metric("Kokonaistuotto", f"{muotoile_luku(kokonaistuotto)} €")

    vuositaulukko = pd.DataFrame({
        "Vuosi": list(range(pitoaika_vuotta + 1)),
        "Asunnon ennustettu arvo": [ostohinta * ((1 + oletettu_kasvu / 100) ** y) for y in range(pitoaika_vuotta + 1)],
        "Kertynyt kassavirta": [vuosikassavirta * y for y in range(pitoaika_vuotta + 1)]
    })

    fig_simulaatio = px.line(
        vuositaulukko, 
        x="Vuosi", 
        y=["Asunnon ennustettu arvo", "Kertynyt kassavirta"],
        markers=True, 
        title="Omaisuuserän arvon ja kumulatiivisen kassavirran kehitys",
        labels={"value": "Euroa (€)", "variable": "Mittari"}
    )
    st.plotly_chart(fig_simulaatio, use_container_width=True)