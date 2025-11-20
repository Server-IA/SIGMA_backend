import csv
import pytest
from pathlib import Path
from types import SimpleNamespace

from monitoring.services import prediction_service as ps_module


class DummyModel:
    def predict(self, X):
        # Return deterministic prediction for testing
        import numpy as _np
        return _np.array([123.45])


@pytest.mark.parametrize("calls, retrain_threshold", [(1, 10), (3, 2)])
def test_predict_and_save_training_data_controlled(tmp_path, monkeypatch, calls, retrain_threshold):
    """
    Controlled integration test:
    - monkeypatch internal data fetchers to avoid heavy DB fixtures
    - monkeypatch model loading to avoid real training/download
    - redirect CSV and counter to `tmp_path`
    This validates the end-to-end path within `predict_and_save_training_data`
    without touching production files or external services.
    """

    service = ps_module.prediction_service

    # Backup original attrs
    orig_model_dir = service.MODEL_DIR
    orig_csv = service.TRAINING_DATA_CSV
    orig_counter = service.TRAINING_COUNTER_FILE
    orig_registers = service.REGISTERS_FOR_RETRAIN
    orig_model = service.model
    orig_loaded = service.model_loaded

    try:
        # Redirect files to tmp_path
        service.MODEL_DIR = Path(tmp_path)
        service.TRAINING_DATA_CSV = Path(tmp_path) / "training_data_accumulated.csv"
        service.TRAINING_COUNTER_FILE = Path(tmp_path) / "training_counter.txt"

        # Small threshold to test retrain path when requested
        service.REGISTERS_FOR_RETRAIN = retrain_threshold

        # Ensure clean
        if service.TRAINING_DATA_CSV.exists():
            service.TRAINING_DATA_CSV.unlink()
        if service.TRAINING_COUNTER_FILE.exists():
            service.TRAINING_COUNTER_FILE.unlink()

        # Monkeypatch model loader to return a DummyModel
        monkeypatch.setattr(service, "_load_model", lambda: DummyModel())

        # Monkeypatch data getters to return deterministic feature pieces
        monkeypatch.setattr(service, "_get_machinery_data", lambda machinery: {
            'Pnominal(kW)': 50.0,
            'Masa_total(kg)': 2000.0
        })

        monkeypatch.setattr(service, "_get_request_data", lambda request, machinery: {
            'Implemento': 'TestImp',
            'k_base': 0.1,
            'n': 0.2,
            'Ancho(m)': 1.2,
            'Profundidad(m)': 0.3,
            'Textura': 'franco',
            'Humedad(%)': 12.0,
            'Pendiente(%)': 0.0,
            'Duracion(h)': 1.5,
            'Tipo_suelo': 'Desconocido'
        })

        monkeypatch.setattr(service, "_get_telemetry_data", lambda request, machinery: {
            'Velocidad(km/h)': 6.0,
            'RPM': 1500.0
        })

        monkeypatch.setattr(service, "_get_ambient_temperature", lambda request: 22.0)

        # Ensure consumption real returns None so prediction is used
        monkeypatch.setattr(service, "_get_consumption_real", lambda request, machinery, ts: None)

        # Track if retrain called
        called = {"retrained": 0}

        def fake_retrain():
            called["retrained"] += 1
            # simulate cleaning CSV header
            cols = [
                'Pnominal(kW)', 'T(°C)', 'Implemento', 'k_base', 'n', 'Ancho(m)',
                'Profundidad(m)', 'Textura', 'Humedad(%)', 'Velocidad(km/h)',
                'Masa_total(kg)', 'Pendiente(%)', 'Tipo_suelo', 'RPM', 'Duracion(h)', 'Consumo_total(L)'
            ]
            with open(service.TRAINING_DATA_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
            return True

        monkeypatch.setattr(service, "_retrain_model", fake_retrain)

        # Prepare fake request/machinery objects (not saved to DB). The monkeypatched getters ignore them.
        from django.utils import timezone
        fake_request = SimpleNamespace(id_request='REQ-INT-001')
        fake_machinery = SimpleNamespace(id_machinery=1)
        ts = timezone.now()

        # Call predict_and_save_training_data `calls` times
        for i in range(calls):
            out = service.predict_and_save_training_data(
                request=fake_request,
                machinery=fake_machinery,
                imei="000000000000000",
                timestamp=ts,
                user=None
            )

            assert out is not None, "predict_and_save_training_data returned None"
            assert "consumo_estimado_l" in out
            assert "training_counter" in out

        # Validate CSV rows (if retrain threshold not yet reached, rows == calls)
        with open(service.TRAINING_DATA_CSV, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        # Expected rows after possible retrain(s)
        expected_retrains = calls // retrain_threshold
        expected_rows = calls % retrain_threshold

        assert called["retrained"] == expected_retrains
        assert len(rows) == expected_rows

        # Validate counter file exists and value is correct
        with open(service.TRAINING_COUNTER_FILE, 'r', encoding='utf-8') as f:
            val = int(f.read().strip())

        assert val == expected_rows

    finally:
        # restore
        service.MODEL_DIR = orig_model_dir
        service.TRAINING_DATA_CSV = orig_csv
        service.TRAINING_COUNTER_FILE = orig_counter
        service.REGISTERS_FOR_RETRAIN = orig_registers
        service.model = orig_model
        service.model_loaded = orig_loaded
