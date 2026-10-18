"""
Yhteiset apufunktiot datan lataamiseen, painotettuun laskentaan ja lukumuotoiluihin.
"""
import json
from pathlib import Path
import pandas as pd
import streamlit as st

DATAPOLKU = Path(__file__).parent / "data" / "housing.json"
VUODET = list(range(2015, 2026))

TALOTYYPIT = {
    "yksio": "Kerrostalo yksiöt",
    "kaksio": "Kerrostalo kaksiot",
    "kolmio": "Kerrostalo kolmiot+",
    "rivitalo": "Rivitalot yhteensä",
}


def muotoile_luku(arvo, desimaalit=0) -> str:
    """Muotoilee luvun suomalaisen standardin mukaan (välilyönti tuhaterottimena)."""
    if pd.isna(arvo):
        return "–"
    return f"{arvo:,.{desimaalit}f}".replace(",", " ").replace(".", ",")


@st.cache_data
def lataa_asuntodata() -> pd.DataFrame:
    """Lataa JSON-tiedoston ja luo normalisoidun pitkän DataFrame-taulukon."""
    if not DATAPOLKU.exists():
        st.error(f"Datalähdettä ei löytynyt polusta: {DATAPOLKU}")
        st.stop()

    data_json = json.loads(DATAPOLKU.read_text(encoding="utf-8"))
    rivit = []

    for alue in data_json:
        koodi = alue["code"]
        nimi = alue["name"]
        kunta = alue["city"]
        lat = alue["lat"]
        lon = alue["lon"]

        for t_avain in TALOTYYPIT:
            hinnat = alue["p"].get(t_avain, [])
            kaupat = alue["n"].get(t_avain, [])

            for indeksi, vuosi in enumerate(VUODET):
                hinta = hinnat[indeksi] if indeksi < len(hinnat) else None
                kauppa = kaupat[indeksi] if indeksi < len(kaupat) else 0

                rivit.append({
                    "code": koodi,
                    "name": nimi,
                    "city": kunta,
                    "lat": lat,
                    "lon": lon,
                    "type": t_avain,
                    "year": vuosi,
                    "price": hinta,
                    "trades": kauppa or 0,
                    "label": f"{koodi} {nimi}"
                })

    return pd.DataFrame(rivit)


def laske_painotettu_neliohinta(df_otos: pd.DataFrame) -> float:
    """Laskee kauppamäärillä painotetun keskimääräisen neliöhinnan."""
    validit = df_otos.dropna(subset=["price"])
    if validit.empty:
        return float("nan")

    kaupat_sum = validit["trades"].sum()
    if kaupat_sum > 0:
        return (validit["price"] * validit["trades"]).sum() / kaupat_sum
    return validit["price"].mean()


def laske_vuosittainen_sarja(df_otos: pd.DataFrame) -> pd.Series:
    """Laskee kunkin vuoden painotetun neliöhinnan ilman apply-varoituksia."""
    tulokset = {}
    for vuosi, ryhma in df_otos.groupby("year"):
        tulokset[vuosi] = laske_painotettu_neliohinta(ryhma)
    return pd.Series(tulokset)