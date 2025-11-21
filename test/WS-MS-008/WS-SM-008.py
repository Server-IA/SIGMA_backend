import os
from pathlib import Path
import io
import csv
import pytest

from monitoring.services.prediction_service import prediction_service


@pytest.mark.parametrize("rows", [1, 3])
def test_append_and_counter_increment(tmp_path, rows):
    """
    Verify training CSV is created and rows are appended, and counter increments.
    This test operates on a temporary model dir so it doesn't touch workspace files.
    """
    # Backup original paths
    orig_model_dir = prediction_service.MODEL_DIR
    orig_csv = prediction_service.TRAINING_DATA_CSV
    orig_counter = prediction_service.TRAINING_COUNTER_FILE

    try:
        # Point service to tmp paths
        prediction_service.MODEL_DIR = Path(tmp_path)
        prediction_service.TRAINING_DATA_CSV = Path(tmp_path) / "training_data_accumulated.csv"
        prediction_service.TRAINING_COUNTER_FILE = Path(tmp_path) / "training_counter.txt"

        # Ensure clean state
        if prediction_service.TRAINING_COUNTER_FILE.exists():
            prediction_service.TRAINING_COUNTER_FILE.unlink()
        if prediction_service.TRAINING_DATA_CSV.exists():
            prediction_service.TRAINING_DATA_CSV.unlink()

        sample_row = {
            'Pnominal(kW)': 10.0,
            'T(°C)': 20.0,
            'Implemento': 'TestImp',
            'k_base': 0.1,
            'n': 0.2,
            'Ancho(m)': 1.0,
            'Profundidad(m)': 0.5,
            'Textura': 'franco',
            'Humedad(%)': 10.0,
            'Velocidad(km/h)': 5.0,
            'Masa_total(kg)': 1000.0,
            'Pendiente(%)': 0.0,
            'Tipo_suelo': 'Desconocido',
            'RPM': 1000,
            'Duracion(h)': 2.0,
            'Consumo_total(L)': 50.0
        }

        # Append rows times and increment counter each time
        for i in range(rows):
            prediction_service._append_to_training_csv(sample_row)
            count = prediction_service._increment_training_counter()
            assert count == i + 1

        # Validate CSV content has expected number of data rows
        assert prediction_service.TRAINING_DATA_CSV.exists()
        with open(prediction_service.TRAINING_DATA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            read_rows = list(reader)
            assert len(read_rows) == rows

        # Validate counter file content
        with open(prediction_service.TRAINING_COUNTER_FILE, 'r', encoding='utf-8') as f:
            val = int(f.read().strip())
            assert val == rows

    finally:
        # restore originals
        prediction_service.MODEL_DIR = orig_model_dir
        prediction_service.TRAINING_DATA_CSV = orig_csv
        prediction_service.TRAINING_COUNTER_FILE = orig_counter


def test_retrain_trigger_and_reset(tmp_path, monkeypatch):
    """
    Simulate the retrain trigger by monkeypatching `_retrain_model` to avoid
    running an expensive training job. Verify the retrain hook is called when
    counter reaches `REGISTERS_FOR_RETRAIN` and that counter is reset afterwards.
    """
    # Backup original values
    orig_model_dir = prediction_service.MODEL_DIR
    orig_csv = prediction_service.TRAINING_DATA_CSV
    orig_counter = prediction_service.TRAINING_COUNTER_FILE
    orig_registers = prediction_service.REGISTERS_FOR_RETRAIN

    try:
        # Use temp files
        prediction_service.MODEL_DIR = Path(tmp_path)
        prediction_service.TRAINING_DATA_CSV = Path(tmp_path) / "training_data_accumulated.csv"
        prediction_service.TRAINING_COUNTER_FILE = Path(tmp_path) / "training_counter.txt"

        # make threshold small for test
        prediction_service.REGISTERS_FOR_RETRAIN = 3

        # Ensure clean files
        if prediction_service.TRAINING_COUNTER_FILE.exists():
            prediction_service.TRAINING_COUNTER_FILE.unlink()
        if prediction_service.TRAINING_DATA_CSV.exists():
            prediction_service.TRAINING_DATA_CSV.unlink()

        # Prepare a simple training row
        sample_row = {k: 1 for k in [
            'Pnominal(kW)', 'T(°C)', 'Implemento', 'k_base', 'n', 'Ancho(m)',
            'Profundidad(m)', 'Textura', 'Humedad(%)', 'Velocidad(km/h)',
            'Masa_total(kg)', 'Pendiente(%)', 'Tipo_suelo', 'RPM', 'Duracion(h)', 'Consumo_total(L)'
        ]}

        called = {'retrained': False}

        def fake_retrain():
            # Simulate successful retrain by writing CSV header only
            called['retrained'] = True
            # create CSV with header only (simulate cleaned file)
            columns = [
                'Pnominal(kW)', 'T(°C)', 'Implemento', 'k_base', 'n', 'Ancho(m)',
                'Profundidad(m)', 'Textura', 'Humedad(%)', 'Velocidad(km/h)',
                'Masa_total(kg)', 'Pendiente(%)', 'Tipo_suelo', 'RPM', 'Duracion(h)', 'Consumo_total(L)'
            ]
            with open(prediction_service.TRAINING_DATA_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
            return True

        # Monkeypatch the instance method
        monkeypatch.setattr(prediction_service, '_retrain_model', fake_retrain)

        # Simulate appending rows and incrementing the counter; trigger retrain when threshold reached
        for i in range(prediction_service.REGISTERS_FOR_RETRAIN):
            prediction_service._append_to_training_csv(sample_row)
            count = prediction_service._increment_training_counter()
            assert count == i + 1

        # Now simulate the logic that predict_and_save_training_data would run
        if count >= prediction_service.REGISTERS_FOR_RETRAIN:
            ok = prediction_service._retrain_model()
            if ok:
                prediction_service._reset_training_counter()

        # Assert retrain was called and counter was reset
        assert called['retrained'] is True
        with open(prediction_service.TRAINING_COUNTER_FILE, 'r', encoding='utf-8') as f:
            assert int(f.read().strip()) == 0

        # And CSV should exist with only headers (no data rows)
        with open(prediction_service.TRAINING_DATA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0

    finally:
        # restore originals
        prediction_service.MODEL_DIR = orig_model_dir
        prediction_service.TRAINING_DATA_CSV = orig_csv
        prediction_service.TRAINING_COUNTER_FILE = orig_counter
        prediction_service.REGISTERS_FOR_RETRAIN = orig_registers
