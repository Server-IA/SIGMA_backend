def get_actor_info(current_user):
    """
    Extrae actor_id, actor_name y actor_role_name del usuario autenticado,
    asegurando compatibilidad con distintos tipos de user (objeto JWTUser, dict, etc.).
    """
    if not current_user:
        return "Sistema", "Sistema", "Sistema"

    # actor_id
    actor_id = None
    if hasattr(current_user, "id"):
        actor_id = str(getattr(current_user, "id", "")) or "Sistema"
    elif isinstance(current_user, dict):
        actor_id = str(current_user.get("id", "")) or "Sistema"
    else:
        actor_id = "Sistema"

    # actor_name — revisamos varios lugares
    actor_name = "Sistema"
    if hasattr(current_user, "name") and getattr(current_user, "name"):
        actor_name = str(getattr(current_user, "name"))
    elif hasattr(current_user, "username") and getattr(current_user, "username"):
        actor_name = str(getattr(current_user, "username"))
    elif hasattr(current_user, "email") and getattr(current_user, "email"):
        actor_name = str(getattr(current_user, "email"))
    elif hasattr(current_user, "_request") and hasattr(current_user._request, "auth"):
        auth = current_user._request.auth or {}
        actor_name = str(auth.get("name") or auth.get("username") or "Sistema")
    elif isinstance(current_user, dict):
        actor_name = str(current_user.get("name") or current_user.get("username") or "Sistema")

    # actor_role
    role_name = "Usuario"
    if hasattr(current_user, "_request") and hasattr(current_user._request, "auth"):
        auth = current_user._request.auth or {}
        roles = auth.get("rol") or auth.get("roles") or []
        if roles and isinstance(roles, list) and len(roles) > 0:
            role = roles[0]
            if isinstance(role, dict):
                role_name = str(role.get("name", "Usuario"))
    
    return str(actor_id), str(actor_name), str(role_name)

def contract_snapshot(contract):
    """
    Crea un snapshot del contrato para auditoría.
    
    Args:
        contract: Instancia del modelo EstablishedContract
        
    Returns:
        dict: Diccionario con los campos relevantes del contrato
    """
    if not contract:
        return {}
        
    return {
        'contract_code': contract.contract_code,
        'id_employee_charge': contract.id_employee_charge_id,
        'contract_type': contract.contract_type_id,
        'start_date': str(contract.start_date),
        'end_date': str(contract.end_date) if contract.end_date else None,
        'status': contract.status_id,
        'salary_base': str(contract.salary_base) if contract.salary_base else None,
        'payment_frequency_type': contract.payment_frequency_type,
        'created_at': str(contract.created_at) if contract.created_at else None,
        'created_by': contract.created_by_id
    }
