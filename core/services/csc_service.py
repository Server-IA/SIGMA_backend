import os
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    base = os.getenv('CSC_API_BASE_URL').rstrip('/')
    return base


def _get_headers() -> Dict[str, str]:
    # La variable de entorno se define con guiones bajos para compatibilidad de Docker/OS
    api_key = os.getenv('X_CSCAPI_KEY')
    headers = {}
    if api_key:
        # El nombre del header HTTP sí lleva guiones, según la documentación de CSC
        headers['X-CSCAPI-KEY'] = api_key
    else:
        logger.warning('CSC API key no configurada (X_CSCAPI_KEY)')
    return headers


def _safe_get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Optional[Any]:
    try:
        resp = requests.get(url, headers=_get_headers(), params=params or {}, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        logger.warning('CSC API %s -> %s', url, resp.status_code)
        return None
    except requests.exceptions.RequestException as e:
        logger.error('CSC API error calling %s: %s', url, str(e))
        return None


@lru_cache(maxsize=1)
def get_countries() -> List[Dict[str, Any]]:
    url = f"{_get_base_url()}/countries"
    data = _safe_get(url)
    return data or []


@lru_cache(maxsize=128)
def get_states(country_iso2: str) -> List[Dict[str, Any]]:
    if not country_iso2:
        return []
    code = str(country_iso2).strip()
    url = f"{_get_base_url()}/countries/{code}/states"
    data = _safe_get(url)
    return data or []


@lru_cache(maxsize=1024)
def get_cities(country_iso2: str, state_iso2: str) -> List[Dict[str, Any]]:
    if not country_iso2 or not state_iso2:
        return []
    c = str(country_iso2).strip()
    s = str(state_iso2).strip()
    url = f"{_get_base_url()}/countries/{c}/states/{s}/cities"
    data = _safe_get(url)
    return data or []


def resolve_country_name(code_or_name: Optional[str]) -> Optional[str]:
    if not code_or_name:
        return None
    value = str(code_or_name).strip()
    # If already looks like a descriptive name (>2 chars), try to confirm; else return as is
    countries = get_countries()
    # First: try ISO2 match (case-insensitive)
    for c in countries:
        if str(c.get('iso2', '')).strip().lower() == value.lower():
            return c.get('name') or value
    # Second: try ISO3 match
    for c in countries:
        if str(c.get('iso3', '')).strip().lower() == value.lower():
            return c.get('name') or value
    # Third: name match (case-insensitive)
    for c in countries:
        if str(c.get('name', '')).strip().lower() == value.lower():
            return c.get('name')
    return value


def get_country_iso2(code_or_name: Optional[str]) -> Optional[str]:
    if not code_or_name:
        return None
    value = str(code_or_name).strip()
    countries = get_countries()
    # ISO2 direct
    for c in countries:
        if str(c.get('iso2', '')).strip().lower() == value.lower():
            return c.get('iso2')
    # ISO3
    for c in countries:
        if str(c.get('iso3', '')).strip().lower() == value.lower():
            return c.get('iso2')
    # Name
    for c in countries:
        if str(c.get('name', '')).strip().lower() == value.lower():
            return c.get('iso2')
    return None


def get_state_iso2(country_code_or_name: Optional[str], state_code_or_name: Optional[str]) -> Optional[str]:
    if not country_code_or_name or not state_code_or_name:
        return None
    country_iso2 = get_country_iso2(country_code_or_name) or str(country_code_or_name).strip()
    states = get_states(country_iso2)
    val = str(state_code_or_name).strip()
    # ISO2 direct
    for s in states:
        if str(s.get('iso2', '')).strip().lower() == val.lower():
            return s.get('iso2')
    # Name
    for s in states:
        if str(s.get('name', '')).strip().lower() == val.lower():
            return s.get('iso2')
    return None


def resolve_state_name(country_code: Optional[str], code_or_name: Optional[str]) -> Optional[str]:
    if not code_or_name:
        return None
    value = str(code_or_name).strip()
    if not country_code:
        return value
    states = get_states(str(country_code).strip())
    # Try ISO2 match
    for s in states:
        if str(s.get('iso2', '')).strip().lower() == value.lower():
            return s.get('name') or value
    # Try name match
    for s in states:
        if str(s.get('name', '')).strip().lower() == value.lower():
            return s.get('name')
    return value


def resolve_city_name(country_code: Optional[str], state_code: Optional[str], id_or_name: Optional[Any]) -> Optional[str]:
    if id_or_name is None:
        return None
    value_str = str(id_or_name).strip()
    if not country_code or not state_code:
        return value_str
    cities = get_cities(str(country_code).strip(), str(state_code).strip())
    # Try ID numeric match if possible
    try:
        value_id = int(value_str)
    except Exception:
        value_id = None
    if value_id is not None:
        for ct in cities:
            # CSC 'id' is int
            if str(ct.get('id')) == str(value_id):
                return ct.get('name') or value_str
    # Try name match
    for ct in cities:
        if str(ct.get('name', '')).strip().lower() == value_str.lower():
            return ct.get('name')
    return value_str


