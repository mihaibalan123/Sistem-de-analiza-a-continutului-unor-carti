document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://localhost:8000/api';

    
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const statusContainer = document.getElementById('status-container');
    const statusSpinner = document.getElementById('status-spinner');
    const successIcon = document.getElementById('status-success-icon');
    const errorIcon = document.getElementById('status-error-icon');
    const statusTitle = document.getElementById('status-title');
    const statusMessage = document.getElementById('status-message');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    
    const viewResultsBtn = document.getElementById('view-results-btn');
    const resetBtn = document.getElementById('reset-btn');
    const btnBackToUpload = document.getElementById('btn-back-to-upload');
    const btnFitGraph = document.getElementById('btn-fit-graph');
    const btnRefreshGraph = document.getElementById('btn-refresh-graph');
    const btnClearAllBooks = document.getElementById('btn-clear-all-books');
    
    
    const uploadSection = document.getElementById('upload-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const booksListSection = document.getElementById('books-list-section');
    
    
    const navUploadLink = document.querySelector('.navbar-nav .nav-link[href="#"]');
    const navBooksLink = document.getElementById('nav-books-link');

    
    let currentBookId = null;
    let pollInterval = null;
    let aiPollInterval = null;
    let network = null;
    let allPersonaje = [];
    let allRelatii = [];
    let pendingFile = null;
    let pendingModalInstance = null;

    
    function showSection(sectionId) {
        uploadSection.classList.add('d-none');
        dashboardSection.classList.add('d-none');
        booksListSection.classList.add('d-none');
        
        document.querySelectorAll('.navbar-nav .nav-link').forEach(link => link.classList.remove('active'));

        if (sectionId === 'upload') {
            uploadSection.classList.remove('d-none');
            navUploadLink.classList.add('active');
        } else if (sectionId === 'dashboard') {
            dashboardSection.classList.remove('d-none');
        } else if (sectionId === 'books') {
            booksListSection.classList.remove('d-none');
            navBooksLink.classList.add('active');
            loadBooksList();
        }
    }

    navUploadLink.addEventListener('click', (e) => {
        e.preventDefault();
        showSection('upload');
    });

    navBooksLink.addEventListener('click', (e) => {
        e.preventDefault();
        showSection('books');
    });

    btnBackToUpload.addEventListener('click', () => {
        resetUploadUI();
        showSection('upload');
    });

    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length) handleFiles(this.files);
    });

    function handleFiles(files) {
        const file = files[0];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError("Format neacceptat. Te rugăm să încarci doar fișiere în format PDF.");
            return;
        }

        
        
        const filenameBase = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
        const parts = filenameBase.split('-');
        
        let guessedTitle = filenameBase.trim();
        let guessedAuthorNume = "Autor";
        let guessedAuthorPrenume = "";
        
        if (parts.length >= 2) {
            const authorRaw = parts[0].trim();
            guessedTitle = parts[1].trim();
            
            const authorParts = authorRaw.split(' ');
            if (authorParts.length >= 2) {
                guessedAuthorPrenume = authorParts[0];
                guessedAuthorNume = authorParts.slice(1).join(' ');
            } else {
                guessedAuthorNume = authorRaw;
            }
        }

        
        document.getElementById('meta-title').value = guessedTitle;
        document.getElementById('meta-year').value = "2024";
        document.getElementById('meta-author-nume').value = guessedAuthorNume;
        document.getElementById('meta-author-prenume').value = guessedAuthorPrenume;
        document.getElementById('meta-author-birth').value = "";
        document.getElementById('meta-author-death').value = "";

        
        pendingFile = file;
        
        const modalEl = document.getElementById('metadataModal');
        pendingModalInstance = new bootstrap.Modal(modalEl);
        pendingModalInstance.show();
    }

    
    function uploadPDF(file, metadata) {
        dropZone.classList.add('d-none');
        statusContainer.classList.remove('d-none');
        
        statusSpinner.classList.remove('d-none');
        successIcon.classList.add('d-none');
        errorIcon.classList.add('d-none');
        viewResultsBtn.classList.add('d-none');
        resetBtn.classList.add('d-none');
        
        statusTitle.textContent = "Se încarcă...";
        statusMessage.textContent = `Se încarcă fișierul "${file.name}" pe server...`;
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        progressText.textContent = 'Pregătire încărcare...';

        const formData = new FormData();
        formData.append('file', file);
        if (metadata) {
            formData.append('titlu', metadata.titlu);
            formData.append('an_aparitie', metadata.an_aparitie);
            formData.append('autor_nume', metadata.autor_nume);
            formData.append('autor_prenume', metadata.autor_prenume);
            if (metadata.autor_data_nasterii) {
                formData.append('autor_data_nasterii', metadata.autor_data_nasterii);
            }
            if (metadata.autor_data_deces) {
                formData.append('autor_data_deces', metadata.autor_data_deces);
            }
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/upload/`);

        
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = `${percent}%`;
                progressPercentage.textContent = `${percent}%`;
                progressText.textContent = `Se încarcă fișierul pe server: ${percent}%`;
                if (percent === 100) {
                    statusTitle.textContent = "Se inițializează parsarea...";
                    progressText.textContent = "Inițializare OCR...";
                }
            }
        };

        xhr.onload = function() {
            if (xhr.status === 201) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    currentBookId = data.id_carte;
                    
                    
                    localStorage.setItem('currentBookId', data.id_carte);
                    localStorage.setItem('currentBookName', file.name);

                    
                    progressBar.style.width = '0%';
                    progressPercentage.textContent = '0%';
                    progressText.textContent = 'Inițializare pagini...';
                    startPollingStatus(data.id_carte, file.name);
                } catch (e) {
                    showError("Eroare la citirea răspunsului de pe server.");
                }
            } else {
                let errorMsg = 'Eroare la încărcare.';
                try {
                    const data = JSON.parse(xhr.responseText);
                    errorMsg = data.error || errorMsg;
                } catch(e) {}
                showError(errorMsg);
            }
        };

        xhr.onerror = function() {
            showError('Eroare de rețea la încărcarea fișierului.');
        };

        xhr.send(formData);
    }

    function startPollingStatus(bookId, filename) {
        statusSpinner.classList.remove('d-none');
        statusTitle.textContent = "Se parsează cartea...";
        statusMessage.innerHTML = `Documentul <strong>${filename}</strong> a fost încărcat.<br>Procesarea OCR a paginilor rulează în fundal.`;

        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(() => {
            fetch(`${API_BASE_URL}/status/${bookId}/`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'error') {
                    clearInterval(pollInterval);
                    localStorage.removeItem('currentBookId');
                    localStorage.removeItem('currentBookName');
                    showError(data.message || "Eroare la procesare document.");
                } else {
                    const done = data.done || 0;
                    const total = data.total || 1;
                    const percent = Math.min(100, Math.round((done / total) * 100));
                    
                    progressBar.style.width = `${percent}%`;
                    progressPercentage.textContent = `${percent}%`;
                    progressText.textContent = `Pagini procesate: ${done} / ${total}`;
                    
                    if (data.status === 'done_ocr' || data.status === 'done') {
                        clearInterval(pollInterval);
                        localStorage.removeItem('currentBookId');
                        localStorage.removeItem('currentBookName');
                        showSuccess(filename, data.status);
                    } else if (data.status === 'processing') {
                        statusMessage.innerHTML = `Se extrage textul prin OCR din <strong>${filename}</strong>...<br>Progres: pagina ${done} din ${total} în curs de finalizare.`;
                    }
                }
            })
            .catch(err => {
                console.error("Eroare la verificarea stării:", err);
            });
        }, 3000);
    }

    function showSuccess(filename, status) {
        statusSpinner.classList.add('d-none');
        successIcon.classList.remove('d-none');
        viewResultsBtn.classList.remove('d-none');
        resetBtn.classList.remove('d-none');
        
        progressBar.style.width = `100%`;
        progressPercentage.textContent = `100%`;

        if (status === 'done_ocr') {
            statusTitle.textContent = "OCR Finalizat!";
            statusMessage.innerHTML = `Cartea <strong>${filename}</strong> a fost citită prin OCR.<br>Apasă pe butonul de mai jos pentru a accesa panoul de analiză AI.`;
        } else {
            statusTitle.textContent = "Analiză Completă!";
            statusMessage.innerHTML = `Cartea <strong>${filename}</strong> a fost complet analizată (OCR + AI).<br>Relațiile și dialogurile au fost detectate și salvate în baza de date.`;
        }
    }

    function showError(message) {
        if (pollInterval) clearInterval(pollInterval);
        statusSpinner.classList.add('d-none');
        errorIcon.classList.remove('d-none');
        resetBtn.classList.remove('d-none');
        
        statusTitle.textContent = "Eroare";
        statusMessage.textContent = message;
    }

    function resetUploadUI() {
        if (pollInterval) clearInterval(pollInterval);
        if (aiPollInterval) clearInterval(aiPollInterval);
        fileInput.value = '';
        statusContainer.classList.add('d-none');
        dropZone.classList.remove('d-none');
    }

    resetBtn.addEventListener('click', resetUploadUI);

    
    document.getElementById('btn-submit-metadata').addEventListener('click', () => {
        const titleVal = document.getElementById('meta-title').value.trim();
        const yearVal = document.getElementById('meta-year').value.trim();
        const authorNumeVal = document.getElementById('meta-author-nume').value.trim();
        const authorPrenumeVal = document.getElementById('meta-author-prenume').value.trim();
        const authorBirthVal = document.getElementById('meta-author-birth').value;
        const authorDeathVal = document.getElementById('meta-author-death').value;
        
        if (!titleVal || !authorNumeVal || !yearVal) {
            alert("Te rugăm să completezi câmpurile obligatorii: Titlu, An Apariție și Nume Autor.");
            return;
        }

        const metadata = {
            titlu: titleVal,
            an_aparitie: yearVal,
            autor_nume: authorNumeVal,
            autor_prenume: authorPrenumeVal,
            autor_data_nasterii: authorBirthVal,
            autor_data_deces: authorDeathVal
        };

        if (pendingModalInstance) {
            pendingModalInstance.hide();
        }

        if (pendingFile) {
            uploadPDF(pendingFile, metadata);
        }
    });

    viewResultsBtn.addEventListener('click', () => {
        if (currentBookId) {
            loadDashboard(currentBookId);
        }
    });

    
    function loadDashboard(bookId) {
        currentBookId = bookId;
        showSection('dashboard');
        
        
        clearFilterInputs();

        
        document.getElementById('qa-question-input').value = '';
        document.getElementById('qa-response-container').classList.add('d-none');
        document.getElementById('qa-loading').classList.add('d-none');
        document.getElementById('qa-answer').textContent = '';
        
        
        if (aiPollInterval) clearInterval(aiPollInterval);

        const loadingDiv = document.getElementById('network-loading');
        loadingDiv.classList.remove('d-none');

        
        fetch(`${API_BASE_URL}/status/${bookId}/`)
        .then(res => res.json())
        .then(statusData => {
            const badge = document.getElementById('active-book-status-badge');
            const progressCont = document.getElementById('ai-progress-container');

            if (statusData.status === 'processing_ai') {
                badge.className = 'badge bg-warning text-dark mb-2';
                badge.textContent = 'Analiză AI în curs...';
                const isSummary = statusData.s_status === 'processing';
                setAnalysisButtonsState(true, isSummary ? 'summary' : 'relations');
                progressCont.classList.remove('d-none');
                startPollingAiProgress(bookId);
            } else if (statusData.status === 'done') {
                badge.className = 'badge bg-success mb-2';
                badge.textContent = 'Analiză AI Finalizată';
                setAnalysisButtonsState(false);
                progressCont.classList.add('d-none');
            } else {
                badge.className = 'badge bg-secondary mb-2';
                badge.textContent = 'OCR Finalizat';
                setAnalysisButtonsState(false);
                progressCont.classList.add('d-none');
            }
        })
        .catch(err => console.error("Eroare la preluarea stării cărții:", err));

        fetch(`${API_BASE_URL}/books/${bookId}/graph/`)
        .then(res => res.json())
        .then(data => {
            loadingDiv.classList.add('d-none');
            
            
            document.getElementById('active-book-title').textContent = data.carte.titlu;
            document.getElementById('active-book-meta').textContent = `Autor: ${data.carte.autor} | An apariție: ${data.carte.an_aparitie} | Pagini: ${data.carte.nr_pagini}`;
            
            
            const btnDownload = document.getElementById('btn-download-summary');
            if (data.has_summary) {
                btnDownload.classList.remove('d-none');
            } else {
                btnDownload.classList.add('d-none');
            }
            
            
            allPersonaje = data.personaje || [];
            allRelatii = data.relatii || [];

            
            renderFilteredTables();
            
            
            drawGraph(data.personaje, data.relatii);
        })
        .catch(err => {
            loadingDiv.classList.add('d-none');
            console.error("Eroare la încărcarea grafului:", err);
            alert("Eroare la încărcarea datelor cărții.");
        });
    }

    function setAnalysisButtonsState(disabled, statusMsg = null) {
        const btnRel = document.getElementById('btn-start-relations-analysis');
        const btnSum = document.getElementById('btn-start-summary-analysis');
        const btnClear = document.getElementById('btn-clear-book-analysis');
        
        if (btnRel) {
            btnRel.disabled = disabled;
            if (disabled && statusMsg === 'relations') {
                btnRel.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Rulare Relații...';
            } else {
                btnRel.innerHTML = '<i class="fa-solid fa-people-arrows-left-right me-1"></i> Analizează Relații';
            }
        }
        if (btnSum) {
            btnSum.disabled = disabled;
            if (disabled && statusMsg === 'summary') {
                btnSum.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Rulare Rezumat...';
            } else {
                btnSum.innerHTML = '<i class="fa-solid fa-file-invoice me-1"></i> Generează Rezumat';
            }
        }
        if (btnClear) {
            btnClear.disabled = disabled;
        }
    }

    function startPollingAiProgress(bookId) {
        if (aiPollInterval) clearInterval(aiPollInterval);

        const badge = document.getElementById('active-book-status-badge');
        const progressCont = document.getElementById('ai-progress-container');
        const progressBarAi = document.getElementById('ai-progress-bar');
        const progressTextAi = document.getElementById('ai-progress-text');
        const progressPercAi = document.getElementById('ai-progress-percentage');

        aiPollInterval = setInterval(() => {
            fetch(`${API_BASE_URL}/status/${bookId}/`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'error') {
                    clearInterval(aiPollInterval);
                    alert("A apărut o eroare la analiza AI: " + data.message);
                    
                    badge.className = 'badge bg-danger mb-2';
                    badge.textContent = 'Eroare AI';
                    setAnalysisButtonsState(false);
                    progressCont.classList.add('d-none');
                } else if (data.status === 'done') {
                    clearInterval(aiPollInterval);
                    
                    badge.className = 'badge bg-success mb-2';
                    badge.textContent = 'Analiză AI Finalizată';
                    setAnalysisButtonsState(false);
                    progressCont.classList.add('d-none');

                    
                    loadDashboard(bookId);
                } else if (data.status === 'processing_ai') {
                    const done = data.done || 0;
                    const total = data.total || 1;
                    const percent = Math.min(100, Math.round((done / total) * 100));

                    progressBarAi.style.width = `${percent}%`;
                    progressPercAi.textContent = `${percent}%`;
                    progressTextAi.textContent = data.message || `Analizăm prin AI...`;
                    
                    badge.className = 'badge bg-warning text-dark mb-2';
                    badge.textContent = `Analiză AI în curs... (${percent}%)`;
                    
                    const isSummary = data.s_status === 'processing';
                    setAnalysisButtonsState(true, isSummary ? 'summary' : 'relations');
                    progressCont.classList.remove('d-none');
                }
            })
            .catch(err => {
                console.error("Eroare la polling AI:", err);
            });
        }, 3000);
    }

    function renderFilteredTables() {
        const charNameFilter = document.getElementById('filter-char-name').value.toLowerCase().trim();
        const charGenFilter = document.getElementById('filter-char-gen').value;
        const charRolFilter = document.getElementById('filter-char-rol').value;

        const relNameFilter = document.getElementById('filter-rel-name').value.toLowerCase().trim();
        const relMinFilter = parseInt(document.getElementById('filter-rel-min').value) || 1;

        
        const filteredPersonaje = allPersonaje.filter(p => {
            const matchesName = p.nume.toLowerCase().includes(charNameFilter);
            const matchesGen = !charGenFilter || p.gen === charGenFilter;
            const matchesRol = !charRolFilter || p.tip_personaj === charRolFilter;
            return matchesName && matchesGen && matchesRol;
        });

        
        const filteredRelatii = allRelatii.filter(r => {
            const matchesName = !relNameFilter || 
                r.personaj_1_nume.toLowerCase().includes(relNameFilter) || 
                r.personaj_2_nume.toLowerCase().includes(relNameFilter);
            const matchesMin = r.numar_dialoguri >= relMinFilter;
            return matchesName && matchesMin;
        });

        
        populateTables(filteredPersonaje, filteredRelatii);
    }

    function clearFilterInputs() {
        document.getElementById('filter-char-name').value = '';
        document.getElementById('filter-char-gen').value = '';
        document.getElementById('filter-char-rol').value = '';
        document.getElementById('filter-rel-name').value = '';
        document.getElementById('filter-rel-min').value = '1';
    }

    
    const btnStartRelations = document.getElementById('btn-start-relations-analysis');
    const btnStartSummary = document.getElementById('btn-start-summary-analysis');
    const btnClearAnalysis = document.getElementById('btn-clear-book-analysis');

    function triggerAiAnalysis(runRelations, runSummary) {
        if (!currentBookId) return;

        setAnalysisButtonsState(true, runSummary ? 'summary' : 'relations');
        
        
        document.getElementById('btn-download-summary').classList.add('d-none');

        fetch(`${API_BASE_URL}/books/${currentBookId}/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                run_relations: runRelations,
                run_summary: runSummary
            })
        })
        .then(res => {
            if (res.ok) {
                const badge = document.getElementById('active-book-status-badge');
                badge.className = 'badge bg-warning text-dark mb-2';
                badge.textContent = 'Analiză AI în curs...';

                const progressCont = document.getElementById('ai-progress-container');
                progressCont.classList.remove('d-none');
                
                const progressBarAi = document.getElementById('ai-progress-bar');
                const progressTextAi = document.getElementById('ai-progress-text');
                const progressPercAi = document.getElementById('ai-progress-percentage');
                progressBarAi.style.width = '0%';
                progressPercAi.textContent = '0%';
                progressTextAi.textContent = 'Inițializare analiză AI...';

                startPollingAiProgress(currentBookId);
            } else {
                alert("Eroare la pornirea analizei AI.");
                setAnalysisButtonsState(false);
            }
        })
        .catch(err => {
            console.error("Eroare la pornirea analizei AI:", err);
            alert("Eroare de rețea la pornirea analizei AI.");
            setAnalysisButtonsState(false);
        });
    }

    if (btnStartRelations) {
        btnStartRelations.addEventListener('click', () => {
            triggerAiAnalysis(true, false);
        });
    }

    if (btnStartSummary) {
        btnStartSummary.addEventListener('click', () => {
            triggerAiAnalysis(false, true);
        });
    }

    if (btnClearAnalysis) {
        btnClearAnalysis.addEventListener('click', () => {
            if (!currentBookId) return;
            if (confirm("Ești sigur că vrei să ștergi TOATE datele de analiză (personaje, relații și rezumatul Word) pentru această carte? Această acțiune este ireversibilă.")) {
                setAnalysisButtonsState(true);
                fetch(`${API_BASE_URL}/books/${currentBookId}/clear-analysis/`, {
                    method: 'POST'
                })
                .then(res => {
                    setAnalysisButtonsState(false);
                    if (res.ok) {
                        alert("Datele de analiză au fost șterse cu succes.");
                        loadDashboard(currentBookId);
                    } else {
                        alert("Eroare la ștergerea datelor de analiză.");
                    }
                })
                .catch(err => {
                    console.error("Eroare la ștergerea analizei:", err);
                    setAnalysisButtonsState(false);
                });
            }
        });
    }

    
    document.getElementById('filter-char-name').addEventListener('input', renderFilteredTables);
    document.getElementById('filter-char-gen').addEventListener('change', renderFilteredTables);
    document.getElementById('filter-char-rol').addEventListener('change', renderFilteredTables);
    document.getElementById('filter-rel-name').addEventListener('input', renderFilteredTables);
    document.getElementById('filter-rel-min').addEventListener('input', renderFilteredTables);

    
    document.getElementById('btn-download-summary').addEventListener('click', () => {
        if (!currentBookId) return;
        window.location.href = `${API_BASE_URL}/books/${currentBookId}/download-summary/`;
    });

    
    const btnSubmitQa = document.getElementById('btn-submit-qa');
    const inputQa = document.getElementById('qa-question-input');
    const containerResponseQa = document.getElementById('qa-response-container');
    const loadingQa = document.getElementById('qa-loading');
    const answerQa = document.getElementById('qa-answer');

    function sendQaRequest() {
        if (!currentBookId) return;
        const questionText = inputQa.value.trim();
        if (!questionText) return;

        
        containerResponseQa.classList.remove('d-none');
        loadingQa.classList.remove('d-none');
        answerQa.textContent = '';
        btnSubmitQa.disabled = true;

        fetch(`${API_BASE_URL}/books/${currentBookId}/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: questionText })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => { throw err; });
            }
            return res.json();
        })
        .then(data => {
            loadingQa.classList.add('d-none');
            answerQa.textContent = data.answer;
            btnSubmitQa.disabled = false;
            inputQa.value = ''; 
        })
        .catch(err => {
            console.error("Eroare la asistentul QA:", err);
            loadingQa.classList.add('d-none');
            answerQa.textContent = `Eroare: ${err.error || 'A apărut o problemă la comunicarea cu asistentul AI.'}`;
            btnSubmitQa.disabled = false;
        });
    }

    btnSubmitQa.addEventListener('click', sendQaRequest);
    inputQa.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendQaRequest();
        }
    });

    function populateTables(personaje, relatii) {
        
        const charTbody = document.getElementById('characters-tbody');
        charTbody.innerHTML = '';
        
        if (personaje.length === 0) {
            charTbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary py-3">Nu au fost detectate personaje.</td></tr>';
        } else {
            personaje.forEach(p => {
                const tr = document.createElement('tr');
                let badgeClass = 'bg-secondary';
                if (p.tip_personaj === 'Principal') badgeClass = 'bg-primary';
                else if (p.tip_personaj === 'Secundar') badgeClass = 'bg-info';
                
                tr.innerHTML = `
                    <td class="fw-medium">${p.nume}</td>
                    <td><span class="badge bg-dark border border-secondary border-opacity-50 text-secondary">${p.gen}</span></td>
                    <td><span class="badge ${badgeClass}">${p.tip_personaj}</span></td>
                `;
                charTbody.appendChild(tr);
            });
        }

        
        const relTbody = document.getElementById('relations-tbody');
        relTbody.innerHTML = '';
        
        if (relatii.length === 0) {
            relTbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary py-3">Nu s-au detectat interacțiuni directe.</td></tr>';
        } else {
            
            const sortedRelatii = [...relatii].sort((a, b) => b.numar_dialoguri - a.numar_dialoguri);
            
            sortedRelatii.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${r.personaj_1_nume}</td>
                    <td>${r.personaj_2_nume}</td>
                    <td class="text-center"><span class="badge bg-accent px-2.5 py-1.5 fs-7">${r.numar_dialoguri}</span></td>
                `;
                relTbody.appendChild(tr);
            });
        }
    }

    function drawGraph(personaje, relatii) {
        const container = document.getElementById('network-container');
        
        
        const nodesArray = personaje.map(p => {
            
            let color = '#6b7280'; 
            let size = 15;
            
            if (p.tip_personaj === 'Principal') {
                color = '#6366f1'; 
                size = 30;
            } else if (p.tip_personaj === 'Secundar') {
                color = '#a855f7'; 
                size = 22;
            } else if (p.tip_personaj === 'Episodic') {
                color = '#3b82f6'; 
                size = 16;
            }

            return {
                id: p.id_personaj,
                label: p.nume,
                shape: 'dot',
                size: size,
                color: {
                    background: color,
                    border: '#ffffff',
                    highlight: {
                        background: '#f43f5e', 
                        border: '#ffffff'
                    }
                },
                font: {
                    color: '#f3f4f6',
                    face: 'Inter',
                    size: p.tip_personaj === 'Principal' ? 14 : 12,
                    bold: p.tip_personaj === 'Principal'
                }
            };
        });

        
        const edgesArray = relatii.map(r => {
            
            const width = Math.min(10, 1 + Math.log2(r.numar_dialoguri + 1));
            
            return {
                from: r.id_personaj1,
                to: r.id_personaj2,
                width: width,
                color: {
                    color: 'rgba(99, 102, 241, 0.4)',
                    highlight: 'rgba(244, 63, 94, 0.8)'
                },
                label: String(r.numar_dialoguri),
                font: {
                    color: '#9ca3af',
                    size: 10,
                    face: 'Inter',
                    background: '#0b0f19'
                }
            };
        });

        const data = {
            nodes: new vis.DataSet(nodesArray),
            edges: new vis.DataSet(edgesArray)
        };

        const options = {
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -3000,
                    centralGravity: 0.3,
                    springLength: 120,
                    springConstant: 0.04,
                    damping: 0.09
                },
                stabilization: {
                    iterations: 100,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: false
            }
        };

        network = new vis.Network(container, data, options);
    }

    btnFitGraph.addEventListener('click', () => {
        if (network) network.fit({ animation: true });
    });

    btnRefreshGraph.addEventListener('click', () => {
        if (currentBookId) {
            loadDashboard(currentBookId);
        }
    });

    
    function loadBooksList() {
        const grid = document.getElementById('books-grid');
        grid.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>';

        fetch(`${API_BASE_URL}/books/`)
        .then(res => res.json())
        .then(books => {
            grid.innerHTML = '';
            if (books.length === 0) {
                grid.innerHTML = '<div class="col-12 text-center text-secondary py-5">Nicio carte analizată momentan. Încarcă o carte din meniu!</div>';
                return;
            }
            
            books.forEach(b => {
                const col = document.createElement('div');
                col.className = 'col-md-6 col-lg-4';
                col.innerHTML = `
                    <div class="glass-card book-card p-4 h-100 d-flex flex-column justify-content-between">
                        <div>
                            <div class="d-flex justify-content-between mb-2">
                                <span class="badge bg-secondary">${b.an_aparitie}</span>
                                <span class="badge bg-dark border border-secondary border-opacity-50 text-secondary">${b.nr_pagini} pagini</span>
                            </div>
                            <h4 class="font-outfit fw-bold text-gradient mb-1">${b.titlu}</h4>
                            <p class="text-secondary mb-3">Autor: ${b.autor_nume} ${b.autor_prenume || ''}</p>
                        </div>
                        <div class="d-flex gap-2 mt-3">
                            <button class="btn btn-sm btn-accent flex-grow-1 btn-load-book" data-id="${b.id_carte}">
                                <i class="fa-solid fa-eye me-1"></i> Vezi Analiza
                            </button>
                            <button class="btn btn-sm btn-outline-warning btn-edit-book" data-id="${b.id_carte}" title="Editează metadate">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger btn-delete-book" data-id="${b.id_carte}" title="Șterge cartea">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </div>
                `;
                grid.appendChild(col);
            });

            
            grid.querySelectorAll('.btn-load-book').forEach(btn => {
                btn.addEventListener('click', function() {
                    const bookId = this.getAttribute('data-id');
                    loadDashboard(bookId);
                });
            });

            
            grid.querySelectorAll('.btn-edit-book').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const bookId = this.getAttribute('data-id');
                    openEditMetadataModal(bookId);
                });
            });

            
            grid.querySelectorAll('.btn-delete-book').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const bookId = this.getAttribute('data-id');
                    if (confirm("Ești sigur că vrei să ștergi această carte din sistem?")) {
                        fetch(`${API_BASE_URL}/books/${bookId}/delete/`, {
                            method: 'DELETE'
                        })
                        .then(res => {
                            if (res.ok) {
                                loadBooksList();
                            } else {
                                alert("Eroare la ștergerea cărții.");
                            }
                        })
                        .catch(err => console.error(err));
                    }
                });
            });
        })
        .catch(err => {
            console.error("Eroare la încărcarea listei de cărți:", err);
            grid.innerHTML = '<div class="col-12 text-center text-danger py-5">Eroare la încărcarea listei de cărți de pe server.</div>';
        });
    }

    
    if (btnClearAllBooks) {
        btnClearAllBooks.addEventListener('click', () => {
            if (confirm("Ești sigur că vrei să ștergi TOATE cărțile și toate analizele stocate în baza de date? Această acțiune este ireversibilă.")) {
                fetch(`${API_BASE_URL}/books/clear-all/`, {
                    method: 'POST'
                })
                .then(res => {
                    if (res.ok) {
                        loadBooksList();
                    } else {
                        alert("Eroare la curățarea datelor.");
                    }
                })
                .catch(err => console.error(err));
            }
        });
    }

    
    const btnEditActiveBook = document.getElementById('btn-edit-active-book-metadata');
    if (btnEditActiveBook) {
        btnEditActiveBook.addEventListener('click', () => {
            if (currentBookId) {
                openEditMetadataModal(currentBookId);
            }
        });
    }

    let editModalInstance = null;

    function openEditMetadataModal(bookId) {
        
        fetch(`${API_BASE_URL}/books/${bookId}/metadata/`)
        .then(res => {
            if (!res.ok) throw new Error("Eroare la preluarea datelor cărții.");
            return res.json();
        })
        .then(data => {
            document.getElementById('edit-meta-book-id').value = data.id_carte;
            document.getElementById('edit-meta-title').value = data.titlu;
            document.getElementById('edit-meta-year').value = data.an_aparitie;
            document.getElementById('edit-meta-author-prenume').value = data.autor_prenume || '';
            document.getElementById('edit-meta-author-nume').value = data.autor_nume;
            document.getElementById('edit-meta-author-birth').value = data.autor_data_nasterii ? data.autor_data_nasterii.substring(0, 10) : '';
            document.getElementById('edit-meta-author-death').value = data.autor_data_deces ? data.autor_data_deces.substring(0, 10) : '';

            const modalEl = document.getElementById('editMetadataModal');
            editModalInstance = new bootstrap.Modal(modalEl);
            editModalInstance.show();
        })
        .catch(err => {
            console.error(err);
            alert("Nu s-au putut prelua metadatele cărții.");
        });
    }

    
    const btnSubmitEditMetadata = document.getElementById('btn-submit-edit-metadata');
    if (btnSubmitEditMetadata) {
        btnSubmitEditMetadata.addEventListener('click', () => {
            const form = document.getElementById('edit-metadata-form');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const bookId = document.getElementById('edit-meta-book-id').value;
            const updatedData = {
                titlu: document.getElementById('edit-meta-title').value,
                an_aparitie: document.getElementById('edit-meta-year').value,
                autor_prenume: document.getElementById('edit-meta-author-prenume').value,
                autor_nume: document.getElementById('edit-meta-author-nume').value,
                autor_data_nasterii: document.getElementById('edit-meta-author-birth').value,
                autor_data_deces: document.getElementById('edit-meta-author-death').value
            };

            btnSubmitEditMetadata.disabled = true;
            btnSubmitEditMetadata.textContent = "Se salvează...";

            fetch(`${API_BASE_URL}/books/${bookId}/metadata/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedData)
            })
            .then(res => res.json())
            .then(data => {
                btnSubmitEditMetadata.disabled = false;
                btnSubmitEditMetadata.textContent = "Salvează Modificările";
                
                if (data.error) {
                    alert("Eroare: " + data.error);
                } else {
                    if (editModalInstance) {
                        editModalInstance.hide();
                    }
                    alert("Metadatele au fost salvate cu succes!");
                    
                    
                    if (currentBookId && currentBookId.toString() === bookId.toString()) {
                        loadDashboard(bookId);
                    } else {
                        
                        loadBooksList();
                    }
                }
            })
            .catch(err => {
                console.error(err);
                btnSubmitEditMetadata.disabled = false;
                btnSubmitEditMetadata.textContent = "Salvează Modificările";
                alert("Eroare de rețea la salvarea metadatelor.");
            });
        });
    }

    
    const savedBookId = localStorage.getItem('currentBookId');
    const savedBookName = localStorage.getItem('currentBookName');
    
    if (savedBookId && savedBookName) {
        
        fetch(`${API_BASE_URL}/status/${savedBookId}/`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'processing') {
                currentBookId = parseInt(savedBookId);
                
                dropZone.classList.add('d-none');
                statusContainer.classList.remove('d-none');
                startPollingStatus(currentBookId, savedBookName);
            } else {
                localStorage.removeItem('currentBookId');
                localStorage.removeItem('currentBookName');
                showSection('upload');
            }
        })
        .catch(err => {
            localStorage.removeItem('currentBookId');
            localStorage.removeItem('currentBookName');
            showSection('upload');
        });
    } else {
        showSection('upload');
    }
});
