"""Tests del paso 4.4: animación de dados y marcador."""

import subprocess

import pytest
from PIL import Image, ImageChops

from src.motor.batalla import resolver
from src.render import animacion_batalla as A
from src.render import dados as D
from src.render import estilo as E
from src.render import marcador as M

BASE = Image.new("RGB", (E.ANCHO, E.ALTO), (255, 255, 255))


def r_normal():  # 4-1, 3-6, 5-4 → A: +3 +0 +1 = 4; B: +3 → con vacas iguales no hay bonus
    return resolver([4, 3, 5], [1, 6, 4], 1000, 1000)


def r_mult():  # A tiene el doble de vacas → ×1,5
    return resolver([4, 3, 5], [1, 6, 4], 2000, 1000)


def r_sd():  # A: 3+0+0 = 3 contra B: 0+3+0 = 3 (3.º dado empatado) → empate → muerte súbita
    return resolver([4, 1, 2], [1, 4, 2], 1000, 1000, dados_muerte_subita=[(2, 2), (6, 3)])


def test_linea_de_tiempo_crece_con_multiplicador_y_muerte_subita():
    n, m, s = (A.calcular_tiempos(f()) for f in (r_normal, r_mult, r_sd))
    assert n.mult is None and n.sd is None
    assert m.mult is not None and m.duracion > n.duracion
    assert s.sd is not None and len(s.rondas_sd) == 2 and s.sd_fin > s.sd
    assert n.tiradas == sorted(n.tiradas) and n.tiradas[0] == n.dados


def test_el_fotograma_es_una_funcion_pura_del_tiempo():
    r = r_mult()
    T = A.calcular_tiempos(r)
    for t in (0.3, 1.0, 2.5, 6.0, T.mult + 1.0, T.duracion - 0.1):
        assert A.fotograma(BASE, r, t, T).tobytes() == A.fotograma(BASE, r, t, T).tobytes()


def test_antes_de_las_espadas_solo_hay_la_base_y_luego_aparecen():
    r = r_normal()
    T = A.calcular_tiempos(r)
    assert A.fotograma(BASE, r, 0.1, T).tobytes() == BASE.tobytes()
    assert ImageChops.difference(A.fotograma(BASE, r, T.espadas + 0.7, T), BASE).getbbox() is not None


def test_las_tiradas_aparecen_en_orden_y_el_ganador_se_resalta():
    r = r_normal()
    T = A.calcular_tiempos(r)
    oro = tuple(int(E.ORO[i:i + 2], 16) for i in (1, 3, 5))
    def n_oro(t, caja):
        return sum(p == oro for p in A.fotograma(BASE, r, t, T).crop(caja).get_flattened_data())
    fila0 = (D.COL_A - 60, D.y_fila(0) - 10, D.COL_A + 60, D.y_fila(0) + D.LADO + 10)
    # rodando: aún sin borde dorado; ya parado y ganado por A (4 > 1): borde dorado
    assert n_oro(T.tiradas[0] + 0.5, fila0) == 0
    assert n_oro(T.tiradas[0] + A.D_RODAR + A.D_ASENTAR, fila0) > 100
    # en la segunda fila A pierde (3 < 6): su dado no es dorado
    fila1 = (D.COL_A - 36, D.y_fila(1) + 2, D.COL_A + 36, D.y_fila(1) + D.LADO - 2)  # solo el dado
    assert n_oro(T.tiradas[1] + A.D_RODAR + A.D_ASENTAR, fila1) == 0


def test_el_marcador_suma_los_puntos_cuando_aterriza_cada_dado():
    r = r_normal()
    T = A.calcular_tiempos(r)
    assert A._marcador_en(r, T, T.tiradas[0] + 0.5)[:2] == ("0", "0")
    assert A._marcador_en(r, T, T.tiradas[0] + A.D_RODAR + 0.01)[:2] == ("3", "0")
    assert A._marcador_en(r, T, T.tiradas[1] + A.D_RODAR + 0.01)[:2] == ("3", "3")
    assert A._marcador_en(r, T, T.final)[:2] == ("4", "3")


def test_tras_el_multiplicador_el_marcador_muestra_decimales():
    r = r_mult()  # A: 4 × 1,5 = 6,0
    T = A.calcular_tiempos(r)
    assert A._marcador_en(r, T, T.mult + 0.1)[:2] == ("4", "3")
    assert A._marcador_en(r, T, T.final)[:2] == ("6,0", "3,0")
    assert M.formato_decimas(91) == "9,1"


def test_la_muerte_subita_cubre_la_zona_de_dados_y_el_ganador_queda_marcado():
    r = r_sd()
    T = A.calcular_tiempos(r)
    en_sd = A.fotograma(BASE, r, T.rondas_sd[0] + A.D_RODAR + 0.5, T)
    centro = (E.ANCHO // 2, D.Y_MEDIO)
    assert en_sd.getpixel((centro[0] + 150, centro[1] + 90)) == (255, 255, 255)  # tarjeta blanca
    rojo = tuple(int(E.CONFLICTO[i:i + 2], 16) for i in (1, 3, 5))
    assert rojo in {p for p in en_sd.crop((300, D.Y0, 780, D.Y0 + 60)).get_flattened_data()}  # título
    final = A.fotograma(BASE, r, T.final + 0.9, T)
    oro = tuple(int(E.ORO[i:i + 2], 16) for i in (1, 3, 5))
    caja = (int(M.X_A) - 90, D.Y_MEDIO - 100, int(M.X_A) + 90, D.Y_MEDIO + 40)
    assert r.ganador == "a" and oro in {p for p in final.crop(caja).get_flattened_data()}


def test_espadas_y_sprites_tienen_transparencia_y_tamano():
    assert A.D.navaja_botella_sprite(200).size == (200, 200)
    assert A.D.dado_sprite(80, 6).getpixel((0, 0))[3] == 0
    assert D.salida_rebote(0) == pytest.approx(0) and D.salida_rebote(1) == pytest.approx(1)
    assert max(D.salida_rebote(t / 100) for t in range(101)) > 1  # rebasa un poco (efecto «pop»)


def test_se_codifica_un_mp4_valido(tmp_path):
    r = r_normal()
    T = A.calcular_tiempos(r)
    ruta = A.escribir_video((A.fotograma(BASE, r, i / 30, T) for i in range(15)), tmp_path / "v.mp4")
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,nb_frames,codec_name",
                          "-of", "default=nw=1", str(ruta)], capture_output=True, text=True, check=True).stdout
    assert "width=1080" in out and "height=1920" in out and "nb_frames=15" in out and "codec_name=h264" in out
