import os
import logging
import unicodedata
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Autor, Carte, Personaj, Relatie
from .services import start_parsing_background, get_progress
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    nfkd_form = unicodedata.normalize('NFKD', filename)
    ascii_bytes = nfkd_form.encode('ASCII', 'ignore')
    ascii_str = ascii_bytes.decode('ASCII')
    safe_chars = []
    for char in ascii_str:
        if char.isalnum() or char in ['.', '-', '_']:
            safe_chars.append(char)
        elif char.isspace():
            safe_chars.append('_')
    result = ''.join(safe_chars)
    name_part, ext = os.path.splitext(result)
    if not name_part.strip():
        import uuid
        return f'carte_{uuid.uuid4().hex[:8]}.pdf'
    return result

@api_view(['POST'])
def upload_file(request):
    if 'file' not in request.FILES:
        return Response({'error': 'Niciun fișier selectat.'}, status=status.HTTP_400_BAD_REQUEST)
    uploaded_file = request.FILES['file']
    if not uploaded_file.name.lower().endswith('.pdf'):
        return Response({'error': 'Te rugăm să încarci un fișier PDF valid.'}, status=status.HTTP_400_BAD_REQUEST)
    titlu_carte = request.POST.get('titlu', '').strip()
    an_aparitie_str = request.POST.get('an_aparitie', '').strip()
    nume_autor = request.POST.get('autor_nume', '').strip()
    prenume_autor = request.POST.get('autor_prenume', '').strip()
    data_nasterii = request.POST.get('autor_data_nasterii', '').strip()
    data_deces = request.POST.get('autor_data_deces', '').strip()
    filename_base = os.path.splitext(uploaded_file.name)[0]
    if not titlu_carte or not nume_autor:
        parts = filename_base.split('-')
        if len(parts) >= 2:
            autor_name_raw = parts[0].strip()
            guessed_titlu = parts[1].strip()
        else:
            autor_name_raw = 'Autor'
            guessed_titlu = filename_base.strip()
        autor_parts = autor_name_raw.split(' ')
        if len(autor_parts) >= 2:
            guessed_prenume = autor_parts[0]
            guessed_nume = ' '.join(autor_parts[1:])
        else:
            guessed_prenume = ''
            guessed_nume = autor_name_raw
        if not titlu_carte:
            titlu_carte = guessed_titlu
        if not nume_autor:
            nume_autor = guessed_nume
            prenume_autor = guessed_prenume
    an_aparitie = 2024
    if an_aparitie_str:
        try:
            an_aparitie = int(an_aparitie_str)
        except ValueError:
            pass
    defaults = {'prenume': prenume_autor, 'data_nasterii': '1900-01-01'}
    if data_nasterii:
        defaults['data_nasterii'] = data_nasterii
    if data_deces:
        defaults['data_deces'] = data_deces
    autor, created = Autor.objects.get_or_create(nume=nume_autor, prenume=prenume_autor, defaults=defaults)
    if not created:
        updated = False
        if data_nasterii and str(autor.data_nasterii) != data_nasterii:
            autor.data_nasterii = data_nasterii
            updated = True
        if data_deces and str(autor.data_deces) != data_deces:
            autor.data_deces = data_deces
            updated = True
        if updated:
            autor.save()
    carte = Carte.objects.create(id_autor=autor, titlu=titlu_carte, an_aparitie=an_aparitie, nr_pagini=0, nr_capitole=1)
    original_name = uploaded_file.name
    safe_name = f'carte_{carte.id_carte}_{sanitize_filename(original_name)}'
    uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, safe_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    path = default_storage.save(os.path.join('uploads', safe_name), ContentFile(uploaded_file.read()))
    full_pdf_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path))
    start_parsing_background(full_pdf_path, carte.id_carte)
    return Response({'message': 'Fișier încărcat cu succes! Parsarea a început în fundal.', 'id_carte': carte.id_carte, 'titlu': carte.titlu, 'autor': f'{autor.prenume or ''} {autor.nume}'.strip()}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def check_status(request, carte_id):
    progress = get_progress(int(carte_id))
    return Response(progress)

@api_view(['GET'])
def list_books(request):
    carti = Carte.objects.select_related('id_autor').all().order_by('-id_carte')
    result = []
    for c in carti:
        result.append({'id_carte': c.id_carte, 'titlu': c.titlu, 'an_aparitie': c.an_aparitie, 'nr_pagini': c.nr_pagini, 'autor_nume': c.id_autor.nume if c.id_autor else 'Necunoscut', 'autor_prenume': c.id_autor.prenume if c.id_autor else ''})
    return Response(result)

@api_view(['GET'])
def get_book_graph(request, carte_id):
    try:
        carte = Carte.objects.select_related('id_autor').get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    personaje = Personaj.objects.filter(id_carte=carte)
    personaje_list = []
    for p in personaje:
        personaje_list.append({'id_personaj': p.id_personaj, 'nume': p.nume, 'gen': p.gen, 'tip_personaj': p.tip_personaj})
    relatii = Relatie.objects.filter(id_personaj1__id_carte=carte, id_personaj2__id_carte=carte).select_related('id_personaj1', 'id_personaj2')
    relatii_list = []
    for r in relatii:
        relatii_list.append({'id_relatie': r.id_relatie, 'id_personaj1': r.id_personaj1.id_personaj, 'id_personaj2': r.id_personaj2.id_personaj, 'personaj_1_nume': r.id_personaj1.nume, 'personaj_2_nume': r.id_personaj2.nume, 'numar_dialoguri': r.numar_dialoguri})
    summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', f'rezumat_carte_{carte_id}.docx')
    has_summary = os.path.exists(summary_path)
    return Response({'carte': {'titlu': carte.titlu, 'autor': f'{carte.id_autor.prenume or ''} {carte.id_autor.nume}'.strip() if carte.id_autor else 'Necunoscut', 'an_aparitie': carte.an_aparitie, 'nr_pagini': carte.nr_pagini, 'has_summary': has_summary}, 'personaje': personaje_list, 'relatii': relatii_list, 'has_summary': has_summary})

@api_view(['DELETE'])
def delete_book(request, carte_id):
    try:
        carte = Carte.objects.get(id_carte=carte_id)
        carte.delete()
        return Response({'message': 'Cartea a fost ștearsă cu succes.'}, status=status.HTTP_200_OK)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu există.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def clear_all_books(request):
    Relatie.objects.all().delete()
    Personaj.objects.all().delete()
    Carte.objects.all().delete()
    Autor.objects.all().delete()
    return Response({'message': 'Toate datele au fost șterse cu succes.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def start_ai_analysis(request, carte_id):
    try:
        carte = Carte.objects.get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    import glob
    outputs_dir = os.path.normpath(os.path.join(settings.BASE_DIR, '..', 'outputs'))
    pattern = os.path.join(outputs_dir, f'carte_{carte_id}_*.json')
    matches = glob.glob(pattern)
    if not matches:
        safe_name = sanitize_filename(carte.titlu)
        pattern_fallback = os.path.join(outputs_dir, f'*{safe_name}*_extras.json')
        matches = glob.glob(pattern_fallback)
    if not matches:
        pattern_any = os.path.join(outputs_dir, f'*_extras.json')
        matches = glob.glob(pattern_any)
        if not matches:
            return Response({'error': 'Fișierul parsat (JSON) nu a fost găsit în outputs/. Te rugăm să rulezi din nou parsarea.'}, status=status.HTTP_404_NOT_FOUND)
    json_path = matches[0]
    run_relations = request.data.get('run_relations', True)
    run_summary = request.data.get('run_summary', True)
    from .services import start_ai_analysis_background
    start_ai_analysis_background(json_path, carte_id, run_relations=run_relations, run_summary=run_summary)
    return Response({'message': 'Analiza AI a început în fundal.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def clear_book_analysis(request, carte_id):
    try:
        carte = Carte.objects.get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    from django.db import transaction
    with transaction.atomic():
        Personaj.objects.filter(id_carte=carte).delete()
    summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', f'rezumat_carte_{carte_id}.docx')
    if os.path.exists(summary_path):
        try:
            os.remove(summary_path)
        except Exception as e:
            logger.warning(f'Nu s-a putut șterge fișierul Word pentru cartea {carte_id}: {e}')
    from .services import PROGRESS_LOCK, PROGRESS_STATE
    with PROGRESS_LOCK:
        if carte_id in PROGRESS_STATE:
            del PROGRESS_STATE[carte_id]
    return Response({'message': 'Datele de analiză pentru această carte au fost șterse.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def download_summary(request, carte_id):
    try:
        carte = Carte.objects.get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', f'rezumat_carte_{carte_id}.docx')
    if not os.path.exists(summary_path):
        return Response({'error': 'Rezumatul nu este disponibil pentru această carte.'}, status=status.HTTP_404_NOT_FOUND)
    from django.http import FileResponse
    import urllib.parse
    filename = f'Rezumat - {carte.titlu}.docx'
    encoded_filename = urllib.parse.quote(filename)
    response = FileResponse(open(summary_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    return response

@api_view(['POST'])
def ask_about_character(request, carte_id):
    try:
        carte = Carte.objects.select_related('id_autor').get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    intrebare = request.data.get('question', '').strip()
    if not intrebare:
        return Response({'error': 'Întrebarea nu poate fi goală.'}, status=status.HTTP_400_BAD_REQUEST)
    personaje = Personaj.objects.filter(id_carte=carte)
    personaje_info = []
    for p in personaje:
        personaje_info.append(f'- {p.nume} (Gen: {p.gen}, Rol: {p.tip_personaj})')
    personaje_str = '\n'.join(personaje_info) if personaje_info else 'Niciun personaj detectat momentan.'
    relatii = Relatie.objects.filter(id_personaj1__id_carte=carte, id_personaj2__id_carte=carte).select_related('id_personaj1', 'id_personaj2')
    relatii_info = []
    for r in relatii:
        relatii_info.append(f'- {r.id_personaj1.nume} <-> {r.id_personaj2.nume}: {r.numar_dialoguri} dialoguri')
    relatii_str = '\n'.join(relatii_info) if relatii_info else 'Nicio relație directă de dialog înregistrată.'
    from .agents import CharacterQAAgent, DialogAgent
    dialog_agent = DialogAgent()
    qa_agent = CharacterQAAgent(dialog_agent=dialog_agent)
    try:
        autor_nume = f'{carte.id_autor.prenume or ''} {carte.id_autor.nume}'.strip() if carte.id_autor else 'Necunoscut'
        raspuns = qa_agent.raspunde_intrebare(carte_titlu=carte.titlu, carte_autor=autor_nume, personaje_info=personaje_str, relatii_info=relatii_str, intrebare=intrebare)
        return Response({'answer': raspuns}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Eroare în QA Agent pentru cartea {carte_id}: {e}')
        return Response({'error': f'Eroare la generarea răspunsului: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_book_metadata(request, carte_id):
    try:
        carte = Carte.objects.select_related('id_autor').get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    autor = carte.id_autor
    return Response({'id_carte': carte.id_carte, 'titlu': carte.titlu, 'an_aparitie': carte.an_aparitie, 'nr_pagini': carte.nr_pagini, 'autor_nume': autor.nume if autor else '', 'autor_prenume': autor.prenume if autor else '', 'autor_data_nasterii': str(autor.data_nasterii) if autor and autor.data_nasterii else '', 'autor_data_deces': str(autor.data_deces) if autor and autor.data_deces else ''})

@api_view(['POST'])
def update_book_metadata(request, carte_id):
    try:
        carte = Carte.objects.select_related('id_autor').get(id_carte=carte_id)
    except Carte.DoesNotExist:
        return Response({'error': 'Cartea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)
    titlu = request.data.get('titlu', '').strip()
    an_aparitie_str = request.data.get('an_aparitie', '').strip()
    nume_autor = request.data.get('autor_nume', '').strip()
    prenume_autor = request.data.get('autor_prenume', '').strip()
    data_nasterii = request.data.get('autor_data_nasterii', '').strip()
    data_deces = request.data.get('autor_data_deces', '').strip()
    if not titlu or not nume_autor:
        return Response({'error': 'Titlul cărții și numele de familie al autorului sunt obligatorii.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        an_aparitie = int(an_aparitie_str)
        if an_aparitie < 1001 or an_aparitie > 2026:
            return Response({'error': 'Anul apariției trebuie să fie între 1001 și 2026.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'error': 'Anul apariției trebuie să fie un număr valid.'}, status=status.HTTP_400_BAD_REQUEST)
    from django.db import transaction
    with transaction.atomic():
        carte.titlu = titlu
        carte.an_aparitie = an_aparitie
        defaults = {'prenume': prenume_autor, 'data_nasterii': data_nasterii if data_nasterii else '1900-01-01'}
        if data_deces:
            defaults['data_deces'] = data_deces
        else:
            defaults['data_deces'] = None
        autor, created = Autor.objects.get_or_create(nume=nume_autor, prenume=prenume_autor, defaults=defaults)
        if not created:
            if data_nasterii:
                autor.data_nasterii = data_nasterii
            if data_deces:
                autor.data_deces = data_deces
            else:
                autor.data_deces = None
            autor.save()
        carte.id_autor = autor
        carte.save()
    return Response({'message': 'Metadatele cărții au fost actualizate cu succes!', 'carte': {'id_carte': carte.id_carte, 'titlu': carte.titlu, 'an_aparitie': carte.an_aparitie, 'autor': f'{autor.prenume or ''} {autor.nume}'.strip()}})