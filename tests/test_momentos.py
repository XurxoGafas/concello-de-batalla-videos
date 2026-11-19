"""Tests del paso 4.7: frases gancho y elección del momento de la portada."""

import random
from types import SimpleNamespace as NS

import pytest

from src.motor import momentos as MO

FRASES = MO.cargar_frases()


# ---------- Gallego ----------

@pytest.mark.parametrize("nombre,a,de", [
    ("A Coruña", "á Coruña", "da Coruña"),
    ("O Porriño", "ao Porriño", "do Porriño"),
    ("As Neves", "ás Neves", "das Neves"),
    ("Os Blancos", "aos Blancos", "dos Blancos"),
    ("Ordes", "a Ordes", "de Ordes"),
    ("Vilamartín de Valdeorras", "a Vilamartín de Valdeorras", "de Vilamartín de Valdeorras"),
])
def test_contracciones(nombre, a, de):
    assert MO.sin_marcas(MO.expandir("{concello:a}", nombre)) == a
    assert MO.sin_marcas(MO.expandir("{concello:de}", nombre)) == de


def test_concordancia_de_numero_y_genero():
    t = "{concello} {n:vén|véñen} {g:cargado|cargada|cargados|cargadas}"
    assert MO.sin_marcas(MO.expandir(t, "Ordes")) == "Ordes vén cargado"
    assert MO.sin_marcas(MO.expandir(t, "A Coruña")) == "A Coruña vén cargada"
    assert MO.sin_marcas(MO.expandir(t, "Os Blancos")) == "Os Blancos véñen cargados"
    assert MO.sin_marcas(MO.expandir(t, "As Neves")) == "As Neves véñen cargadas"


def test_el_nombre_queda_marcado_para_resaltarlo():
    assert MO.expandir("{concello:de}", "A Coruña") == f"da {MO.MARCA_A}Coruña{MO.MARCA_B}"
    assert MO.expandir("¿Cae {concello}?", "Ordes") == f"¿Cae {MO.MARCA_A}Ordes{MO.MARCA_B}?"


def test_bateria_de_48_frases_y_todas_se_pueden_rellenar():
    assert len(FRASES) == 48 and len({f["id"] for f in FRASES}) == 48
    assert {f["tipo"] for f in FRASES} == {"atacante", "defensor", "dados", "multiplicador", "morte_subita"}
    for f in FRASES:
        for nombre in ("Ordes", "A Coruña", "O Porriño", "As Neves", "Os Blancos", "As Pontes de García Rodríguez"):
            if es := (f["plural"] or not MO.es_plural(nombre)):
                txt = MO.sin_marcas(MO.expandir(f["texto"], nombre))
                assert "{" not in txt and "}" not in txt and txt


def test_ninguna_frase_dice_quien_gana():
    prohibidas = ("gaña", "gañou", "perde", "perdeu", "cae ", "caeu", "conquista a", "vitoria")
    for f in FRASES:
        assert not any(p in f["texto"].lower() for p in prohibidas), f["texto"]


def test_frases_de_nombre_plural_solo_las_validas():
    for _ in range(50):
        f = MO.elegir_frase("atacante", "As Neves", FRASES, [], random.Random(_))
        assert f["plural"]


# ---------- Momentos y elección ----------

def batalla(a, b, nom_a, nom_b, mult_a=1.0, mult_b=1.0, subita=False):
    estado = {"donos": {a: {"nome": nom_a}, b: {"nome": nom_b}}}
    ep = NS(enfrentamiento=NS(atacante=a, defensor=b),
            resultado=NS(mult_a=mult_a, mult_b=mult_b, muerte_subita=(1,) if subita else ()))
    return estado, ep


POB = {"v": 295_000, "o": 20_000, "p": 9_000, "q": 3_000, "r": 2_000, "s": 1_000}


def tres(subita_en=None):
    return [batalla("o", "p", "Ordes", "Pontevedra"),
            batalla("v", "q", "Vigo", "Quiroga", subita=subita_en == "v"),
            batalla("r", "s", "Rairiz", "Sada")]


def test_detecta_muerte_subita_y_bonus_grande():
    m = MO.detectar_momentos([batalla("o", "p", "A", "B", mult_a=1.5, subita=True)], {"o": 1, "p": 1})
    tipos = {(x.concello, x.tipo) for x in m}
    assert ("o", "morte_subita") in tipos and ("p", "morte_subita") in tipos
    assert ("o", "multiplicador") in tipos and ("p", "multiplicador") not in tipos
    assert MO.detectar_momentos([batalla("o", "p", "A", "B", mult_a=1.3)], {"o": 1, "p": 1})[0].tipo == "atacante"
    assert all(x.tipo != "multiplicador" for x in MO.detectar_momentos([batalla("o", "p", "A", "B", mult_a=1.3)], {"o": 1, "p": 1}))


def test_reparto_70_30_con_el_mas_poblado_cuando_tiene_momento_singular():
    n = 4000
    grandes = 0
    for i in range(n):
        p = MO.elegir_portada(tres(subita_en="v"), POB, FRASES, [], random.Random(i))
        grandes += p.concello == "v"
        assert p.rama == ("grande" if p.concello == "v" else "otro")
    assert abs(grandes / n - 0.70) < 0.03


def test_si_el_mas_poblado_no_tiene_momento_singular_se_elige_otro_concello():
    for i in range(300):
        p = MO.elegir_portada(tres(), POB, FRASES, [], random.Random(i))
        assert p.concello != "v" and p.rama == "otro"


def test_el_30_por_ciento_nunca_es_el_mas_poblado():
    for i in range(300):
        rng = random.Random(i)
        m, rama = MO.elegir_momento(MO.detectar_momentos(tres(subita_en="v"), POB), rng)
        assert (rama == "grande") == (m.concello == "v")


def test_el_momento_mas_singular_gana_a_los_demas():
    bs = [batalla("o", "p", "Ordes", "Pontevedra", mult_a=1.5), batalla("v", "q", "Vigo", "Quiroga", subita=True)]
    m, _ = MO.elegir_momento(MO.detectar_momentos(bs, POB), random.Random(1))
    assert m.tipo in ("morte_subita", "multiplicador")


def test_misma_semilla_misma_portada_y_la_frase_encaja_con_el_tipo():
    a = MO.elegir_portada(tres(subita_en="v"), POB, FRASES, [], random.Random(7))
    assert a == MO.elegir_portada(tres(subita_en="v"), POB, FRASES, [], random.Random(7))
    tipo_de = {f["id"]: f["tipo"] for f in FRASES}
    for i in range(100):
        p = MO.elegir_portada(tres(subita_en="v"), POB, FRASES, [], random.Random(i))
        assert tipo_de[p.frase_id] == p.tipo and p.nombre in MO.sin_marcas(p.texto) or p.frase_id == 27


def test_no_repite_frases_recientes_y_cuando_se_agotan_usa_la_mas_antigua():
    ids = [f["id"] for f in FRASES if f["tipo"] == "morte_subita"]
    for i in range(50):
        f = MO.elegir_frase("morte_subita", "Ordes", FRASES, ids[:5], random.Random(i))
        assert f["id"] not in ids[:5]
    f = MO.elegir_frase("morte_subita", "Ordes", FRASES, ids, random.Random(0))  # todas recientes
    assert f["id"] == ids[0]  # la que lleva más tiempo sin salir


def test_historial(tmp_path):
    ruta = tmp_path / "portadas.jsonl"
    assert MO.leer_recientes(ruta) == []
    p = MO.Portada("o", "Ordes", "atacante", 1, "otro", 5, "x")
    MO.anadir_al_historial(3, p, ruta)
    MO.anadir_al_historial(4, p, ruta)
    assert MO.leer_recientes(ruta) == [5, 5]
