import os
import django
from django.conf import settings

# Configurar variables de entorno necesarias para las pruebas
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-unit-testing-only')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('ALLOWED_HOSTS', '*')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ.setdefault('DB_USER', 'test_user')
os.environ.setdefault('DB_PASSWORD', 'test_pass')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')

# Configurar Django antes de importar los modelos
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
    django.setup()

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from parameterization.models import StatuesCategory, Statues, TypesCategory, Types
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_ut_para_002_endpoints_crud_tipos_globales():
    """
    UT-PARA-002 (RF-101): Endpoints CRUD tipos globales
    
    Valida operaciones CRUD sobre tipos globales asociados a categorías en los endpoints,
    asegurando validaciones de duplicados, unicidad y restricciones de eliminación con
    referencias activas.
    """
    client = APIClient()

    # Arrange: Datos base requeridos por serializers (usuario y estados)
    admin_user = User.objects.create(id_user=1)

    # Crear categoría de estados
    status_cat = StatuesCategory.objects.create(
        id_statues_categories=1,
        name="Estados",
        description="Categoría de estados del sistema",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Crear estados necesarios (Activo e Inactivo)
    estado_activo = Statues.objects.create(
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

    # Arrange: Crear categoría de tipos "Mantenimiento" con tipo "Preventivo"
    categoria_mantenimiento_resp = client.post(
        "/types_categories/",
        {
            "name": "Mantenimiento",
            "description": "Categoría de tipos de mantenimiento",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_mantenimiento_resp.status_code == 201

    # Obtener ID de la categoría creada
    categoria_mantenimiento = TypesCategory.objects.get(name="Mantenimiento")
    categoria_id = categoria_mantenimiento.pk

    # Crear tipo "Preventivo" inicial
    tipo_preventivo_resp = client.post(
        "/types/",
        {
            "name": "Preventivo",
            "description": "Tipo de mantenimiento preventivo",
            "types_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert tipo_preventivo_resp.status_code == 201

    # Obtener ID del tipo preventivo creado
    tipo_preventivo = Types.objects.get(name="Preventivo")
    tipo_preventivo_id = tipo_preventivo.pk

    # Act 1: Crear un nuevo tipo "Correctivo" con POST /types
    nuevo_tipo_resp = client.post(
        "/types/",
        {
            "name": "Correctivo",
            "description": "Tipo de mantenimiento correctivo aplicado a fallas detectadas",
            "types_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 1: Paso 1 devuelve 201 Created con ID asignado
    assert nuevo_tipo_resp.status_code == 201
    assert "message" in nuevo_tipo_resp.json()
    
    # Verificar que el tipo fue creado correctamente
    tipo_correctivo = Types.objects.get(name="Correctivo")
    assert tipo_correctivo.description == "Tipo de mantenimiento correctivo aplicado a fallas detectadas"
    assert tipo_correctivo.id_types_categories == categoria_mantenimiento

    # Act 2: Consultar lista con GET /types/list/{categoria_id} para confirmar la creación
    lista_tipos_resp = client.get(f"/types/list/{categoria_id}/")
    
    # Assert 2: Paso 2 muestra lista con ["Preventivo","Correctivo"]
    assert lista_tipos_resp.status_code == 200
    tipos_data = lista_tipos_resp.json()
    assert isinstance(tipos_data, list)
    nombres_tipos = [tipo["name"] for tipo in tipos_data]
    assert "Preventivo" in nombres_tipos
    assert "Correctivo" in nombres_tipos
    assert len(nombres_tipos) == 2

    # Act 3: Editar tipo existente con PUT /types/{id}
    editar_tipo_resp = client.put(
        f"/types/{tipo_preventivo_id}/",
        {
            "name": "Preventi ovo",
            "description": "Tipo de mantenimiento preventivo editado",
            "types_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 3: Paso 3 devuelve 200 OK y lista muestra "Preventi ovo"
    assert editar_tipo_resp.status_code == 200
    assert "message" in editar_tipo_resp.json()
    
    # Verificar que el cambio se aplicó
    tipo_editado = Types.objects.get(pk=tipo_preventivo_id)
    assert tipo_editado.name == "Preventi ovo"
    
    # Verificar en la lista actualizada
    lista_tipos_actualizada_resp = client.get(f"/types/list/{categoria_id}/")
    assert lista_tipos_actualizada_resp.status_code == 200
    tipos_actualizados = lista_tipos_actualizada_resp.json()
    nombres_actualizados = [tipo["name"] for tipo in tipos_actualizados]
    assert "Preventi ovo" in nombres_actualizados
    assert "Preventivo" not in nombres_actualizados

    # Act 4: Intentar crear un tipo duplicado con POST /types
    tipo_duplicado_resp = client.post(
        "/types/",
        {
            "name": "Correctivo",  # Nombre ya existente
            "description": "Intento de duplicar tipo",
            "types_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 4: Paso 4 devuelve 400 Bad Request con mensaje de error por duplicado
    assert tipo_duplicado_resp.status_code == 400
    # El modelo Types tiene unique=True en el campo name, por lo que Django devuelve error
    assert "name" in tipo_duplicado_resp.json() or "error" in tipo_duplicado_resp.json()

    # Act 5: Probar toggle de status (desactivar tipo)
    toggle_status_resp = client.patch(f"/types/{tipo_correctivo.pk}/toggle-status/")
    
    # Assert 5: Toggle status funciona correctamente
    assert toggle_status_resp.status_code == 200
    assert "message" in toggle_status_resp.json()
    
    # Verificar que el tipo fue desactivado
    tipo_correctivo_actualizado = Types.objects.get(pk=tipo_correctivo.pk)
    assert tipo_correctivo_actualizado.id_statues.pk == 2  # Estado inactivo

    # Act 6: Consultar solo tipos activos
    tipos_activos_resp = client.get(f"/types/list/active/{categoria_id}/")
    
    # Assert 6: Solo devuelve tipos activos
    assert tipos_activos_resp.status_code == 200
    tipos_activos_data = tipos_activos_resp.json()
    nombres_activos = [tipo["name"] for tipo in tipos_activos_data]
    assert "Preventi ovo" in nombres_activos  # Este sigue activo
    assert "Correctivo" not in nombres_activos  # Este fue desactivado

    # Act 7: Reactivar tipo
    toggle_status_reactivar_resp = client.patch(f"/types/{tipo_correctivo.pk}/toggle-status/")
    
    # Assert 7: Reactivación exitosa
    assert toggle_status_reactivar_resp.status_code == 200
    tipo_correctivo_reactivado = Types.objects.get(pk=tipo_correctivo.pk)
    assert tipo_correctivo_reactivado.id_statues.pk == 1  # Estado activo

    # Act 8: Intentar eliminar categoría que tiene tipos asociados (no hay endpoint DELETE pero probamos)
    delete_categoria_resp = client.delete(f"/types_categories/{categoria_id}/")
    
    # Assert 8: Método no permitido o restricción por FK
    assert delete_categoria_resp.status_code == 405  # Method not allowed

    # Act 9: Consultar categorías disponibles
    lista_categorias_resp = client.get("/types_categories/list/")
    
    # Assert 9: Lista de categorías incluye la creada
    assert lista_categorias_resp.status_code == 200
    categorias_data = lista_categorias_resp.json()
    assert isinstance(categorias_data, list)
    nombres_categorias = [cat["name"] for cat in categorias_data]
    assert "Mantenimiento" in nombres_categorias

    # Verificaciones finales de consistencia
    # - Jerarquía mantenida: tipos asociados a su categoría
    tipos_finales = Types.objects.filter(id_types_categories=categoria_mantenimiento)
    assert tipos_finales.count() == 2
    
    # - Validación de unicidad: no pueden existir dos tipos con el mismo nombre
    nombres_tipos_finales = list(tipos_finales.values_list('name', flat=True))
    assert len(nombres_tipos_finales) == len(set(nombres_tipos_finales))  # Sin duplicados
    
    # - Estados manejados correctamente
    assert Types.objects.filter(id_statues=estado_activo).count() == 2  # Ambos tipos activos


@pytest.mark.django_db(transaction=True)
def test_ut_para_002_validaciones_restricciones():
    """
    Pruebas adicionales para validar restricciones específicas del caso UT-PARA-002
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=2)

    status_cat = StatuesCategory.objects.create(
        id_statues_categories=2,
        name="Estados Test",
        description="Cat estados test",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    Statues.objects.create(
        id_statues=3,
        name="Activo Test",
        description="Estado activo test",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Test: Crear categoría con nombre duplicado
    client.post(
        "/types_categories/",
        {
            "name": "Duplicada",
            "description": "Primera categoría",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )

    # Intentar crear otra con el mismo nombre
    categoria_dup_resp = client.post(
        "/types_categories/",
        {
            "name": "Duplicada",
            "description": "Segunda categoría",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )

    # Assert: Validación de duplicados en categorías
    assert categoria_dup_resp.status_code == 400
    assert "nombre" in str(categoria_dup_resp.json()).lower()

    # Test: Crear tipo sin categoría válida
    tipo_sin_categoria_resp = client.post(
        "/types/",
        {
            "name": "Tipo Sin Categoría",
            "description": "Tipo sin categoría válida",
            "types_category": 99999,  # ID inexistente
            "responsible_user": admin_user.pk,
        },
        format="json",
    )

    # Assert: Error por FK inválida
    assert tipo_sin_categoria_resp.status_code == 400

    # Test: Consultar tipos de categoría inexistente
    tipos_categoria_inexistente_resp = client.get("/types/list/99999/")
    
    # Assert: Error por categoría no encontrada
    assert tipos_categoria_inexistente_resp.status_code == 404

    # Test: Editar tipo inexistente
    editar_inexistente_resp = client.put(
        "/types/99999/",
        {
            "name": "Tipo Inexistente",
            "description": "No existe",
        },
        format="json",
    )

    # Assert: Error por tipo no encontrado
    assert editar_inexistente_resp.status_code == 404

    # Test: Toggle status de tipo inexistente
    toggle_inexistente_resp = client.patch("/types/99999/toggle-status/")
    
    # Assert: Error por tipo no encontrado
    assert toggle_inexistente_resp.status_code == 404
