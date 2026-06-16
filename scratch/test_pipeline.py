import os
import sys
import django
import logging

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mds_backend.settings')
django.setup()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from analyzer.models import Carte, Autor, Personaj, Relatie
from analyzer.services import _worker_parsing_thread

def main():
    print("Cleaning tables...")
    Relatie.objects.all().delete()
    Personaj.objects.all().delete()
    Carte.objects.all().delete()

    autor, _ = Autor.objects.get_or_create(
        nume='Zamfirescu', 
        defaults={'prenume': 'Duiliu', 'data_nasterii': '1900-01-01'}
    )
    carte = Carte.objects.create(
        id_autor=autor, 
        titlu='Tanase Scatiu', 
        an_aparitie=1909, 
        nr_pagini=0, 
        nr_capitole=1
    )
    print(f"Created Test Book: ID={carte.id_carte}, Title={carte.titlu}")

    print("Starting parsing process...")
    # Using the copied sanitized PDF
    _worker_parsing_thread(
        'backend/media/uploads/1895f-1907e.-Duiliu-Zamfirescu-Tanase-Scatiu.-Roman-1909.pdf', 
        carte.id_carte
    )

    print("\n--- RESULTS ---")
    print(f"Total characters: {Personaj.objects.filter(id_carte=carte).count()}")
    for p in Personaj.objects.filter(id_carte=carte):
        print(f" - {p.nume} ({p.gen}, {p.tip_personaj})")
        
    print(f"\nTotal relations: {Relatie.objects.filter(id_personaj1__id_carte=carte).count()}")
    for r in Relatie.objects.filter(id_personaj1__id_carte=carte):
        print(f" - {r.id_personaj1.nume} <-> {r.id_personaj2.nume} (Dialogs: {r.numar_dialoguri})")

if __name__ == '__main__':
    main()
