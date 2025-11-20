import pytest
from types import SimpleNamespace
from pathlib import Path
from django.utils import timezone

from monitoring.services import prediction_service as ps_module


class DummyModel:
    def predict(self, X):
        return [35.0]


@pytest.mark.django_db
def test_retrain_trigger_and_csv_accumulation(tmp_path, monkeypatch):
    """
    DB-like integration test for WS-MS-008 (controlled):
    - Redirect model dir and CSV to `tmp_path`
    - Set `REGISTERS_FOR_RETRAIN` low (2) to trigger retrain after two calls
    - Spy on `_retrain_model` to assert it is invoked
    - Verify CSV is created and two rows are appended
    """

    service = ps_module.prediction_service

    # Backup originals
    orig_model_dir = service.MODEL_DIR
    orig_csv = service.TRAINING_DATA_CSV
    orig_counter = service.TRAINING_COUNTER_FILE
    orig_registers = service.REGISTERS_FOR_RETRAIN
    orig_model = getattr(service, 'model', None)
    orig_loaded = getattr(service, 'model_loaded', None)

    try:
        # Redirect to temp
        service.MODEL_DIR = Path(tmp_path)
        service.TRAINING_DATA_CSV = Path(tmp_path) / "training_data_accumulated.csv"
        service.TRAINING_COUNTER_FILE = Path(tmp_path) / "training_counter.txt"
        service.REGISTERS_FOR_RETRAIN = 2

        # Force a deterministic model and getters
        monkeypatch.setattr(service, "_load_model", lambda: DummyModel())

        tank_capacity = 200.0
        nivel_ini = 80.0
        nivel_fin = 60.0
        work_duration_h = 2.0

        # Provide deterministic consumption real
        monkeypatch.setattr(service, "_get_consumption_real", lambda request, machinery, timestamp: ((nivel_ini - nivel_fin) / 100.0) * tank_capacity)

        # Minimal request/machinery data used by _prepare_features
        monkeypatch.setattr(service, "_get_request_data", lambda request, machinery: {'Duracion(h)': float(work_duration_h), 'Implemento': 'TestImp', 'k_base': 0.1, 'n': 0.2, 'Ancho(m)': 1.2, 'Profundidad(m)': 0.3, 'Textura': 'franco', 'Humedad(%)': 12.0, 'Pendiente(%)': 0.0, 'Tipo_suelo': 'Desconocido'})
        monkeypatch.setattr(service, "_get_machinery_data", lambda machinery: {'Pnominal(kW)': 50.0, 'Masa_total(kg)': 2000.0})
        monkeypatch.setattr(service, "_get_telemetry_data", lambda request, machinery: {'Velocidad(km/h)': 6.0, 'RPM': 1500.0})
        monkeypatch.setattr(service, "_get_ambient_temperature", lambda request: 22.0)

        # Spy for retrain calls
        calls = {"count": 0}

        def fake_retrain():
            calls["count"] += 1
            # Return False to indicate retrain did not actually run (we're not training here)
            return False

        monkeypatch.setattr(service, "_retrain_model", fake_retrain)

        fake_request = SimpleNamespace(id_request="REQ-WS-MS-008-1")
        fake_machinery = SimpleNamespace(id_machinery=1)
        ts = timezone.now()

        # First call -> should append one row and counter = 1
        out1 = service.predict_and_save_training_data(request=fake_request, machinery=fake_machinery, imei="000000000000001", timestamp=ts, user=None)
        assert out1 is not None
        assert out1.get('training_counter') == 1

        # Second call -> should append second row and trigger retrain (calls count increments)
        out2 = service.predict_and_save_training_data(request=fake_request, machinery=fake_machinery, imei="000000000000001", timestamp=ts, user=None)
        assert out2 is not None
        # After second call, counter should be >= 2
        assert out2.get('training_counter') >= 2

        # Give a moment for retrain logic (sync here)
        assert calls["count"] >= 1, "_retrain_model was not invoked when threshold reached"

        # Verify CSV contents: at least header + 2 rows
        csv_path = service.TRAINING_DATA_CSV
        assert csv_path.exists(), "Training CSV not created"
        content = csv_path.read_text(encoding='utf-8')
        # Expect header line + at least 2 data lines
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) >= 3, f"Expected at least header+2 rows in CSV, found {len(lines)} lines"

    finally:
        # Restore
        service.MODEL_DIR = orig_model_dir
        service.TRAINING_DATA_CSV = orig_csv
        service.TRAINING_COUNTER_FILE = orig_counter
        service.REGISTERS_FOR_RETRAIN = orig_registers
        if orig_model is not None:
            service.model = orig_model
        service.model_loaded = orig_loaded
