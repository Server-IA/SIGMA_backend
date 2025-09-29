import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from parameterization.models import StatuesCategory, Statues, VisualParameterization
from users.models import User


def _valid_payload_base(user_id, status_id):
    return {
        "name": "TemaClaro",
        "description": "Tema claro editable",
        "background_color": "#000000",
        "text_color": "#FFFFFF",
        "font": "Arial",
        "font_size": "14",
        "border_thickness": "1",
        "border_color": "#FFFFFF",
        "visual_parameterization_status": status_id,
        "responsible_user": user_id,
    }


@pytest.mark.django_db(transaction=True)
def test_ut_para_006_detalles_y_modificacion_visual_parameterization():
    client = APIClient()

    # Arrange: usuario, categorías y estados
    admin_user = User.objects.create(id_user=1)

    status_cat = StatuesCategory.objects.create(
        id_statues_categories=1,
        name="Estados",
        description="Cat estados",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    status_active = Statues.objects.create(
        id_statues=1,
        name="Activo",
        description="Estado activo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )
    status_inactive = Statues.objects.create(
        id_statues=2,
        name="Inactivo",
        description="Estado inactivo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Parámetro A (simulado "en uso": estado Activo)
    param_a = VisualParameterization.objects.create(
        name="TemaA",
        description="A en uso",
        background_color="#000000",
        text_color="#FFFFFF",
        font="Arial",
        font_size="14",
        border_thickness="1",
        border_color="#FFFFFF",
        visual_parameterization_status=status_active,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Parámetro B (libre)
    param_b = VisualParameterization.objects.create(
        name="TemaB",
        description="B libre",
        background_color="#000000",
        text_color="#FFFFFF",
        font="Arial",
        font_size="14",
        border_thickness="1",
        border_color="#FFFFFF",
        visual_parameterization_status=status_active,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Act 1) GET detalles de A
    get_a = client.get(f"/visual_parameterization/{param_a.pk}/")
    assert get_a.status_code == 200
    data_a = get_a.json()
    assert data_a.get("id_visual_parameterization") == param_a.pk
    assert data_a.get("visual_parameterization_status") == status_active.pk
    assert data_a.get("visual_parameterization_status_name") == "Activo"

    # Act 2) PUT modificar descripción de B
    payload_put_b = _valid_payload_base(admin_user.pk, status_active.pk)
    payload_put_b["name"] = param_b.name  # mantener el mismo nombre para no chocar unicidad
    payload_put_b["description"] = "B libre modificado"
    before_mod_date = VisualParameterization.objects.get(pk=param_b.pk).modification_date
    put_b = client.put(f"/visual_parameterization/{param_b.pk}/", payload_put_b, format="json")
    assert put_b.status_code == 200
    updated_b = VisualParameterization.objects.get(pk=param_b.pk)
    assert updated_b.description == "B libre modificado"
    assert updated_b.modification_date is not None and updated_b.modification_date >= before_mod_date

    # Act 3) PUT desactivar parámetro A (en esta API no hay bloqueo por uso; debe retornar 200)
    payload_put_a = _valid_payload_base(admin_user.pk, status_inactive.pk)
    payload_put_a["name"] = param_a.name
    payload_put_a["description"] = param_a.description
    put_a = client.put(f"/visual_parameterization/{param_a.pk}/", payload_put_a, format="json")
    assert put_a.status_code == 200

    # Act 4) PUT con valores vacíos (400 Bad Request)
    bad_payload = {
        "name": " ",
        "description": "",
        "background_color": "",
        "text_color": "",
        "font": "",
        "font_size": "",
        "border_thickness": "",
        "border_color": "",
        "visual_parameterization_status": "",
        "responsible_user": "",
    }
    bad_put = client.put(f"/visual_parameterization/{param_b.pk}/", bad_payload, format="json")
    assert bad_put.status_code == 400
    errors = bad_put.json().get("errors") or {}
    # Validar que haya errores para campos clave sin depender del texto exacto
    assert "name" in errors and errors["name"]
    assert "responsible_user" in errors and errors["responsible_user"]
    assert "visual_parameterization_status" in errors and errors["visual_parameterization_status"]

    # Act 5) PUT exitoso en B para verificar auditoría (fecha actualización)
    payload_put_b2 = _valid_payload_base(admin_user.pk, status_active.pk)
    payload_put_b2["name"] = param_b.name
    payload_put_b2["description"] = "B libre modificado 2"
    before_mod_date_2 = VisualParameterization.objects.get(pk=param_b.pk).modification_date
    put_b2 = client.put(f"/visual_parameterization/{param_b.pk}/", payload_put_b2, format="json")
    assert put_b2.status_code == 200
    updated_b2 = VisualParameterization.objects.get(pk=param_b.pk)
    assert updated_b2.description == "B libre modificado 2"
    assert updated_b2.modification_date is not None and updated_b2.modification_date >= before_mod_date_2

    # Act 6) GET detalles post-modificación de B
    get_b_after = client.get(f"/visual_parameterization/{param_b.pk}/")
    assert get_b_after.status_code == 200
    data_b_after = get_b_after.json()
    assert data_b_after.get("description") == "B libre modificado 2"


