"""
Suomen asuntomarkkinoiden analytiikka – Pääohjelma.
"""
import streamlit as st
from utils import lataa_asuntodata
from views.analyysi import render_alueanalyysi
from views.vertailu import render_vertailu
from views.kartta import render_kartta
from views.laskuri import render_laskuri

# 1. Sivun asetukset
st.set_page_config(
    page_title="Suomen asuntomarkkinoiden analytiikka",
    page_icon="🏠",
    layout="wide"
)

# 2. Datan alustus
df = lataa_asuntodata()
alueet_df = df.drop_duplicates(subset=["code"]).set_index("code")
aluelabelit = dict(zip(alueet_df.index, alueet_df["label"]))
postinumerot = list(alueet_df.index)

# Istuntokohtaiset oletukset laskurille
if "growth" not in st.session_state:
    st.session_state["growth"] = 1.5
if "area" not in st.session_state:
    st.session_state["area"] = aluelabelit.get("50100", "50100 Mikkeli Keskus")

# 3. Yläpalkki ja otsikointi
st.title("Suomen asuntomarkkinoiden analytiikka")
st.markdown("Interaktiivinen katsaus toteutuneisiin asuntokauppoihin, hintatrendeihin ja aluetilastoihin.")

# 4. Välilehtien reititys
tab1, tab2, tab3, tab4 = st.tabs([
    "Alueanalyysi", 
    "Aluevertailu", 
    "Hintakartta", 
    "Sijoituslaskuri"
])

with tab1:
    render_alueanalyysi(df, postinumerot, aluelabelit)

with tab2:
    render_vertailu(df, postinumerot, aluelabelit)

with tab3:
    render_kartta(df, alueet_df)

with tab4:
    render_laskuri()

st.divider()
st.caption(
    "Datalähde: Tilastokeskus, vanhojen osakeasuntojen hinnat (taulukko 13mu), CC BY 4.0. "
    "Merkintä '–' tarkoittaa, että Tilastokeskus ei julkaise arvoa liian vähäisen kauppamäärän vuoksi."
)