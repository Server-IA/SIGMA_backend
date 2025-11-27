#!/usr/bin/env python3
"""Script para capturar el error exacto del endpoint"""
import os
import sys
import json
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from rest_framework.test import APIClient
from django.utils import timezone
from unittest.mock import patch, MagicMock
from users.authentication import JWTUser
from users.models import User

# Setup
client = APIClient()
today = timezone.now().date()
start_date = (today + timedelta(days=2)).strftime('%Y-%m-%d')

body = {
    "observation": "Ingreso por contratación directa",
    "id_employee_charge": 1,
    "contract": [{
        "description": "Contrato de prueba 2",
        "contract_type": 19,
        "start_date": start_date,
        "end_date": None,
        "payment_frequency_type": "diario",
        "minimum_hours": 8,
        "workday_type": 22,
        "work_mode_type": 25,
        "salary_type": "Mensual fijo",
        "salary_base": 100000,
        "currency_type": 17,
        "trial_period_days": 30,
        "vacation_days": 15,
        "vacation_frequency_days": 360,
        "cumulative_vacation": True,
        "start_cumulative_vacation": (today + timedelta(days=2)).strftime('%Y-%m-%d'),
        "maximum_disability_days": 15,
        "overtime": 40,
        "overtime_period": "dia",
        "notice_period_days": 9,
        "contract_payments": [{"id_day_of_week": None, "date_payment": None}],
        "established_deductions": [],
        "established_increases": []
    }]
}

token_payload = {
    "id": 1,
    "email": "test@example.com",
    "name": "Test User",
    "roles": [{"permisos": [{"id": 186}], "permissions": [{"id": 186}]}],
    "rol": [{"permisos": [{"id": 186}], "permissions": [{"id": 186}]}],
    "permisos": [{"id": 186}],
    "permissions": [{"id": 186}],
}

# Crear usuario
user, _ = User.objects.get_or_create(id_user=1)
user.id = user.id_user
user.is_authenticated = True
user.save()

# Configurar autenticación
with patch('users.authentication.JWTAuthentication.authenticate') as mock_auth, \
     patch('users.authentication.jwt.decode') as mock_decode:
    mock_decode.return_value = token_payload
    mock_user = JWTUser(
        user_id=1,
        email='test@example.com',
        name='Test User',
        raw_payload=token_payload
    )
    mock_user.id = 1
    mock_user.is_authenticated = True
    mock_auth.return_value = (mock_user, token_payload)
    
    # Force authenticate
    client.force_authenticate(user=user)
    
    response = client.post(
        '/employees/1/change-contract/',
        data=json.dumps(body),
        content_type='application/json',
        HTTP_AUTHORIZATION='Bearer valid_token'
    )
    
    print(f"Status: {response.status_code}")
    print(f"\n{'='*80}")
    print("RESPONSE DATA:")
    print(f"{'='*80}")
    try:
        error_data = response.json()
        print(json.dumps(error_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error al obtener JSON: {e}")
        print(f"Response content: {response.content.decode('utf-8', errors='ignore')[:2000]}")
    print(f"{'='*80}\n")



