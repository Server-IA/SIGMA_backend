import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from parameterization.models import StatuesCategory, Statues, TypesCategory
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_ut_para_005_endpoints_marcas_modelos_adaptado():
    client = APIClient()

    # Arrange: datos base requeridos por serializers (usuario y estados)
    admin_user = User.objects.create(id_user=1)

    status_cat = StatuesCategory.objects.create(
        id_statues_categories=1,
        name="Estados",
        description="Cat estados",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    Statues.objects.create(
        id_statues=1,
        name="Activo",
        description="Estado activo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )
    Statues.objects.create(
        id_statues=2,
        name="Inactivo",
        description="Estado inactivo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Arrange: Configurar marca "PowerPro" (TypesCategory) y modelo "PP5000" (Types)
    create_brand_resp = client.post(
        "/types_categories/",
        {
            "name": "PowerPro",
            "description": "Marca de potencia",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_brand_resp.status_code == 201

    brand_id = TypesCategory.objects.get(name="PowerPro").pk

    create_model_resp = client.post(
        "/types/",
        {
            "name": "PP5000",
            "description": "Modelo generador",
            "types_category": brand_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_model_resp.status_code == 201

    # Act 1: GET marcas (categorías) y verificar estructura
    list_brands_resp = client.get("/types_categories/list/")
    assert list_brands_resp.status_code == 200
    assert isinstance(list_brands_resp.json(), list)
    assert any(b.get("name") == "PowerPro" for b in list_brands_resp.json())

    # Act 2: POST nueva marca con nombre único
    create_brand_unique_resp = client.post(
        "/types_categories/",
        {
            "name": "TechPlus",
            "description": "Otra marca",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_brand_unique_resp.status_code == 201
    new_brand_id = TypesCategory.objects.get(name="TechPlus").pk

    # Act 3: POST modelo asociado a marca creada
    create_model_for_new_brand_resp = client.post(
        "/types/",
        {
            "name": "TP100",
            "description": "Modelo base",
            "types_category": new_brand_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_model_for_new_brand_resp.status_code == 201

    # Act 4: GET modelos filtrados por marca
    list_models_by_brand_resp = client.get(f"/types/list/{new_brand_id}/")
    assert list_models_by_brand_resp.status_code == 200
    models_payload = list_models_by_brand_resp.json()
    assert isinstance(models_payload, list)
    assert any(m.get("name") == "TP100" for m in models_payload)

    # Act 5: POST marca con nombre duplicado (valida unicidad). El serializer retorna 400.
    create_brand_dup_resp = client.post(
        "/types_categories/",
        {
            "name": "TechPlus",
            "description": "duplicada",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_brand_dup_resp.status_code == 400

    # Act 6: POST modelo sin marcaId válido (types_category inválido) -> 400 Bad Request
    create_model_bad_fk_resp = client.post(
        "/types/",
        {
            "name": "X1",
            "description": "Modelo sin marca",
            "types_category": 999999,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert create_model_bad_fk_resp.status_code == 400

    # Act 7: DELETE marca con modelos asociados.
    # En la implementación actual no hay endpoint DELETE -> 405 Method Not Allowed.
    delete_brand_resp = client.delete(f"/types_categories/{new_brand_id}/")
    assert delete_brand_resp.status_code == 405

    # Assert finales (consistencia jerárquica y validaciones)
    # - Jerarquía mantenida: el listado por categoría devuelve el modelo esperado
    assert any(m.get("name") == "TP100" for m in models_payload)
    # - Validación de unicidad de nombres de categoría
    assert create_brand_dup_resp.status_code == 400
    # - Asociación obligatoria modelo-marca (FK requerida)
    assert create_model_bad_fk_resp.status_code == 400


