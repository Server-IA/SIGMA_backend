#!/usr/bin/env python
"""
Script de seed para datos de prueba WebSocket.

Uso:
    docker-compose exec web python test/WS-MS-003/seed_data.py
"""
import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
django.setup()

# Import and run seed
from test.conftest import seed_ws_demo_data

if __name__ == '__main__':
    print("Seeding WebSocket demo data...")
    result = seed_ws_demo_data()
    print(f"✅ Seed completed successfully!")
    print(f"   - User ID: {result['user'].id_user}")
    print(f"   - Device IMEI: {result['device'].IMEI}")
    print(f"   - Machinery: {result['machinery'].machinery_name}")
    print(f"   - Service Request: {result['service_request'].id_request}")
