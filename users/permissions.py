from typing import Optional

from rest_framework.permissions import BasePermission


class HasPermissionId(BasePermission):
    """Verifica que el JWT incluya el id de permiso requerido por la vista.

    Uso:
      - En una vista/configurar atributo `required_permission_id = 27` (int)
      - O definir método `get_required_permission_id(self, request)` que retorne el id (int)
    El JWT esperado tiene `rol: [{ permisos: [{id:int, name:str}, ...] }]`.
    """

    message = "No tiene el permiso requerido para acceder a este recurso."

    def has_permission(self, request, view) -> bool:
        required_id = self._get_required_permission_id(request, view)
        if required_id is None:
            # Si la vista no declara permiso, denegamos por defecto para evitar endpoints sin protección accidental.
            return False

        user = getattr(request, "user", None)
        payload = getattr(request, "auth", None) or {}

        if not getattr(user, "is_authenticated", False):
            return False

        # Reunir ids de permisos del token aceptando distintos formatos
        permission_ids = set()

        # Roles: "rol" (es) o "roles" (en)
        roles = payload.get("rol") or payload.get("roles") or []
        for role in roles or []:
            # Permisos: "permisos" (es) o "permissions" (en)
            perms = (role or {}).get("permisos")
            if perms is None:
                perms = (role or {}).get("permissions")
            for permiso in perms or []:
                try:
                    permission_ids.add(int(permiso.get("id")))
                except Exception:
                    continue

        # Algunos JWT podrían traer permisos a nivel top (fallback)
        top_perms = payload.get("permisos") or payload.get("permissions") or []
        for permiso in top_perms or []:
            try:
                permission_ids.add(int(permiso.get("id")))
            except Exception:
                continue

        return int(required_id) in permission_ids

    def _get_required_permission_id(self, request, view) -> Optional[int]:
        if hasattr(view, "get_required_permission_id"):
            try:
                return int(view.get_required_permission_id(request))
            except Exception:
                return None
        if hasattr(view, "required_permission_id"):
            try:
                return int(getattr(view, "required_permission_id"))
            except Exception:
                return None
        return None


