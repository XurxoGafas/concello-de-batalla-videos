"""Tests de banderas y escudos (paso 2.5)."""
import json

from PIL import Image

from src.datos.construir_estado import construir
from src.render import estilo as E
from src.render import portada as PT
from src.render.mapa import MapaGalicia

RAIZ = E.RAIZ


def _estado():
    return json.loads((RAIZ / "data" / "processed" / "estado_inicial.json").read_text(encoding="utf-8"))


def test_los_concellos_con_escudo_se_pintan_de_blanco_y_el_archivo_existe():
    e = _estado()
    esc = [c for c in e["concellos"].values() if c["cor"]["fonte"] == "escudo"]
    assert len(esc) > 150
    for c in esc:
        assert c["cor"]["colores"] == ["#ffffff"]
        assert (RAIZ / c["cor"]["escudo"]).exists(), c["nome"]
    assert all(d["cor"] == e["concellos"][i]["cor"] for i, d in e["donos"].items())


def test_cada_concello_tiene_bandera_escudo_o_color_provisional():
    e = _estado()
    fuentes = {c["cor"]["fonte"] for c in e["concellos"].values()}
    assert fuentes <= {"bandeira", "escudo", "provisional"}
    prov = sorted(c["nome"] for c in e["concellos"].values() if c["cor"]["fonte"] == "provisional")
    assert "Rianxo" in prov and "Carral" in prov and len(prov) == 8


def test_los_escudos_son_rgba_con_fondo_transparente():
    e = _estado()
    for c in e["concellos"].values():
        if c["cor"]["fonte"] == "escudo":
            im = Image.open(RAIZ / c["cor"]["escudo"]).convert("RGBA")
            esquinas = [im.getpixel(p)[3] for p in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1))]
            assert min(esquinas) == 0, c["nome"]  # el escudo no lleva fondo: alguna esquina es transparente
            assert im.height <= 300


def test_construir_acepta_escudos():
    nombres = {"a": ("A", "P"), "b": ("B", "P")}
    e = construir(nombres, {"a": ["b"], "b": ["a"]}, {"a": 1, "b": 2}, {}, {"a": {"escudo": "assets/escudos/x.png"}})
    assert e["concellos"]["a"]["cor"]["fonte"] == "escudo" and e["concellos"]["b"]["cor"]["fonte"] == "provisional"


def test_el_mapa_dibuja_el_escudo_sobre_el_territorio_blanco():
    e = _estado()
    mapa = MapaGalicia()
    k = next(i for i, c in e["concellos"].items() if c["nome"] == "Verín")
    ventana = E.caja_de_zoom(mapa.limites([k]), 1080 / 440, margen=0.3)
    con = mapa.dibujar(e, ventana, 1080, 440)
    sin = mapa.dibujar({**e, "donos": {**e["donos"], k: {**e["donos"][k], "cor": {"colores": ["#ffffff"], "pesos": [1.0]}}}},
                       ventana, 1080, 440)
    assert con.tobytes() != sin.tobytes()  # con escudo se ve distinto que sin él


def test_la_silueta_de_la_portada_lleva_el_escudo():
    mapa = MapaGalicia()
    e = _estado()
    k = next(i for i, c in e["concellos"].items() if c["nome"] == "Frades")
    cor = e["concellos"][k]["cor"]
    con = PT._silueta(mapa.geometria([k]), 400, 300, cor["colores"][0], cor["escudo"])
    sin = PT._silueta(mapa.geometria([k]), 400, 300, cor["colores"][0])
    assert con.tobytes() != sin.tobytes()
