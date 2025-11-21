import pytest

def calc_consumo_real_por_niveles(nivel_inicial_pct, nivel_final_pct, tank_capacity_l):
    delta_pct = nivel_inicial_pct - nivel_final_pct
    return (delta_pct / 100.0) * tank_capacity_l


def calc_consumo_instantaneo_lh(consumo_l, duracion_h):
    if duracion_h is None or duracion_h <= 0:
        return 0.0
    return consumo_l / duracion_h


def calc_error_porcentual(real_l, estimado_l):
    if real_l == 0:
        return None
    return abs(real_l - estimado_l) / real_l * 100.0


def test_calc_consumo_real_por_niveles():
    assert pytest.approx(calc_consumo_real_por_niveles(80, 60, 200.0), rel=1e-6) == 40.0


def test_calc_consumo_instantaneo_lh():
    assert calc_consumo_instantaneo_lh(40.0, 2.0) == pytest.approx(20.0)
    assert calc_consumo_instantaneo_lh(40.0, 0) == 0.0
    assert calc_consumo_instantaneo_lh(0.0, 2.0) == 0.0


def test_calc_error_porcentual():
    assert calc_error_porcentual(40.0, 36.0) == pytest.approx(10.0)
    assert calc_error_porcentual(0.0, 36.0) is None
