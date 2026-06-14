import os
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from django.db import transaction
from django.conf import settings
from .models import Carte, Personaj, Relatie
logger = logging.getLogger(__name__)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class Interaction(BaseModel):
    personaj_1: str = Field(default='', description="Numele principal al primului personaj care dialoghează (de ex. 'Gheorghe' în loc de 'Ghiță' sau 'el')")
    personaj_2: str = Field(default='', description="Numele principal al celui de-al doilea personaj care dialoghează (de ex. 'Ana' în loc de 'ea')")
    gen_personaj_1: str = Field(default='Masculin', description="Genul primului personaj: 'Masculin' sau 'Feminin'")
    gen_personaj_2: str = Field(default='Masculin', description="Genul celui de-al doilea personaj: 'Masculin' sau 'Feminin'")
    tip_personaj_1: str = Field(default='Secundar', description="Importanța primului personaj în această scenă: 'Principal', 'Secundar', 'Episodic'")
    tip_personaj_2: str = Field(default='Secundar', description="Importanța celui de-al doilea personaj în această scenă: 'Principal', 'Secundar', 'Episodic'")

class DialogueExtraction(BaseModel):
    interactiuni: List[Interaction]

class ChapterSummary(BaseModel):
    titlu_sectiune: str = Field(default='', description="Titlul acestei secțiuni mari sau capitol (ex: 'Începutul războiului', 'Spânzurătoarea sub cerul cenușiu')")
    rezumat_sectiune: str = Field(default='', description='Un rezumat detaliat și cursiv al acțiunii din această secțiune.')
    idei_principale: List[str] = Field(default_factory=list, description='O listă cu 2-4 idei sau evenimente-cheie din această secțiune.')

class BookSummary(BaseModel):
    rezumat_general: str = Field(default='', description='Un rezumat general al romanului (maximum 3 paragrafe).')
    teme_principale: List[str] = Field(default_factory=list, description='O listă cu 3-4 teme literare principale.')
    sectiuni: List[ChapterSummary] = Field(default_factory=list, description='Capitolele sau secțiunile mari ale cărții (5-7 secțiuni).')

class InteractionSchema(BaseModel):
    personaj_1: str = Field(description="Numele principal al primului personaj care dialoghează (de ex. 'Gheorghe' în loc de 'Ghiță' sau 'el')")
    personaj_2: str = Field(description="Numele principal al celui de-al doilea personaj care dialoghează (de ex. 'Ana' în loc de 'ea')")
    gen_personaj_1: str = Field(description="Genul primului personaj: 'Masculin' sau 'Feminin'")
    gen_personaj_2: str = Field(description="Genul celui de-al doilea personaj: 'Masculin' sau 'Feminin'")
    tip_personaj_1: str = Field(description="Importanța primului personaj în această scenă: 'Principal', 'Secundar', 'Episodic'")
    tip_personaj_2: str = Field(description="Importanța celui de-al doilea personaj în această scenă: 'Principal', 'Secundar', 'Episodic'")

class DialogueExtractionSchema(BaseModel):
    interactiuni: List[InteractionSchema]

class ChapterSummarySchema(BaseModel):
    titlu_sectiune: str = Field(description="Titlul acestei secțiuni mari sau capitol (ex: 'Capitolul I: Glasul pământului')")
    rezumat_sectiune: str = Field(description='Un rezumat concis, fluid și redactat literar al acțiunii din această secțiune (maximum 2 paragrafe).')
    idei_principale: List[str] = Field(description='O listă cu exact 3 idei esențiale din această secțiune.')

class BookSummarySchema(BaseModel):
    rezumat_general: str = Field(description='Un rezumat general al romanului (maximum 3 paragrafe).')
    teme_principale: List[str] = Field(description='O listă cu exact 3-4 teme literare principale.')
    sectiuni: List[ChapterSummarySchema] = Field(description='Capitolele sau secțiunile mari ale cărții (exact 5-7 secțiuni mari care acoperă cronologic toată opera de la început la sfârșit).')

class DialogAgent:

    def __init__(self):
        keys_str = os.environ.get('GEMINI_API_KEYS') or os.environ.get('GEMINI_API_KEY') or ''
        self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        self.current_key_idx = 0
        if GENAI_AVAILABLE and self.api_keys:
            self.configure_current_key()
            self.active = True
        else:
            self.active = False
            logger.warning('Gemini API keys are missing or google-generativeai is not installed. AI Agent running in fallback simulation mode.')

    def configure_current_key(self):
        key = self.api_keys[self.current_key_idx]
        masked_key = f'{key[:6]}...{key[-4:]}' if len(key) > 10 else '...'
        logger.info(f'Configurăm Gemini API cu cheia index {self.current_key_idx} ({masked_key})')
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def extrage_interactiuni(self, text_pagina: str, personaje_cunoscute: List[str]) -> List[Interaction]:
        if not self.active:
            return self._simuleaza_interactiuni(text_pagina)
        personaje_str = ', '.join(personaje_cunoscute) if personaje_cunoscute else 'niciunul momentan'
        prompt = f"""\nEști un expert în analiză literară și lingvistică a textelor în limba română. \nSarcina ta este să analizezi următorul fragment dintr-o carte și să identifici toate interacțiunile directe de tip dialog între personaje.\n\nPentru fiecare interacțiune/dialog identificat între două personaje, trebuie să completezi obligatoriu următoarele câmpuri în obiectul returnat:\n1. "personaj_1": Numele principal standardizat al primului personaj care dialoghează (de ex. 'Gheorghe' în loc de 'Ghiță' sau 'el').\n2. "personaj_2": Numele principal standardizat al celui de-al doilea personaj care dialoghează (de ex. 'Ana' în loc de 'ea').\n3. "gen_personaj_1": Genul primului personaj ("Masculin" sau "Feminin").\n4. "gen_personaj_2": Genul celui de-al doilea personaj ("Masculin" sau "Feminin").\n5. "tip_personaj_1": Importanța primului personaj în această scenă ("Principal", "Secundar" sau "Episodic").\n6. "tip_personaj_2": Importanța celui de-al doilea personaj în această scenă ("Principal", "Secundar" sau "Episodic").\n\nINSTRUCȚIUNI CRITICE (Coreference Resolution):\n1. **Rezolvă Coreferințele Contextuale**: Dacă personajele vorbesc, iar în loc de nume se folosesc pronume ('el', 'ea', 'dânsul', 'lui', etc.), determină din contextul scenei cine sunt persoanele reale din spate.\n2. **Standardizează Diminutivele și Poreclele**: Dacă un personaj este apelat sau menționat printr-un diminutiv (ex. 'Ghiță', 'Vasilică', 'Anișoara', 'Niță'), identifică numele lui principal standardizat (ex. 'Gheorghe', 'Vasile', 'Ana', 'Ilie') și folosește-l EXCLUSIV pe acesta în rezultat.\n3. **Folosește Personajele Existente**: Iată o listă cu numele personajelor deja identificate în această carte: [{personaje_str}]. Dacă un personaj din scenă corespunde unuia din această listă, folosește EXACT același nume.\n4. **Ignoră zgomotul de fundal**: Extrage doar dialogurile clare dintre două entități conștiente.\n\nFragment de text de analizat:\n---\n{text_pagina}\n---\n"""
        import time
        retries = 0
        while self.current_key_idx < len(self.api_keys):
            try:
                response = self.model.generate_content(prompt, generation_config=genai.GenerationConfig(response_mime_type='application/json', response_schema=DialogueExtractionSchema, temperature=0.1))
                data = json.loads(response.text)
                extracted_interactions = []
                for item in data.get('interactiuni', []):
                    extracted_interactions.append(Interaction(**item))
                return extracted_interactions
            except Exception as e:
                err_msg = str(e)
                is_quota_or_auth = '429' in err_msg or 'quota' in err_msg.lower() or 'api key' in err_msg.lower() or ('api_key' in err_msg.lower()) or ('invalid' in err_msg.lower())
                if is_quota_or_auth and self.current_key_idx < len(self.api_keys) - 1:
                    logger.warning(f'Cheia API Gemini de la indexul {self.current_key_idx} a eșuat ({err_msg[:80]}). Trecem la următoarea cheie...')
                    self.current_key_idx += 1
                    self.configure_current_key()
                    continue
                elif not is_quota_or_auth and retries < 2:
                    retries += 1
                    logger.warning(f'DialogAgent: Eroare temporară de generare/validare ({err_msg[:80]}). Reîncercăm (încercarea {retries}/2)...')
                    time.sleep(1)
                    continue
                else:
                    logger.error(f'Eroare critică sau lipsă chei de rezervă la apelul Gemini API: {e}')
                    raise e

    def proceseaza_pagina_si_salveaza(self, text_pagina: str, carte_id: int):
        personaje_existente = Personaj.objects.filter(id_carte_id=carte_id)
        nume_personaje_existente = [p.nume for p in personaje_existente]
        interactiuni = self.extrage_interactiuni(text_pagina, nume_personaje_existente)
        with transaction.atomic():
            carte = Carte.objects.get(id_carte=carte_id)
            for interactiune in interactiuni:
                nume_p1 = interactiune.personaj_1.strip()
                nume_p2 = interactiune.personaj_2.strip()
                if not nume_p1 or not nume_p2 or nume_p1.lower() == nume_p2.lower():
                    continue
                gen_p1 = interactiune.gen_personaj_1 if interactiune.gen_personaj_1 in ['Masculin', 'Feminin'] else 'Masculin'
                gen_p2 = interactiune.gen_personaj_2 if interactiune.gen_personaj_2 in ['Masculin', 'Feminin'] else 'Masculin'
                tip_p1 = interactiune.tip_personaj_1 if interactiune.tip_personaj_1 in ['Principal', 'Secundar', 'Episodic', 'Colectiv'] else 'Secundar'
                tip_p2 = interactiune.tip_personaj_2 if interactiune.tip_personaj_2 in ['Principal', 'Secundar', 'Episodic', 'Colectiv'] else 'Secundar'
                p1, created_p1 = Personaj.objects.get_or_create(id_carte=carte, nume__iexact=nume_p1, defaults={'nume': nume_p1, 'gen': gen_p1, 'tip_personaj': tip_p1})
                p2, created_p2 = Personaj.objects.get_or_create(id_carte=carte, nume__iexact=nume_p2, defaults={'nume': nume_p2, 'gen': gen_p2, 'tip_personaj': tip_p2})
                personaj_a = p1 if p1.id_personaj < p2.id_personaj else p2
                personaj_b = p2 if p1.id_personaj < p2.id_personaj else p1
                relatie, created_rel = Relatie.objects.get_or_create(id_personaj1=personaj_a, id_personaj2=personaj_b, defaults={'numar_dialoguri': 1})
                if not created_rel:
                    relatie.numar_dialoguri += 1
                    relatie.save()

    def _simuleaza_interactiuni(self, text_pagina: str) -> List[Interaction]:
        text_lower = text_pagina.lower()
        simulari = []
        personaje_posibile = [('Ion', 'Masculin', 'Principal'), ('Ana', 'Feminin', 'Principal'), ('Gheorghe', 'Masculin', 'Secundar'), ('Florica', 'Feminin', 'Secundar'), ('Moromete', 'Masculin', 'Principal'), ('Catrina', 'Feminin', 'Secundar'), ('Otilia', 'Feminin', 'Principal'), ('Felix', 'Masculin', 'Principal'), ('Leonida', 'Masculin', 'Principal'), ('Efimița', 'Feminin', 'Secundar'), ('Zoe', 'Feminin', 'Principal'), ('Tipătescu', 'Masculin', 'Principal')]
        prezente = []
        for nume, gen, tip in personaje_posibile:
            if nume.lower() in text_lower:
                prezente.append((nume, gen, tip))
        if len(prezente) < 2:
            import hashlib
            h = int(hashlib.md5(text_pagina.encode('utf-8')).hexdigest(), 16)
            p1_idx = h % len(personaje_posibile)
            p2_idx = (h + 1) % len(personaje_posibile)
            p1 = personaje_posibile[p1_idx]
            p2 = personaje_posibile[p2_idx]
            simulari.append(Interaction(personaj_1=p1[0], personaj_2=p2[0], gen_personaj_1=p1[1], gen_personaj_2=p2[1], tip_personaj_1=p1[2], tip_personaj_2=p2[2]))
        else:
            for i in range(len(prezente) - 1):
                simulari.append(Interaction(personaj_1=prezente[i][0], personaj_2=prezente[i + 1][0], gen_personaj_1=prezente[i][1], gen_personaj_2=prezente[i + 1][1], tip_personaj_1=prezente[i][2], tip_personaj_2=prezente[i + 1][2]))
        return simulari

class SummaryAgent:

    def __init__(self, dialog_agent=None):
        if dialog_agent:
            self.api_keys = dialog_agent.api_keys
            self.current_key_idx = dialog_agent.current_key_idx
            self.active = dialog_agent.active
            self.model = dialog_agent.model
        else:
            keys_str = os.environ.get('GEMINI_API_KEYS') or os.environ.get('GEMINI_API_KEY') or ''
            self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            self.current_key_idx = 0
            if GENAI_AVAILABLE and self.api_keys:
                self.configure_current_key()
                self.active = True
            else:
                self.active = False
                logger.warning('Gemini API keys are missing for SummaryAgent. Fallback to simulation.')

    def configure_current_key(self):
        key = self.api_keys[self.current_key_idx]
        masked_key = f'{key[:6]}...{key[-4:]}' if len(key) > 10 else '...'
        logger.info(f'SummaryAgent: Configurăm Gemini API cu cheia index {self.current_key_idx} ({masked_key})')
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def extrage_rezumat(self, text_carte: str, carte_titlu: str, carte_autor: str) -> BookSummary:
        if not self.active:
            return self._simuleaza_rezumat(carte_titlu, carte_autor)
        prompt = f'\nEști un critic literar de prestigiu și asistent de analiză literară.\nSarcina ta este să citești textul complet al operei literare "{carte_titlu}" de {carte_autor} furnizat mai jos și să realizezi o analiză și un rezumat general, profesionist, structurat și redactat într-un stil literar îngrijit în limba română.\n\nTrebuie să returnezi un obiect JSON valid care conține exact următoarele câmpuri:\n1. "rezumat_general": Un rezumat general general, cuprinzător, detaliat și fluid al întregului roman, evidențiind conflictul central și evoluția acțiunii.\n2. "teme_principale": O listă cu 3-5 teme literare sau motive cheie din operă (ex: datoria, războiul, drama conștiinței, dragostea).\n3. "sectiuni": O listă cu principalele secțiuni sau capitole cronologice (între 5 și 8 secțiuni mari) care rezumă cursul întregii opere de la început până la sfârșit. Fiecare secțiune trebuie să conțină:\n   - "titlu_sectiune": Un titlu reprezentativ (ex: "Capitolul I: Condamnarea lui Svoboda", "Apostol Bologa și dilema datoriei").\n   - "rezumat_sectiune": Rezumatul detaliat al acelei părți.\n   - "idei_principale": 2-4 idei sau detalii esențiale din acea secțiune.\n\nTextul complet al operei (extras prin OCR):\n---\n{text_carte}\n---\n\nINSTRUCȚIUNI CRITICE PENTRU LIMITAREA LUNGIMII ȘI SIGURANȚĂ JSON:\n1. Rezumatul general ("rezumat_general") trebuie să aibă maximum 3-4 paragrafe.\n2. Teme principale ("teme_principale") trebuie să conțină exact 3-4 teme importante.\n3. Secțiuni ("sectiuni") trebuie să conțină EXACT între 5 și 7 secțiuni mari care să acopere cronologic întregul text analizat.\n4. Pentru fiecare secțiune:\n   - Rezumatul de secțiune ("rezumat_sectiune") trebuie să fie concis (maximum 2 paragrafe).\n   - Ideile principale ("idei_principale") trebuie să conțină exact 3 puncte esențiale.\n5. Toate valorile text (string-urile) din JSON trebuie scrise curgător. Nu folosi taste/literal newline direct în interiorul ghilimelelor dintr-un string JSON, ci scrie textul într-un mod continuu.\nNu lungi inutil descrierile, fii dens, precis și concis!\n'
        import time
        retries = 0
        while self.current_key_idx < len(self.api_keys):
            try:
                response = self.model.generate_content(prompt, generation_config=genai.GenerationConfig(response_mime_type='application/json', response_schema=BookSummarySchema, temperature=0.2))
                cleaned_text = self._curata_newlines_json(response.text)
                data = json.loads(cleaned_text)
                return BookSummary(**data)
            except Exception as e:
                err_msg = str(e)
                if 'response' in locals() and hasattr(response, 'text'):
                    logger.error(f'SummaryAgent: Răspunsul brut care a generat eroarea de parsare:\n{response.text}')
                is_quota_or_auth = '429' in err_msg or 'quota' in err_msg.lower() or 'api key' in err_msg.lower() or ('api_key' in err_msg.lower()) or ('invalid' in err_msg.lower())
                if is_quota_or_auth and self.current_key_idx < len(self.api_keys) - 1:
                    logger.warning(f'SummaryAgent: Cheia API Gemini de la indexul {self.current_key_idx} a eșuat ({err_msg[:80]}). Trecem la următoarea cheie...')
                    self.current_key_idx += 1
                    self.configure_current_key()
                    continue
                elif not is_quota_or_auth and retries < 2:
                    retries += 1
                    logger.warning(f'SummaryAgent: Eroare temporară de parsare/generare ({err_msg[:80]}). Reîncercăm cererea (încercarea {retries}/2)...')
                    time.sleep(1)
                    continue
                else:
                    logger.error(f'SummaryAgent: Eroare critică sau lipsă chei de rezervă la apelul Gemini API: {e}')
                    raise e

    def _simuleaza_rezumat(self, carte_titlu: str, carte_autor: str) -> BookSummary:
        return BookSummary(rezumat_general=f"Opera literară '{carte_titlu}', scrisă de {carte_autor}, reprezintă o capodoperă a literaturii române. Acțiunea explorează conflicte morale profunde și analizează în profunzime psihologia umană în fața unor încercări cruciale. Personajele complexe evoluează într-un cadru social și istoric tensionat, oferind o perspectivă realistă asupra vieții.", teme_principale=['Destinul și condiția umană', 'Conflictul de conștiință și datoria', 'Relațiile sociale și familiale'], sectiuni=[ChapterSummary(titlu_sectiune='Secțiunea I: Introducere și Context', rezumat_sectiune='Introducerea personajelor principale și stabilirea cadrului inițial al acțiunii.', idei_principale=['Stabilirea decorului', 'Apariția conflictului', 'Primele decizii']), ChapterSummary(titlu_sectiune='Secțiunea II: Punctul Culminant', rezumat_sectiune='Tensiunea atinge cote maxime pe măsură ce conflictele dintre personaje se intensifică.', idei_principale=['Confruntări directe', 'Evoluții dramatice', 'Dileme morale']), ChapterSummary(titlu_sectiune='Secțiunea III: Rezoluție și Deznodământ', rezumat_sectiune='Rezolvarea conflictelor narative și concluziile asupra destinului personajelor.', idei_principale=['Deznodământul operei', 'Reflecțiile finale', 'Mântuirea sufletească'])])

    def _curata_newlines_json(self, json_str: str) -> str:
        in_string = False
        escaped = False
        chars = []
        for char in json_str:
            if char == '"' and (not escaped):
                in_string = not in_string
                chars.append(char)
            elif char == '\\' and in_string:
                escaped = not escaped
                chars.append(char)
            elif char in ('\r', '\n') and in_string:
                chars.append('\\n')
                escaped = False
            else:
                chars.append(char)
                escaped = False
        return ''.join(chars)

class CharacterQAAgent:

    def __init__(self, dialog_agent=None):
        if dialog_agent:
            self.api_keys = dialog_agent.api_keys
            self.current_key_idx = dialog_agent.current_key_idx
            self.active = dialog_agent.active
            self.model = dialog_agent.model
        else:
            keys_str = os.environ.get('GEMINI_API_KEYS') or os.environ.get('GEMINI_API_KEY') or ''
            self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            self.current_key_idx = 0
            if GENAI_AVAILABLE and self.api_keys:
                self.configure_current_key()
                self.active = True
            else:
                self.active = False
                logger.warning('Gemini API keys are missing for CharacterQAAgent. Fallback to simulation.')

    def configure_current_key(self):
        key = self.api_keys[self.current_key_idx]
        masked_key = f'{key[:6]}...{key[-4:]}' if len(key) > 10 else '...'
        logger.info(f'CharacterQAAgent: Configurăm Gemini API cu cheia index {self.current_key_idx} ({masked_key})')
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def raspunde_intrebare(self, carte_titlu: str, carte_autor: str, personaje_info: str, relatii_info: str, intrebare: str) -> str:
        if not self.active:
            return self._simuleaza_raspuns(carte_titlu, intrebare)
        prompt = f'\nEști un critic literar experimentat și asistent virtual inteligent. Răspunde la întrebarea utilizatorului despre opera literară "{carte_titlu}" de {carte_autor}.\n\nIată datele extrase din baza noastră de date despre personaje și interacțiunile lor directe (numărul de dialoguri):\n---\nPERSONAJE DETECTATE:\n{personaje_info}\n\nRELAȚII DETECTATE:\n{relatii_info}\n---\n\nÎntrebarea utilizatorului:\n"{intrebare}"\n\nINSTRUCȚIUNI:\n1. Răspunde politicos și redactează un răspuns bine documentat, coerent și captivant în limba română.\n2. Integrează datele structurate primite (cum ar fi statutul personajului de protagonist/secundar și cuplurile cele mai active) și coroborează-le cu cunoștințele tale despre acțiunea cărții.\n3. Dacă întrebarea se referă la un personaj specific, explică cine este acesta, ce rol are în operă și cum interacționează cu ceilalți.\n4. Fii concis, dar acoperă toate detaliile importante (aproximativ 2-4 paragrafe).\n'
        while self.current_key_idx < len(self.api_keys):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                err_msg = str(e)
                is_quota_or_auth = '429' in err_msg or 'quota' in err_msg.lower() or 'api key' in err_msg.lower() or ('api_key' in err_msg.lower()) or ('invalid' in err_msg.lower())
                if is_quota_or_auth and self.current_key_idx < len(self.api_keys) - 1:
                    logger.warning(f'CharacterQAAgent: Cheia API Gemini de la indexul {self.current_key_idx} a eșuat. Trecem la următoarea...')
                    self.current_key_idx += 1
                    self.configure_current_key()
                    continue
                else:
                    logger.error(f'CharacterQAAgent: Eroare la apelul Gemini API: {e}')
                    raise e

    def _simuleaza_raspuns(self, carte_titlu: str, intrebare: str) -> str:
        q_lower = intrebare.lower()
        if 'cine' in q_lower or 'rol' in q_lower or 'despre' in q_lower:
            name = 'personajul menționat'
            for candidate in ['ion', 'ana', 'gheorghe', 'florica', 'moromete', 'catrina', 'otilia', 'felix', 'zoe', 'tipatescu']:
                if candidate in q_lower:
                    name = candidate.capitalize()
                    break
            return f'[Simulare Asistent AI] În opera "{carte_titlu}", {name} are un rol deosebit de important în structura dramatică a narațiunii. Din datele de dialoguri extrase, se poate observa că acest personaj participă activ la evoluția acțiunii, interacțiunile sale definind conflictele sociale și morale specifice mediului descris de autor.'
        else:
            return f'[Simulare Asistent AI] Răspuns la întrebarea despre "{carte_titlu}": Opera literară investigată prezintă o complexitate deosebită a caracterelor și a relațiilor inter-umane. Graficul interactiv de dialoguri arată intensitatea interacțiunilor dintre personaje, reflectând exact structura narativă concepută de autor.'