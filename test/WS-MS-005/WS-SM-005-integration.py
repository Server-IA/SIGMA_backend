import csv
import pytest
from types import SimpleNamespace
from pathlib import Path
from django.utils import timezone

from monitoring.services import prediction_service as ps_module


class DummyModel:
    def predict(self, X):
        return [35.0]


@pytest.mark.django_db
def test_consumo_comparativa_controlada(tmp_path, monkeypatch):
    """
    Integración controlada para WS-MS-005:
    - Monkeypatch del modelo por `DummyModel` (no hay entrenamiento ni descarga).
    - Monkeypatch de getters para devolver valores deterministas.
    - Redirección de CSV/contador a `tmp_path`.
    """

    service = ps_module.prediction_service

    # backup
    orig_model_dir = service.MODEL_DIR
    orig_csv = service.TRAINING_DATA_CSV
    orig_counter = service.TRAINING_COUNTER_FILE
    orig_registers = service.REGISTERS_FOR_RETRAIN
    orig_model = service.model
    orig_loaded = service.model_loaded

    try:
        # redirect
        service.MODEL_DIR = Path(tmp_path)
        service.TRAINING_DATA_CSV = Path(tmp_path) / "training_data_accumulated.csv"
        service.TRAINING_COUNTER_FILE = Path(tmp_path) / "training_counter.txt"
        service.REGISTERS_FOR_RETRAIN = 1000

        # patch model
        monkeypatch.setattr(service, "_load_model", lambda: DummyModel())

        # Test scenario parameters
        tank_capacity = 200.0
        nivel_ini = 80.0
        nivel_fin = 60.0
        work_duration_h = 2.0

        # monkeypatch consumption real calculation to use simple difference * tank
        def fake_get_consumption_real(request, machinery, timestamp):
            delta_pct = nivel_ini - nivel_fin
            return (delta_pct / 100.0) * tank_capacity

        monkeypatch.setattr(service, "_get_consumption_real", fake_get_consumption_real)

        # request data provides duration
        monkeypatch.setattr(service, "_get_request_data", lambda request, machinery: {
            'Implemento': 'TestImp',
            'k_base': 0.1,
            'n': 0.2,
            'Ancho(m)': 1.2,
            'Profundidad(m)': 0.3,
            'Textura': 'franco',
            'Humedad(%)': 12.0,
            'Pendiente(%)': 0.0,
            'Duracion(h)': float(work_duration_h),
            'Tipo_suelo': 'Desconocido'
        })

        monkeypatch.setattr(service, "_get_machinery_data", lambda machinery: {
            'Pnominal(kW)': 50.0,
            'Masa_total(kg)': 2000.0
        })

        monkeypatch.setattr(service, "_get_telemetry_data", lambda request, machinery: {
            'Velocidad(km/h)': 6.0,
            'RPM': 1500.0
        })

        monkeypatch.setattr(service, "_get_ambient_temperature", lambda request: 22.0)

        # fake request/machinery
        fake_request = SimpleNamespace(id_request="REQ-WS-MS-005-1")
        fake_machinery = SimpleNamespace(id_machinery=1)
        ts = timezone.now()

        out = service.predict_and_save_training_data(
            request=fake_request,
            machinery=fake_machinery,
            imei="000000000000000",
            timestamp=ts,
            user=None
        )

        assert out is not None

        consumo_real_esperado = ((nivel_ini - nivel_fin) / 100.0) * tank_capacity
        assert out["consumo_real_l"] == pytest.approx(consumo_real_esperado, rel=1e-6)
        assert out["consumo_estimado_l"] == pytest.approx(35.0)
        assert out["consumo_estimado_lh"] == pytest.approx(35.0 / work_duration_h)

        diferencia_abs = abs(consumo_real_esperado - 35.0)
        if consumo_real_esperado != 0:
            error_pct = diferencia_abs / consumo_real_esperado * 100.0
            calc_error = abs(out["consumo_real_l"] - out["consumo_estimado_l"]) / out["consumo_real_l"] * 100.0
            assert calc_error == pytest.approx(error_pct, rel=1e-6)

    finally:
        service.MODEL_DIR = orig_model_dir
        service.TRAINING_DATA_CSV = orig_csv
        service.TRAINING_COUNTER_FILE = orig_counter
        service.REGISTERS_FOR_RETRAIN = orig_registers
        service.model = orig_model
        service.model_loaded = orig_loaded
