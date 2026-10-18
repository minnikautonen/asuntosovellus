"""
Hakee vanhojen osakeasuntojen hintatilastot Tilastokeskuksen PxWeb API:sta
sekä postinumeroiden sijaintitiedot Paavo WFS -rajapinnasta.
"""
import json
import re
from pathlib import Path
import requests

STATFIN_URL = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/ashi/13mu.px"
PAAVO_WFS_URL = (
    "https://geo.stat.fi/geoserver/postialue/wfs"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeName=postialue:pno_2025&outputFormat=application/json&srsName=EPSG:4326"
)

VUODET = [str(vuosi) for vuosi in range(2015, 2026)]
TALOTYYPIT = {"1": "yksio", "2": "kaksio", "3": "kolmio", "5": "rivitalo"}


def muunna_kokonaisluvuksi(arvo):
    try:
        return int(float(arvo))
    except (ValueError, TypeError):
        return None


def hae_hintadata():
    print("Noudetaan Tilastokeskuksen PxWeb-muuttujat...")
    vastaus = requests.get(STATFIN_URL, timeout=60)
    muuttujat = vastaus.json()["variables"][1]
    
    aluekoodit = muuttujat["values"]
    aluenimet = muuttujat["valueTexts"]
    nimi_kartta = dict(zip(aluekoodit, aluenimet))

    tulokset = {}
    erakoko = 300

    print(f"Haetaan hintatiedot erissä ({len(aluekoodit)} aluetta)...")
    for i in range(0, len(aluekoodit), erakoko):
        era = aluekoodit[i:i + erakoko]
        kysely = {
            "query": [
                {"code": "timeperiod_y", "selection": {"filter": "item", "values": VUODET}},
                {"code": muuttujat["code"], "selection": {"filter": "item", "values": era}},
                {"code": "talotyyppi_6_20131021", "selection": {"filter": "item", "values": list(TALOTYYPIT.keys())}},
                {"code": "contentscode", "selection": {"filter": "item", "values": ["keskihinta_aritm_nw", "lkm_julk20"]}}
            ],
            "response": {"format": "json"}
        }

        res = requests.post(STATFIN_URL, json=kysely, timeout=120)
        res.raise_for_status()

        for rivi in res.json().get("data", []):
            vuosi, koodi, talotyyppi = rivi["key"]
            arvot = rivi["values"]
            tulokset.setdefault(koodi, {}).setdefault(talotyyppi, {})[vuosi] = arvot

    return nimi_kartta, tulokset


def hae_koordinaatit():
    print("Haetaan Paavo-rajapinnasta postinumeroalueiden keskipisteet...")
    res = requests.get(PAAVO_WFS_URL, timeout=180)
    keskipisteet = {}

    for feature in res.json().get("features", []):
        geom = feature.get("geometry", {})
        postialue = feature.get("properties", {}).get("posti_alue")

        monikulmiot = geom.get("coordinates", [])
        if geom.get("type") != "MultiPolygon":
            monikulmiot = [monikulmiot]

        pisteet = [p for poly in monikulmiot for p in poly[0]]
        if pisteet and postialue:
            keski_lat = round(sum(p[1] for p in pisteet) / len(pisteet), 3)
            keski_lon = round(sum(p[0] for p in pisteet) / len(pisteet), 3)
            keskipisteet[postialue] = (keski_lat, keski_lon)

    return keskipisteet


def main():
    nimet, hintadata = hae_hintadata()
    koordinaatit = hae_koordinaatit()

    valmis_data = []

    for koodi, nimi_koko in nimet.items():
        match = re.match(r"\d{5}\s+(.*?)\s*\((.*)\)$", nimi_koko)
        if not match or koodi not in koordinaatit:
            continue

        alue_nimi = match.group(1)
        kunta = match.group(2)
        alue_data = hintadata.get(koodi, {})

        hinnat_dict = {}
        kaupat_dict = {}

        for t_koodi, t_avain in TALOTYYPIT.items():
            hinnat_dict[t_avain] = []
            kaupat_dict[t_avain] = []

            for v in VUODET:
                solu = alue_data.get(t_koodi, {}).get(v, [None, None])
                hinnat_dict[t_avain].append(muunna_kokonaisluvuksi(solu[0]))
                kaupat_dict[t_avain].append(muunna_kokonaisluvuksi(solu[1]) or 0)

        # Otetaan mukaan vain alueet, joilla on vähintään jotain hintatietoa
        onko_dataa = any(any(v is not None for v in sarja) for sarja in hinnat_dict.values())
        if onko_dataa:
            lat, lon = koordinaatit[koodi]
            valmis_data.append({
                "code": koodi,
                "name": alue_nimi,
                "city": kunta,
                "lat": lat,
                "lon": lon,
                "p": hinnat_dict,
                "n": kaupat_dict
            })

    kohdekansio = Path(__file__).parent / "data"
    kohdekansio.mkdir(exist_ok=True)
    kohdetiedosto = kohdekansio / "housing.json"

    kohdetiedosto.write_text(json.dumps(valmis_data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"Valmis! Tallennettu {len(valmis_data)} aluetta tiedostoon: {kohdetiedosto}")


if __name__ == "__main__":
    main()