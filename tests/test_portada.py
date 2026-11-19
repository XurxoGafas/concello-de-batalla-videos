"""Tests de la portada-gancho (paso 4.7)."""
import pytest

from src.motor.momentos import MARCA_A, MARCA_B
from src.render import escenas as S
from src.render import estilo as E
from src.render import portada as PT
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def montaje():
    return S.construir_episodio(S.estado_de_muestra(), "muestra", MapaGalicia())


def test_la_frase_cabe_en_la_zona_segura():
    for txt in (f"{MARCA_A}A Coruña{MARCA_B} xoga a súa última carta, e ninguén o viu vir ata hoxe!", "Carallo, que tirada!"):
        lineas, tam = PT.partir_frase(txt)
        assert 1 <= len(lineas) <= PT.MAX_LINEAS and tam >= PT.TAM_MIN
        for l in lineas:
            assert E.ancho_texto(" ".join(w for w, _ in l), tam) <= PT.TEXTO_ANCHO


def test_el_nombre_va_marcado_y_no_quedan_marcadores():
    lineas, _ = PT.partir_frase(f"Hoxe cae {MARCA_A}O Porriño{MARCA_B}?")
    assert [w for l in lineas for w, es in l if es] == ["O", "Porriño"]
    assert all(MARCA_A not in w and MARCA_B not in w for l in lineas for w, _ in l)


def test_portada_es_la_primera_escena_y_el_fondo_es_negro(montaje):
    e = montaje.escenas[0]
    assert isinstance(e, PT.EscenaPortada) and e.fundido == 0
    f = e.fotograma(0.0)
    assert f.getpixel((20, 20)) == (0, 0, 0) and f.getpixel((1060, 1900)) == (0, 0, 0)
    assert f.size == (E.ANCHO, E.ALTO)


def test_la_portada_enlaza_sin_salto_con_la_intro(montaje):
    e, intro = montaje.escenas[0], montaje.escenas[1]
    assert e.fotograma(e.duracion - 1e-6).tobytes() == intro.img.tobytes()
    assert e.fotograma(e.duracion).tobytes() == intro.img.tobytes()
    assert e.fotograma(0.0).tobytes() != intro.img.tobytes()
