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
    Crea un snapshot completo del contrato para auditoría.
    Incluye todos los campos del modelo EstablishedContract y sus relaciones.
    
    Args:
        contract: Instancia del modelo EstablishedContract
        
    Returns:
        dict: Diccionario con todos los campos del contrato y sus relaciones
    """
    if not contract:
        return {}
    
    def safe_get_attr(obj, attr, default=None):
        """Safely get attribute with default value if not exists"""
        if not hasattr(obj, attr):
            return default
        value = getattr(obj, attr)
        return value if value is not None else default
    
    def safe_str_date(date_obj):
        """Safely convert date to string"""
        return str(date_obj) if date_obj else None

    # Get contract data
    # Get days_of_week as a list of day numbers
    days_of_week = []
    if hasattr(contract, 'days_of_week') and contract.days_of_week.exists():
        days_of_week = list(contract.days_of_week.values_list('id_day_of_week', flat=True))
    
    snapshot = {
        # Basic Info
        'id_employee_charge': safe_get_attr(contract, 'id_employee_charge_id'),
        'description': safe_get_attr(contract, 'description'),
        'contract_type': safe_get_attr(contract, 'contract_type_id'),
        'start_date': safe_str_date(safe_get_attr(contract, 'start_date')),
        'end_date': safe_str_date(safe_get_attr(contract, 'end_date')),
        'payment_frequency_type': safe_get_attr(contract, 'payment_frequency_type'),
        'minimum_hours': safe_get_attr(contract, 'minimum_hours'),
        'workday_type': safe_get_attr(contract, 'workday_type_id'),
        'work_mode_type': safe_get_attr(contract, 'work_mode_type_id'),
        'salary_type': safe_get_attr(contract, 'salary_type'),
        'salary_base': float(safe_get_attr(contract, 'salary_base', 0)),
        'currency_type': safe_get_attr(contract, 'currency_type_id'),
        'trial_period_days': safe_get_attr(contract, 'trial_period_days'),
        'vacation_days': safe_get_attr(contract, 'vacation_days', 0),
        'vacation_frequency_days': safe_get_attr(contract, 'vacation_frequency_days'),
        'cumulative_vacation': bool(safe_get_attr(contract, 'cumulative_vacation', False)),
        'start_cumulative_vacation': safe_str_date(safe_get_attr(contract, 'start_cumulative_vacation')),
        'maximum_disability_days': safe_get_attr(contract, 'maximum_disability_days', 0),
        'overtime': float(safe_get_attr(contract, 'overtime', 0)),
        'overtime_period': safe_get_attr(contract, 'overtime_period'),
        'notice_period_days': safe_get_attr(contract, 'notice_period_days'),
        'days_of_week': days_of_week,
        'established_contract_status': safe_get_attr(contract, 'established_contract_status_id'),
        'id_responsible_user': safe_get_attr(contract, 'id_responsible_user_id'),
        'contract_payments': [],
        'established_deductions': [],
        'established_increases': []
    }

    # Add contract payments
    if hasattr(contract, 'contract_payments'):
        for payment in contract.contract_payments.all():
            snapshot['contract_payments'].append({
                'id_day_of_week': safe_get_attr(payment, 'id_day_of_week_id'),
                'date_payment': safe_get_attr(payment, 'date_payment')
            })

    # Add established deductions
    if hasattr(contract, 'established_deductions'):
        for deduction in contract.established_deductions.all():
            snapshot['established_deductions'].append({
                'deduction_type': safe_get_attr(deduction, 'deduction_type_id'),
                'amount_type': safe_get_attr(deduction, 'amount_type'),
                'amount_value': float(safe_get_attr(deduction, 'amount_value', 0)),
                'application_deduction_type': safe_get_attr(deduction, 'application_deduction_type'),
                'start_date_deduction': safe_str_date(safe_get_attr(deduction, 'start_date_deduction')),
                'end_date_deductions': safe_str_date(safe_get_attr(deduction, 'end_date_deductions')),
                'description': safe_get_attr(deduction, 'description'),
                'amount': float(safe_get_attr(deduction, 'amount', 0))
            })

    # Add established increases
    if hasattr(contract, 'established_increases'):
        for increase in contract.established_increases.all():
            snapshot['established_increases'].append({
                'increase_type': safe_get_attr(increase, 'increase_type_id'),
                'amount_type': safe_get_attr(increase, 'amount_type'),
                'amount_value': float(safe_get_attr(increase, 'amount_value', 0)),
                'application_increase_type': safe_get_attr(increase, 'application_increase_type'),
                'start_date_increase': safe_str_date(safe_get_attr(increase, 'start_date_increase')),
                'end_date_increase': safe_str_date(safe_get_attr(increase, 'end_date_increase')),
                'description': safe_get_attr(increase, 'description'),
                'amount': float(safe_get_attr(increase, 'amount', 0))
            })

    return snapshot


def employee_with_contract_snapshot(employee=None, contract=None):
    """Genera un snapshot simplificado de un empleado y su contrato asociado."""

    def safe_get(obj, attr):
        if not obj or not hasattr(obj, attr):
            return None
        return getattr(obj, attr)

    def safe_date(value):
        return str(value) if value else None

    employee_data = {}
    if employee:
        employee_data = {
            "id_employee": safe_get(employee, "id_employee"),
            "id_user": safe_get(employee, "id_user_id"),
            "email": safe_get(employee, "email"),
            "id_employee_charge": safe_get(employee, "id_employee_charge_id"),
            "employee_status": safe_get(employee, "employee_status_id"),
            "creation_date": safe_date(safe_get(employee, "creation_date")),
            "modification_date": safe_date(safe_get(employee, "modification_date")),
            "id_responsible_user": safe_get(employee, "id_responsible_user_id"),
        }

    contract_data = {}
    if contract:
        contract_data = {
            "contract_code": safe_get(contract, "contract_code"),
            "id_employee": safe_get(contract, "id_employee_id"),
            "contract_status": safe_get(contract, "contract_status_id"),
            "start_date": safe_date(safe_get(contract, "start_date")),
            "end_date": safe_date(safe_get(contract, "end_date")),
            "salary_base": safe_get(contract, "salary_base"),
            "currency_type": safe_get(contract, "currency_type_id"),
        }

    return {
        "employee": employee_data,
        "contract": contract_data,
    }
