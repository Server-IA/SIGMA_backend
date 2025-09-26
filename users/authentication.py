from typing import Optional, Tuple

import os
import jwt
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import cached_property
from rest_framework import authentication, exceptions


class JWTUser:
    """Ligero envoltorio para exponer un usuario autenticado desde un JWT sin tocar el modelo User de Django."""

    def __init__(self, user_id: int, email: str, name: Optional[str], raw_payload: dict):
        self.id = user_id
        self.email = email
        self.name = name
        self._raw_payload = raw_payload

    @property
    def is_authenticated(self) -> bool:  # DRF espera esta propiedad
        return True

    @cached_property
    def roles(self):
        return self._raw_payload.get("rol") or self._raw_payload.get("roles") or []

    @cached_property
    def permissions(self):
        permisos = []
        for rol in self.roles or []:
            role_perms = (rol or {}).get("permisos")
            if role_perms is None:
                role_perms = (rol or {}).get("permissions")
            for permiso in role_perms or []:
                if isinstance(permiso, dict):
                    permisos.append(permiso)
        return permisos


class JWTAuthentication(authentication.BaseAuthentication):
    """Autenticación por header Authorization: Bearer <JWT> usando HS256.

    - Decodifica el token con la clave secreta (JWT_SECRET o SECRET_KEY).
    - Expone el payload en request.auth y un JWTUser en request.user.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request) -> Optional[Tuple[JWTUser, dict]]:
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(" ", 1)
        except ValueError:
            raise exceptions.AuthenticationFailed("Formato de Authorization inválido. Use 'Bearer <token>'.")

        if prefix.lower() != "bearer":
            return None

        secret = os.getenv("JWT_SECRET")
        algorithms = ["HS256"]
        try:
            payload = jwt.decode(token, secret, algorithms=algorithms)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expirado.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Token inválido.")

        user_id = payload.get("id")
        email = payload.get("email") or payload.get("sub")
        if user_id is None or email is None:
            raise exceptions.AuthenticationFailed("El token no contiene campos requeridos (id/email).")

        user = JWTUser(user_id=user_id, email=email, name=payload.get("name"), raw_payload=payload)
        return user, payload

    def authenticate_header(self, request) -> str:
        return f'Bearer realm="{self.www_authenticate_realm}"'


