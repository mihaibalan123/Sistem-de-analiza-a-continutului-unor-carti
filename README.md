# Sistem de Analiză a Conținutului unei Cărți

Acest proiect își propune analiza obiectivă a romanului românesc prin vizualizarea unui graf a interacțiunilor dintre personajele cărții unde nodurile reprezintă numele personajelor, arcele interacțiunile, iar ponderile arcelor numără dialogurile existente iîntre ele. Prin utilizarea tehnologiilor moderne de procesare a imaginilor (OCR) și a LLM-urilor, sistemul transformă o carte statică (format `.pdf`) într-o bază de date interactivă, oferind o perspectivă tehnică și riguroasă asupra structurii narative.

---

## Funcționalități Principale

1. **Parsare și Extragere Text (pdf2image, OCR-tesseract/pytesseract+regex)**: 
   - Încarci un document `.pdf`, iar sistemul îi curăță fundalul și extrage textul folosind Tesseract OCR și OpenCV.
2. **Harta Interactivă a Relațiilor (Vis.js)**: 
   - Identifică automat personajele (rol, gen) și generează un graf vizual interactiv al relațiilor dintre ele. Două personaje sunt conectate dacă au avut cel puțin un dialog pe parcursul cărții.
3. **Chatbot (LLM)**: 
   - Un agent cu care poți purta o conversație liberă pentru a-i pune întrebări despre personajele din carte, bazându-se pe datele extrase.
4. **Rezumate Automate (.docx)**: 
   - Generează o sinteză a conflictului central și a temelor principale, pe care o poți descărca direct într-un document Word.

---

## Arhitectură și Tehnologii

Aplicația folosește o arhitectură **MVC**:

- **Frontend (View)**: SPA creată cu HTML5, CSS3, Bootstrap și JavaScript. Folosește **Vis.js** pentru randarea dinamică a grafurilor.
- **Backend (Controller)**: **Python** și **Django REST Framework**. Gestionează logica de business, rutele API și comunicarea asincronă.
- **Modele AI și Procesare**: `pdf2image`, `pytesseract`, `OpenCV` și SDK-ul Google Gemini.
- **Bază de Date (Model)**: **PostgreSQL** pentru stocarea persistentă și relațională a metadatelor.
- **Infrastructură**: **Docker & Docker Compose** (containere izolate pentru Frontend, Backend și Baza de date). Automatizare de lansări prin **GitHub Actions**.

---

## Cum se rulează

Proiectul este "Dockerizat", ceea ce înseamnă că poate rula pe orice sistem de operare (Windows, Linux) fără ca utilizatorul să fie nevoit să instaleze manual Python, baze de date sau librării OCR. 

**Singura cerință:** Să ai instalat [Docker Desktop](https://www.docker.com/products/docker-desktop/) și pornit pe calculator.

### Pași de instalare:
1. Descarcă cel mai recent Release `.zip` din secțiunea **Releases** de pe GitHub și dezarhivează-l (sau clonează acest repository).
2. În interiorul folderului, vei găsi două scripturi ajutătoare. Dă dublu-click pe cel potrivit sistemului tău:
   - **Pe Windows:** Rulează `start_windows.bat`
   - **Pe Linux:** Rulează `start_linux.sh` (din terminal folosind `sudo bash start_linux.sh`)
3. La prima rulare, o fereastră de terminal îți va cere **Cheia de API Gemini** (o poți obține gratuit de la Google AI Studio). Introdu cheia și apasă Enter.
4. Sistemul va descărca mediul virtual și va porni aplicația în fundal.
5. Accesează în browser: **`http://localhost:8080`**

*(Aplicația de backend rulează intern pe portul `8000`, iar baza de date pe `5432`).*

---

## Arhitectura Datelor

Baza de date este centrată pe 4 entități principale (Modele Django):
- **Autor:** Gestionează metadatele scriitorului.
- **Carte:** Detaliile operei (titlu, an apariție, nr. pagini).
- **Personaj:** Extrage tipologia personajelor (Gen: Masculin/Feminin, Tip: Principal/Secundar/Episodic).
- **Relație (Tabel asociativ):** Mapează interacțiunile dintre două personaje (many-to-many reflexiv), asigurând greutatea muchiilor din graful final prin contorizarea numărului de dialoguri.
