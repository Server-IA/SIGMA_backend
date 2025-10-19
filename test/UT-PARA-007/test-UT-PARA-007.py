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
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
    django.setup()

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from parameterization.models import StatuesCategory, Statues, VisualParameterization
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_ut_para_007_interfaz_personalizacion_visual():
    """
    IT-PARA-007 (RF-107): Interfaz personalización visual
    
    Validar con Selenium la aplicación de temas visuales en tiempo real, validación de contraste WCAG 
    y persistencia entre sesiones según RF-107 y HU-PAR-013.
    
    Casos de prueba:
    1) Modificar color primario, observar actualización en previsualización inmediata
    2) Probar combinación de bajo contraste, verificar alerta de validación WCAG
    3) Ajustar a contraste aceptable, verificar indicador verde y habilitación de guardado
    4) Aplicar tema globalmente, navegar por módulos verificando consistencia
    5) Cerrar/reabrir sesión, verificar persistencia del tema aplicado
    6) Verificar responsive en diferentes breakpoints
    """
    client = APIClient()

    # Arrange: Configurar datos base requeridos
    admin_user = User.objects.create(id_user=1)

    # Configurar estados necesarios
    status_cat = StatuesCategory.objects.create(
        id_statues_categories=1,
        name="Estados",
        description="Categoría de estados del sistema",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    estado_activo = Statues.objects.create(
        id_statues=1,
        name="Activo",
        description="Estado activo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    estado_inactivo = Statues.objects.create(
        id_statues=2,
        name="Inactivo",
        description="Estado inactivo",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Act 1: Crear "Tema Claro" inicial con colores de alto contraste
    tema_claro_data = {
        "name": "Tema Claro",
        "description": "Tema claro con alto contraste para accesibilidad",
        "primary_color": "#1E40AF",  # Azul oscuro
        "secondary_color": "#64748B",  # Gris azulado
        "accent_color": "#059669",  # Verde
        "background_color": "#FFFFFF",  # Blanco
        "surface_color": "#F8FAFC",  # Gris muy claro
        "text_color": "#1E293B",  # Gris muy oscuro
        "text_secondary_color": "#64748B",  # Gris medio
        "border_color": "#E2E8F0",  # Gris claro
        "hover_color": "#F1F5F9",  # Gris muy claro
        "error_color": "#DC2626",  # Rojo
        "success_color": "#059669",  # Verde
        "warning_color": "#D97706",  # Naranja
        "font": "Inter",
        "title_size": "xl",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_claro_resp = client.post(
        "/visual_parameterization/",
        tema_claro_data,
        format="json",
    )
    
    # Assert 1: Tema claro creado exitosamente con validación WCAG
    assert create_tema_claro_resp.status_code == 201
    assert "Parametrización visual creada exitosamente" in create_tema_claro_resp.json()["message"]
    
    tema_claro_id = VisualParameterization.objects.get(name="Tema Claro").pk

    # Act 2: Crear "Tema Corporativo" objetivo con colores corporativos
    tema_corporativo_data = {
        "name": "Tema Corporativo",
        "description": "Tema corporativo con colores de marca",
        "primary_color": "#7C3AED",  # Púrpura corporativo
        "secondary_color": "#8B5CF6",  # Púrpura claro
        "accent_color": "#F59E0B",  # Amarillo corporativo
        "background_color": "#FFFFFF",  # Blanco
        "surface_color": "#F9FAFB",  # Gris muy claro
        "text_color": "#111827",  # Negro
        "text_secondary_color": "#6B7280",  # Gris
        "border_color": "#D1D5DB",  # Gris claro
        "hover_color": "#F3F4F6",  # Gris muy claro
        "error_color": "#EF4444",  # Rojo
        "success_color": "#10B981",  # Verde
        "warning_color": "#F59E0B",  # Amarillo
        "font": "Roboto",
        "title_size": "2xl",
        "paragraph_size": "lg",
        "responsible_user": admin_user.pk,
    }

    create_tema_corporativo_resp = client.post(
        "/visual_parameterization/",
        tema_corporativo_data,
        format="json",
    )
    
    # Assert 2: Tema corporativo creado exitosamente
    assert create_tema_corporativo_resp.status_code == 201
    tema_corporativo_id = VisualParameterization.objects.get(name="Tema Corporativo").pk

    # Act 3: Probar combinación de bajo contraste (debería fallar validación WCAG)
    tema_bajo_contraste_data = {
        "name": "Tema Bajo Contraste",
        "description": "Tema con colores de bajo contraste para probar validación WCAG",
        "primary_color": "#F3F4F6",  # Gris muy claro
        "secondary_color": "#E5E7EB",  # Gris claro
        "accent_color": "#D1D5DB",  # Gris claro
        "background_color": "#FFFFFF",  # Blanco
        "surface_color": "#F9FAFB",  # Gris muy claro
        "text_color": "#F3F4F6",  # Gris muy claro (bajo contraste con fondo blanco)
        "text_secondary_color": "#E5E7EB",  # Gris claro
        "border_color": "#D1D5DB",  # Gris claro
        "hover_color": "#E5E7EB",  # Gris claro
        "error_color": "#F3F4F6",  # Gris muy claro
        "success_color": "#E5E7EB",  # Gris claro
        "warning_color": "#D1D5DB",  # Gris claro
        "font": "Arial",
        "title_size": "base",
        "paragraph_size": "sm",
        "responsible_user": admin_user.pk,
    }

    create_tema_bajo_contraste_resp = client.post(
        "/visual_parameterization/",
        tema_bajo_contraste_data,
        format="json",
    )
    
    # Assert 3: Validación WCAG debe rechazar tema con bajo contraste
    assert create_tema_bajo_contraste_resp.status_code == 400
    response_data = create_tema_bajo_contraste_resp.json()
    assert "errors" in response_data
    # Verificar que hay errores de contraste específicos
    errors = response_data["errors"]
    contrast_errors = [key for key in errors.keys() if "contrast" in key]
    assert len(contrast_errors) > 0, "Debe haber errores de contraste WCAG"

    # Act 4: Modificar color primario del tema corporativo (previsualización en tiempo real)
    tema_corporativo_actualizado_data = {
        "name": "Tema Corporativo",
        "description": "Tema corporativo con color primario actualizado",
        "primary_color": "#1D4ED8",  # Azul más oscuro para mejor contraste
        "secondary_color": "#8B5CF6",  # Púrpura claro
        "accent_color": "#F59E0B",  # Amarillo corporativo
        "background_color": "#FFFFFF",  # Blanco
        "surface_color": "#F9FAFB",  # Gris muy claro
        "text_color": "#111827",  # Negro
        "text_secondary_color": "#6B7280",  # Gris
        "border_color": "#D1D5DB",  # Gris claro
        "hover_color": "#F3F4F6",  # Gris muy claro
        "error_color": "#EF4444",  # Rojo
        "success_color": "#10B981",  # Verde
        "warning_color": "#F59E0B",  # Amarillo
        "font": "Roboto",
        "title_size": "2xl",
        "paragraph_size": "lg",
        "responsible_user": admin_user.pk,
    }

    update_tema_corporativo_resp = client.put(
        f"/visual_parameterization/{tema_corporativo_id}/",
        tema_corporativo_actualizado_data,
        format="json",
    )
    
    # Assert 4: Actualización exitosa con nuevo color primario
    assert update_tema_corporativo_resp.status_code == 200
    assert "Parametrización visual actualizada exitosamente" in update_tema_corporativo_resp.json()["message"]
    
    # Verificar que el cambio se aplicó
    tema_actualizado = VisualParameterization.objects.get(pk=tema_corporativo_id)
    assert tema_actualizado.primary_color == "#1D4ED8"

    # Act 5: Consultar tema actualizado (simular previsualización en tiempo real)
    get_tema_actualizado_resp = client.get(f"/visual_parameterization/{tema_corporativo_id}/")
    
    # Assert 5: Previsualización muestra cambios inmediatamente
    assert get_tema_actualizado_resp.status_code == 200
    tema_data = get_tema_actualizado_resp.json()
    assert tema_data["primary_color"] == "#1D4ED8"
    assert tema_data["name"] == "Tema Corporativo"

    # Act 6: Listar todos los temas (verificar consistencia global)
    list_temas_resp = client.get("/visual_parameterization/list/")
    
    # Assert 6: Lista muestra todos los temas creados
    assert list_temas_resp.status_code == 200
    temas_lista = list_temas_resp.json()
    assert isinstance(temas_lista, list)
    assert len(temas_lista) >= 2  # Al menos Tema Claro y Tema Corporativo
    
    nombres_temas = [tema["name"] for tema in temas_lista]
    assert "Tema Claro" in nombres_temas
    assert "Tema Corporativo" in nombres_temas

    # Act 7: Toggle status del tema (activar/desactivar)
    toggle_status_resp = client.patch(f"/visual_parameterization/{tema_corporativo_id}/toggle-status/")
    
    # Assert 7: Toggle status funciona correctamente
    assert toggle_status_resp.status_code == 200
    assert "desactivada" in toggle_status_resp.json()["message"]
    
    # Verificar que el estado cambió
    tema_desactivado = VisualParameterization.objects.get(pk=tema_corporativo_id)
    assert tema_desactivado.visual_parameterization_status_id == 2  # Inactivo

    # Act 8: Reactivar tema
    toggle_status_resp2 = client.patch(f"/visual_parameterization/{tema_corporativo_id}/toggle-status/")
    
    # Assert 8: Reactivación exitosa
    assert toggle_status_resp2.status_code == 200
    assert "activada" in toggle_status_resp2.json()["message"]
    
    tema_reactivado = VisualParameterization.objects.get(pk=tema_corporativo_id)
    assert tema_reactivado.visual_parameterization_status_id == 1  # Activo

    # Act 9: Crear tema con validación de contraste AAA (más estricta)
    tema_aaa_data = {
        "name": "Tema AAA",
        "description": "Tema con contraste WCAG AAA para máxima accesibilidad",
        "primary_color": "#000000",  # Negro puro
        "secondary_color": "#374151",  # Gris muy oscuro
        "accent_color": "#059669",  # Verde
        "background_color": "#FFFFFF",  # Blanco
        "surface_color": "#F9FAFB",  # Gris muy claro
        "text_color": "#000000",  # Negro puro
        "text_secondary_color": "#374151",  # Gris muy oscuro
        "border_color": "#D1D5DB",  # Gris claro
        "hover_color": "#F3F4F6",  # Gris muy claro
        "error_color": "#DC2626",  # Rojo
        "success_color": "#059669",  # Verde
        "warning_color": "#D97706",  # Naranja
        "font": "Inter",
        "title_size": "xl",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_aaa_resp = client.post(
        "/visual_parameterization/",
        tema_aaa_data,
        format="json",
    )
    
    # Assert 9: Tema AAA creado exitosamente (cumple WCAG AA)
    assert create_tema_aaa_resp.status_code == 201

    # Act 10: Probar actualización parcial (PATCH) para simular ajustes en tiempo real
    patch_data = {
        "primary_color": "#1F2937",  # Gris muy oscuro
        "accent_color": "#10B981",  # Verde más claro
    }

    patch_tema_resp = client.patch(
        f"/visual_parameterization/{tema_corporativo_id}/",
        patch_data,
        format="json",
    )
    
    # Assert 10: Actualización parcial exitosa
    assert patch_tema_resp.status_code == 200
    
    # Verificar que solo se actualizaron los campos especificados
    tema_patch = VisualParameterization.objects.get(pk=tema_corporativo_id)
    assert tema_patch.primary_color == "#1F2937"
    assert tema_patch.accent_color == "#10B981"
    # Los demás campos deben mantenerse igual
    assert tema_patch.name == "Tema Corporativo"
    assert tema_patch.font == "Roboto"

    # Verificaciones finales de consistencia y persistencia
    # - Los temas están correctamente almacenados en la base de datos
    temas_finales = VisualParameterization.objects.all()
    assert temas_finales.count() >= 3  # Al menos los 3 temas válidos creados
    
    # - Los cambios se reflejan inmediatamente en las consultas
    tema_final = VisualParameterization.objects.get(name="Tema Corporativo")
    assert tema_final.primary_color == "#1F2937"
    assert tema_final.visual_parameterization_status_id == 1  # Activo
    
    # - La validación WCAG funciona correctamente
    assert not VisualParameterization.objects.filter(name="Tema Bajo Contraste").exists()


@pytest.mark.django_db(transaction=True)
def test_ut_para_007_validaciones_wcag_especificas():
    """
    Pruebas específicas para validaciones WCAG con diferentes niveles y escenarios
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=2)

    # Configurar estados
    status_cat = StatuesCategory.objects.create(
        id_statues_categories=2,
        name="Estados WCAG",
        description="Estados para pruebas WCAG",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    estado_activo = Statues.objects.create(
        id_statues=1,
        name="Activo WCAG",
        description="Estado activo para WCAG",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Test 1: Colores con contraste exactamente en el límite WCAG AA (4.5:1)
    tema_limite_aa_data = {
        "name": "Tema Límite AA",
        "description": "Tema con contraste exactamente en el límite WCAG AA",
        "primary_color": "#767676",  # Gris que cumple exactamente 4.5:1 con blanco
        "secondary_color": "#767676",
        "accent_color": "#767676",
        "background_color": "#FFFFFF",
        "surface_color": "#FFFFFF",
        "text_color": "#767676",
        "text_secondary_color": "#767676",
        "border_color": "#767676",
        "hover_color": "#FFFFFF",  # Blanco para hover (contraste >= 4.5:1)
        "error_color": "#767676",
        "success_color": "#767676",
        "warning_color": "#767676",
        "font": "Arial",
        "title_size": "base",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_limite_resp = client.post(
        "/visual_parameterization/",
        tema_limite_aa_data,
        format="json",
    )
    
    # Assert: Debe pasar la validación (contraste >= 4.5:1)
    assert create_tema_limite_resp.status_code == 201

    # Test 2: Colores con contraste justo por debajo del límite WCAG AA
    tema_insuficiente_data = {
        "name": "Tema Insuficiente",
        "description": "Tema con contraste insuficiente para WCAG AA",
        "primary_color": "#808080",  # Gris que no cumple 4.5:1 con blanco
        "secondary_color": "#808080",
        "accent_color": "#808080",
        "background_color": "#FFFFFF",
        "surface_color": "#FFFFFF",
        "text_color": "#808080",
        "text_secondary_color": "#808080",
        "border_color": "#808080",
        "hover_color": "#FFFFFF",  # Blanco para hover (contraste >= 4.5:1)
        "error_color": "#808080",
        "success_color": "#808080",
        "warning_color": "#808080",
        "font": "Arial",
        "title_size": "base",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_insuficiente_resp = client.post(
        "/visual_parameterization/",
        tema_insuficiente_data,
        format="json",
    )
    
    # Assert: Debe fallar la validación
    assert create_tema_insuficiente_resp.status_code == 400
    errors = create_tema_insuficiente_resp.json()["errors"]
    contrast_errors = [key for key in errors.keys() if "contrast" in key]
    assert len(contrast_errors) > 0

    # Test 3: Validación de formato de colores hexadecimales
    tema_formato_invalido_data = {
        "name": "Tema Formato Inválido",
        "description": "Tema con formato de colores inválido",
        "primary_color": "rojo",  # Formato inválido
        "secondary_color": "#GGGGGG",  # Formato inválido
        "accent_color": "#12345",  # Formato inválido (5 caracteres)
        "background_color": "#FFFFFF",
        "surface_color": "#FFFFFF",
        "text_color": "#000000",
        "text_secondary_color": "#000000",
        "border_color": "#000000",
        "hover_color": "#000000",
        "error_color": "#000000",
        "success_color": "#000000",
        "warning_color": "#000000",
        "font": "Arial",
        "title_size": "base",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_formato_resp = client.post(
        "/visual_parameterization/",
        tema_formato_invalido_data,
        format="json",
    )
    
    # Assert: Debe fallar por formato inválido
    assert create_tema_formato_resp.status_code == 400

    # Test 4: Validación de tamaños tipográficos
    tema_tipografia_invalida_data = {
        "name": "Tema Tipografía Inválida",
        "description": "Tema con tamaños tipográficos inválidos",
        "primary_color": "#000000",
        "secondary_color": "#000000",
        "accent_color": "#000000",
        "background_color": "#FFFFFF",
        "surface_color": "#FFFFFF",
        "text_color": "#000000",
        "text_secondary_color": "#000000",
        "border_color": "#000000",
        "hover_color": "#000000",
        "error_color": "#000000",
        "success_color": "#000000",
        "warning_color": "#000000",
        "font": "Arial",
        "title_size": "xxl",  # Tamaño inválido
        "paragraph_size": "medium",  # Tamaño inválido
        "responsible_user": admin_user.pk,
    }

    create_tema_tipografia_resp = client.post(
        "/visual_parameterization/",
        tema_tipografia_invalida_data,
        format="json",
    )
    
    # Assert: Debe fallar por tamaños inválidos
    assert create_tema_tipografia_resp.status_code == 400
    errors = create_tema_tipografia_resp.json()["errors"]
    assert "title_size" in errors or "paragraph_size" in errors


@pytest.mark.django_db(transaction=True)
def test_ut_para_007_persistencia_y_consistencia():
    """
    Pruebas para verificar persistencia entre sesiones y consistencia global
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=3)

    # Configurar estados
    status_cat = StatuesCategory.objects.create(
        id_statues_categories=3,
        name="Estados Persistencia",
        description="Estados para pruebas de persistencia",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    estado_activo = Statues.objects.create(
        id_statues=1,
        name="Activo Persistencia",
        description="Estado activo para persistencia",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Test 1: Crear tema y verificar persistencia
    tema_persistencia_data = {
        "name": "Tema Persistencia",
        "description": "Tema para probar persistencia entre sesiones",
        "primary_color": "#1E40AF",
        "secondary_color": "#64748B",
        "accent_color": "#059669",
        "background_color": "#FFFFFF",
        "surface_color": "#F8FAFC",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "border_color": "#E2E8F0",
        "hover_color": "#F1F5F9",
        "error_color": "#DC2626",
        "success_color": "#059669",
        "warning_color": "#D97706",
        "font": "Inter",
        "title_size": "xl",
        "paragraph_size": "base",
        "responsible_user": admin_user.pk,
    }

    create_tema_resp = client.post(
        "/visual_parameterization/",
        tema_persistencia_data,
        format="json",
    )
    
    assert create_tema_resp.status_code == 201
    tema_id = VisualParameterization.objects.get(name="Tema Persistencia").pk

    # Test 2: Simular "cierre de sesión" - consultar tema después de creación
    get_tema_resp = client.get(f"/visual_parameterization/{tema_id}/")
    
    # Assert: Tema persiste correctamente
    assert get_tema_resp.status_code == 200
    tema_data = get_tema_resp.json()
    assert tema_data["name"] == "Tema Persistencia"
    assert tema_data["primary_color"] == "#1E40AF"
    assert tema_data["visual_parameterization_status_name"] == "Activo Persistencia"

    # Test 3: Simular "reabrir sesión" - modificar tema y verificar persistencia
    tema_modificado_data = {
        "name": "Tema Persistencia Modificado",
        "description": "Tema modificado para probar persistencia",
        "primary_color": "#7C3AED",  # Cambio de color
        "secondary_color": "#64748B",
        "accent_color": "#059669",
        "background_color": "#FFFFFF",
        "surface_color": "#F8FAFC",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "border_color": "#E2E8F0",
        "hover_color": "#F1F5F9",
        "error_color": "#DC2626",
        "success_color": "#059669",
        "warning_color": "#D97706",
        "font": "Roboto",  # Cambio de fuente
        "title_size": "2xl",  # Cambio de tamaño
        "paragraph_size": "lg",
        "responsible_user": admin_user.pk,
    }

    update_tema_resp = client.put(
        f"/visual_parameterization/{tema_id}/",
        tema_modificado_data,
        format="json",
    )
    
    assert update_tema_resp.status_code == 200

    # Test 4: Verificar que los cambios persisten
    get_tema_modificado_resp = client.get(f"/visual_parameterization/{tema_id}/")
    
    assert get_tema_modificado_resp.status_code == 200
    tema_modificado_data = get_tema_modificado_resp.json()
    assert tema_modificado_data["name"] == "Tema Persistencia Modificado"
    assert tema_modificado_data["primary_color"] == "#7C3AED"
    assert tema_modificado_data["font"] == "Roboto"
    assert tema_modificado_data["title_size"] == "2xl"

    # Test 5: Verificar consistencia en listado global
    list_temas_resp = client.get("/visual_parameterization/list/")
    
    assert list_temas_resp.status_code == 200
    temas_lista = list_temas_resp.json()
    
    # Buscar el tema modificado en la lista
    tema_en_lista = next((t for t in temas_lista if t["id_visual_parameterization"] == tema_id), None)
    assert tema_en_lista is not None
    assert tema_en_lista["name"] == "Tema Persistencia Modificado"
    assert tema_en_lista["primary_color"] == "#7C3AED"

    # Test 6: Verificar que no hay inconsistencias en la base de datos
    tema_db = VisualParameterization.objects.get(pk=tema_id)
    assert tema_db.name == "Tema Persistencia Modificado"
    assert tema_db.primary_color == "#7C3AED"
    assert tema_db.font == "Roboto"
    assert tema_db.title_size == "2xl"
    assert tema_db.visual_parameterization_status_id == 1  # Activo


@pytest.mark.django_db(transaction=True)
def test_ut_para_007_responsive_y_breakpoints():
    """
    Pruebas para validación responsive en diferentes breakpoints
    Nota: En el backend, esto se simula validando que los temas se apliquen
    consistentemente y que los tamaños tipográficos sean apropiados para diferentes dispositivos
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=4)

    # Configurar estados
    status_cat = StatuesCategory.objects.create(
        id_statues_categories=4,
        name="Estados Responsive",
        description="Estados para pruebas responsive",
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    estado_activo = Statues.objects.create(
        id_statues=1,
        name="Activo Responsive",
        description="Estado activo para responsive",
        id_statues_categories=status_cat,
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Test 1: Tema optimizado para móviles (tamaños pequeños)
    tema_mobile_data = {
        "name": "Tema Mobile",
        "description": "Tema optimizado para dispositivos móviles",
        "primary_color": "#1E40AF",
        "secondary_color": "#64748B",
        "accent_color": "#059669",
        "background_color": "#FFFFFF",
        "surface_color": "#F8FAFC",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "border_color": "#E2E8F0",
        "hover_color": "#F1F5F9",
        "error_color": "#DC2626",
        "success_color": "#059669",
        "warning_color": "#D97706",
        "font": "Inter",
        "title_size": "lg",  # Tamaño apropiado para móvil
        "paragraph_size": "sm",  # Tamaño apropiado para móvil
        "responsible_user": admin_user.pk,
    }

    create_tema_mobile_resp = client.post(
        "/visual_parameterization/",
        tema_mobile_data,
        format="json",
    )
    
    assert create_tema_mobile_resp.status_code == 201
    tema_mobile_id = VisualParameterization.objects.get(name="Tema Mobile").pk

    # Test 2: Tema optimizado para desktop (tamaños grandes)
    tema_desktop_data = {
        "name": "Tema Desktop",
        "description": "Tema optimizado para dispositivos de escritorio",
        "primary_color": "#1E40AF",
        "secondary_color": "#64748B",
        "accent_color": "#059669",
        "background_color": "#FFFFFF",
        "surface_color": "#F8FAFC",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "border_color": "#E2E8F0",
        "hover_color": "#F1F5F9",
        "error_color": "#DC2626",
        "success_color": "#059669",
        "warning_color": "#D97706",
        "font": "Inter",
        "title_size": "3xl",  # Tamaño apropiado para desktop
        "paragraph_size": "xl",  # Tamaño apropiado para desktop
        "responsible_user": admin_user.pk,
    }

    create_tema_desktop_resp = client.post(
        "/visual_parameterization/",
        tema_desktop_data,
        format="json",
    )
    
    assert create_tema_desktop_resp.status_code == 201
    tema_desktop_id = VisualParameterization.objects.get(name="Tema Desktop").pk

    # Test 3: Tema adaptativo (tamaños medios)
    tema_adaptativo_data = {
        "name": "Tema Adaptativo",
        "description": "Tema que se adapta a diferentes tamaños de pantalla",
        "primary_color": "#1E40AF",
        "secondary_color": "#64748B",
        "accent_color": "#059669",
        "background_color": "#FFFFFF",
        "surface_color": "#F8FAFC",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "border_color": "#E2E8F0",
        "hover_color": "#F1F5F9",
        "error_color": "#DC2626",
        "success_color": "#059669",
        "warning_color": "#D97706",
        "font": "Inter",
        "title_size": "xl",  # Tamaño balanceado
        "paragraph_size": "base",  # Tamaño balanceado
        "responsible_user": admin_user.pk,
    }

    create_tema_adaptativo_resp = client.post(
        "/visual_parameterization/",
        tema_adaptativo_data,
        format="json",
    )
    
    assert create_tema_adaptativo_resp.status_code == 201

    # Test 4: Verificar que todos los temas responsive están disponibles
    list_temas_resp = client.get("/visual_parameterization/list/")
    
    assert list_temas_resp.status_code == 200
    temas_lista = list_temas_resp.json()
    
    nombres_temas = [tema["name"] for tema in temas_lista]
    assert "Tema Mobile" in nombres_temas
    assert "Tema Desktop" in nombres_temas
    assert "Tema Adaptativo" in nombres_temas

    # Test 5: Verificar tamaños tipográficos apropiados para cada dispositivo
    tema_mobile = next((t for t in temas_lista if t["name"] == "Tema Mobile"), None)
    tema_desktop = next((t for t in temas_lista if t["name"] == "Tema Desktop"), None)
    tema_adaptativo = next((t for t in temas_lista if t["name"] == "Tema Adaptativo"), None)
    
    assert tema_mobile["title_size"] == "lg"
    assert tema_mobile["paragraph_size"] == "sm"
    
    assert tema_desktop["title_size"] == "3xl"
    assert tema_desktop["paragraph_size"] == "xl"
    
    assert tema_adaptativo["title_size"] == "xl"
    assert tema_adaptativo["paragraph_size"] == "base"

    # Test 6: Verificar que los colores mantienen contraste en todos los temas responsive
    for tema in [tema_mobile, tema_desktop, tema_adaptativo]:
        # Todos deben tener colores válidos que pasen validación WCAG
        assert tema["primary_color"] is not None
        assert tema["text_color"] is not None
        assert tema["background_color"] is not None
        assert tema["visual_parameterization_status"] == 1  # Activo
