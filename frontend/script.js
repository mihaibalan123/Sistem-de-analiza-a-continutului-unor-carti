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

    });