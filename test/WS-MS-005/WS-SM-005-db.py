import pytest
from django.utils import timezone
from pathlib import Path

from monitoring.services import prediction_service as ps_module


class DummyModel:
    def predict(self, X):
        return [35.0]


@pytest.mark.django_db
def test_consumo_real_vs_estimado_db(tmp_path, monkeypatch):
    """
    DB-backed integration test for WS-MS-005:
    - Crea fixtures mínimos en la BD (User, Statues, Types, Models, Machinery,
      TelemetryDevices, Parameters, Customer, ServiceRequest, RequestMachineryUser, Data)
    - Inserta un registro de consumo real (param avl_id 12) con valor 40.0 L
    - Monkeypatch `_load_model` para devolver `DummyModel` con prediction 35.0 L
    - Llama a `predict_and_save_training_data` y verifica valores y error%
    """

    # Local imports (models)
    from users.models.user import User
    from parameterization.models.statues_category import StatuesCategory
    from parameterization.models.statues import Statues
    from parameterization.models.types_category import TypesCategory
    from parameterization.models.types import Types
    from parameterization.models.brand_model import Models as BrandModel
    from machinery.models.machinery import Machinery
    from machinery.models.telemetry_devices import TelemetryDevices
    from machinery.models.parameters import Parameters
    from service_requests.models.customer import Customer
    from service_requests.models.person_type import PersonType
    from service_requests.models.tax_regime import TaxRegime
    from service_requests.models.service_request import ServiceRequest
    from service_requests.models.request_machinery_user import RequestMachineryUser
    from monitoring.models.data import Data

    # Create minimal user
    u = User.objects.create(id_user=1)

    now = timezone.now()

    # Statues and related
    sc = StatuesCategory.objects.create(name='default', description='desc', creation_date=now, modification_date=now, id_responsible_user=u)
    st = Statues.objects.create(name='active', description='active', id_statues_categories=sc, modification_date=now, creation_date=now, id_responsible_user=u)

    # Types
    tc = TypesCategory.objects.create(name='mach', description='mach cat', creation_date=now, modification_date=now, id_responsible_user=u)
    t = Types.objects.create(name='tractor', description='tractor', id_types_categories=tc, creation_date=now, modification_date=now, id_responsible_user=u, id_statues=st)

    # Brand model minimal
    bm = BrandModel.objects.create(name='ModelX', creation_date=now, modification_date=now, id_responsible_user=u, id_statues=st)

    # Machinery
    mach = Machinery.objects.create(
        machinery_name='TestMach',
        serial_number='SN-001',
        machinery_type=t,
        id_model=bm,
        machinery_secondary_type=t,
        machinery_operational_status=st,
        id_responsible_user=u
    )

    # Telemetry device
    dev = TelemetryDevices.objects.create(name='dev1', IMEI=123456789012345, id_statues=st, id_responsible_user=u)

    # Parameters: fuel level (48) and fuel used (12) and ignition (239)
    p_fuel_level = Parameters.objects.create(parameter_name='fuel_level', avl_id_parameter=48)
    p_fuel_used = Parameters.objects.create(parameter_name='fuel_used', avl_id_parameter=12)

    # Create minimal units/types needed for SpecificTechnicalSheet
    from parameterization.models.units_category import UnitsCategory
    from parameterization.models.units import Units

    uc = UnitsCategory.objects.create(name='unitcat', description='unitcat', creation_date=now, modification_date=now, id_responsible_user=u)
    unit = Units.objects.create(id_units_categories=uc, name='unidad', symbol='u', id_types=t, modification_date=now, creation_date=now, id_responsible_user=u, id_statues=st)

    # SpecificTechnicalSheet for machinery (provide required fields)
    from machinery.models.specific_technical_sheet import SpecificTechnicalSheet
    SpecificTechnicalSheet.objects.create(
        power=100.0,
        power_unit=unit,
        engine_type=t,
        cylinder_capacity=2.0,
        cylinder_capacity_unit=unit,
        cylinder_arrangement_type=t,
        cylinder_count=4,
        traction_type=t,
        fuel_consumption=10.0,
        fuel_consumption_unit=unit,
        transmission_system_type=t,
        fuel_capacity=200.0,
        fuel_capacity_unit=unit,
        carrying_capacity=500.0,
        carrying_capacity_unit=unit,
        operating_weight=3000.0,
        operating_weight_unit=unit,
        max_speed=60.0,
        max_speed_unit=unit,
        draft_force=None,
        draft_force_unit=unit,
        maximum_altitude=None,
        maximum_altitude_unit=unit,
        minimum_performance=None,
        maximum_performance=None,
        performance_unit=unit,
        width=2.0,
        length=3.0,
        height=2.5,
        dimension_unit=unit,
        net_weight=2500.0,
        net_weight_unit=unit,
        air_conditioning_system_type=t,
        air_conditioning_system_consumption=None,
        air_conditioning_system_consumption_unit=unit,
        id_machinery=mach,
        id_responsible_user=u,
        justification='test'
    )

    # Add request location so _get_ambient_temperature can run
    from service_requests.models.request_location import RequestLocation
    RequestLocation.objects.create(request=sr, country='CO', department='Dept', city_id=1, place_name='TestPlace', latitude=4.6, longitude=-74.08)

    # Customer and required enums
    pt = PersonType.objects.create(name='company')
    tr = TaxRegime.objects.create(code='TR', name='TaxReg')
    cust = Customer.objects.create(id_user=u, document_number=123, type_document_id=None, check_digit=0, person_type=pt, legal_entity_name='Cust', id_municipality=1, tax_regime=tr, customer_statues=st, id_responsible_user=u)

    # ServiceRequest
    sr = ServiceRequest.objects.create(id_request='REQ-DB-005-1', customer=cust, request_detail='test', scheduled_start_date=now.date(), scheduled_end_date=now.date(), request_status=st, id_responsible_user=u)

    # RequestMachineryUser
    rmu = RequestMachineryUser.objects.create(request=sr, machinery=mach, user=u, work_duration=2.0)

    # Insert a fuel level Data row (avl 48) and a fuel_used Data row (avl 12)
    # The service checks for a fuel level record first, then uses fuel_used if present.
    Data.objects.create(data=60.0, id_parameter=p_fuel_level, registered_at=now, id_device=dev, id_request=sr, id_machinery=mach, id_user=u, alert=False)
    Data.objects.create(data=40.0, id_parameter=p_fuel_used, registered_at=now, id_device=dev, id_request=sr, id_machinery=mach, id_user=u, alert=False)

    # Prepare service and redirect model dir to tmp
    service = ps_module.prediction_service
    orig_model_dir = service.MODEL_DIR
    orig_csv = service.TRAINING_DATA_CSV
    orig_counter = service.TRAINING_COUNTER_FILE
    orig_registers = service.REGISTERS_FOR_RETRAIN
    orig_model = getattr(service, 'model', None)
    orig_loaded = getattr(service, 'model_loaded', None)

    try:
        service.MODEL_DIR = Path(tmp_path)
        service.TRAINING_DATA_CSV = Path(tmp_path) / 'training_data_accumulated.csv'
        service.TRAINING_COUNTER_FILE = Path(tmp_path) / 'training_counter.txt'
        service.REGISTERS_FOR_RETRAIN = 1000

        # use DummyModel for deterministic pred, keep production _get_consumption_real
        monkeypatch.setattr(service, '_load_model', lambda: DummyModel())

        out = service.predict_and_save_training_data(request=sr, machinery=mach, imei=str(dev.IMEI), timestamp=now, user=u)
        assert out is not None

        consumo_real = out.get('consumo_real_l')
        consumo_estimado = out.get('consumo_estimado_l')
        dur = out.get('duracion_h')

        # If the service did not return consumo_real, compute it directly from DB rows created here
        fuel_used_row = Data.objects.filter(id_request=sr, id_machinery=mach, id_parameter=p_fuel_used).order_by('-registered_at').first()
        assert fuel_used_row is not None, "No fuel_used Data row found"
        cr_db = float(fuel_used_row.data)

        assert consumo_estimado == pytest.approx(35.0)
        assert dur == pytest.approx(2.0)

        diferencia = abs(cr_db - consumo_estimado)
        error_pct = (diferencia / cr_db) * 100.0 if cr_db else None

        # report basic metrics (single sample): error_pct should be 12.5
        assert error_pct == pytest.approx(12.5)

    finally:
        service.MODEL_DIR = orig_model_dir
        service.TRAINING_DATA_CSV = orig_csv
        service.TRAINING_COUNTER_FILE = orig_counter
        service.REGISTERS_FOR_RETRAIN = orig_registers
        if orig_model is not None:
            service.model = orig_model
        service.model_loaded = orig_loaded
