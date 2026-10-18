import streamlit as st
import pandas as pd
import plotly.express as px
from utils import TALOTYYPIT, muotoile_luku, laske_painotettu_neliohinta, laske_vuosittainen_sarja

def render_alueanalyysi(df: pd.DataFrame, postinumerot: list, aluelabelit: dict):
    col_alue, col_talotyyppi, col_vuodet = st.columns([1.2, 1.4, 1.4])
    
    oletus_idx = postinumerot.index("50100") if "50100" in postinumerot else 0
    valittu_koodi = col_alue.selectbox(
        "Postinumeroalue",
        options=postinumerot,
        index=oletus_idx,
        format_func=aluelabelit.get
    )
    valitut_tyypit = col_talotyyppi.multiselect(
        "Talotyypit",
        options=list(TALOTYYPIT.keys()),
        default=list(TALOTYYPIT.keys()),
        format_func=TALOTYYPIT.get
    ) or list(TALOTYYPIT.keys())
    
    alkuvuosi, loppuvuosi = col_vuodet.slider(
        "Tarkastelujakso",
        min_value=2015,
        max_value=2025,
        value=(2015, 2025)
    )

    suodatettu = df[
        (df["code"] == valittu_koodi) & 
        (df["type"].isin(valitut_tyypit)) & 
        (df["year"].between(alkuvuosi, loppuvuosi))
    ]

    aikasarja = laske_vuosittainen_sarja(suodatettu)
    alkuhinta = aikasarja.get(alkuvuosi)
    loppuhinta = aikasarja.get(loppuvuosi)
    muutos_pros = (loppuhinta - alkuhinta) / alkuhinta * 100 if alkuhinta and loppuhinta else float("nan")

    if alkuhinta and loppuhinta and alkuhinta > 0:
        vuosiero = max(1, loppuvuosi - alkuvuosi)
        vuotuinen_kasvu = ((loppuhinta / alkuhinta) ** (1 / vuosiero) - 1) * 100
        st.session_state["growth"] = vuotuinen_kasvu
    st.session_state["area"] = aluelabelit.get(valittu_koodi, "")

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Tarkastelujakso", f"{alkuvuosi}–{loppuvuosi}")
    kpi2.metric("Keskimääräinen neliöhinta", f"{muotoile_luku(laske_painotettu_neliohinta(suodatettu))} €/m²")
    kpi3.metric("Kauppamäärä yhteensä", f"{muotoile_luku(suodatettu['trades'].sum())} kpl")

    if pd.notnull(muutos_pros):
        st.info(
            f"Alueen keskimääräinen neliöhinta on muuttunut **{muotoile_luku(muutos_pros, 1)} %** "
            f"vuosien {alkuvuosi} ja {loppuvuosi} välillä ({muotoile_luku(alkuhinta)} → {muotoile_luku(loppuhinta)} €/m²)."
        )

    kuvaaja_data = suodatettu.copy()
    kuvaaja_data["tyyppi_nimi"] = kuvaaja_data["type"].map(TALOTYYPIT)

    g1, g2 = st.columns(2)
    fig_hinta = px.line(
        kuvaaja_data, 
        x="year", 
        y="price", 
        color="tyyppi_nimi", 
        markers=True, 
        title="Neliöhinnan kehitys (€/m²)",
        labels={"year": "Vuosi", "price": "Neliöhinta (€/m²)", "tyyppi_nimi": "Talotyyppi"}
    )
    g1.plotly_chart(fig_hinta, use_container_width=True)

    fig_kaupat = px.bar(
        kuvaaja_data, 
        x="year", 
        y="trades", 
        color="tyyppi_nimi", 
        barmode="group", 
        title="Toteutuneet kaupat (kpl)",
        labels={"year": "Vuosi", "trades": "Kaupat (kpl)", "tyyppi_nimi": "Talotyyppi"}
    )
    g2.plotly_chart(fig_kaupat, use_container_width=True)