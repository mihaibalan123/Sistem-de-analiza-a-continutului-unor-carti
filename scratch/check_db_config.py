import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mds_backend.settings')
django.setup()

from django.conf import settings
from django.db import connection
from analyzer.models import Carte

print("=== Django Database Settings ===")
print(settings.DATABASES['default'])

print("\n=== Connection Settings ===")
print("Engine:", connection.vendor)
print("Database Name:", connection.settings_dict['NAME'])
print("Database User:", connection.settings_dict['USER'])
print("Database Host:", connection.settings_dict['HOST'])
print("Database Port:", connection.settings_dict['PORT'])

print("\n=== Database Content ===")
try:
    carti = list(Carte.objects.all())
    print(f"Number of books: {len(carti)}")
    for c in carti:
        print(f"  - ID: {c.id_carte}, Title: {c.titlu}, Pages: {c.nr_pagini}")
except Exception as e:
    print(f"Error querying database: {e}")
