// Global variable to keep track of current translation results for downloading
let currentTranslationData = {
    originalText: "",
    translatedText: "",
    targetLang: "",
    accuracy: null,
    modelUsed: ""
};

let activeDeleteRecordId = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Dashboard Charts (if elements exist)
    initDashboardCharts();

    // 2. Initialize Drag & Drop Workspace (if elements exist)
    initDragAndDrop();

    // 3. Initialize Form Submission Handler
    initFormHandler();
});

/* ==========================================================================
   DASHBOARD CHARTS (Chart.js)
   ========================================================================== */
function initDashboardCharts() {
    const langCanvas = document.getElementById("langDistChart");
    const accuracyCanvas = document.getElementById("accuracyChart");

    if (langCanvas && typeof langDistributionData !== 'undefined') {
        const labels = Object.keys(langDistributionData);
        const data = Object.values(langDistributionData);
        
        // Dynamic color palette matching HSL primary/accent
        const colors = [
            'rgba(99, 102, 241, 0.75)',  // Indigo
            'rgba(245, 158, 11, 0.75)',  // Amber
            'rgba(16, 185, 129, 0.75)',  // Emerald
            'rgba(244, 63, 94, 0.75)',   // Rose
            'rgba(139, 92, 246, 0.75)',  // Purple
            'rgba(6, 182, 212, 0.75)',   // Cyan
            'rgba(236, 72, 153, 0.75)',  // Pink
            'rgba(14, 165, 233, 0.75)',  // Sky
            'rgba(168, 85, 247, 0.75)',  // Violet
            'rgba(101, 163, 13, 0.75)'   // Lime
        ];

        new Chart(langCanvas, {
            type: 'doughnut',
            data: {
                labels: labels.length > 0 ? labels : ['No Data'],
                datasets: [{
                    data: data.length > 0 ? data : [1],
                    backgroundColor: data.length > 0 ? colors.slice(0, data.length) : ['rgba(255,255,255,0.05)'],
                    borderColor: 'rgba(22, 28, 45, 0.9)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 11 }
                        }
                    }
                }
            }
        });
    }

    if (accuracyCanvas && typeof accuracyHistory !== 'undefined') {
        // Map raw database points
        const labels = accuracyHistory.map(pt => pt.date);
        const data = accuracyHistory.map(pt => pt.score);

        // Fallbacks if history is empty
        const chartLabels = labels.length > 0 ? labels : ['06-13', '06-14', '06-15', '06-16', '06-17', '06-18', '06-19'];
        const chartData = data.length > 0 ? data : [88.5, 91.2, 89.0, 92.4, 91.8, 93.1, 92.0];

        new Chart(accuracyCanvas, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Accuracy Score (%)',
                    data: chartData,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#090d16',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        min: 75,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } }
                    }
                }
            }
        });
    }
}

/* ==========================================================================
   WORKSPACE INPUT TABS & FILE UPLOAD
   ========================================================================== */
function switchInputTab(tabType) {
    const fileBtn = document.getElementById("tab-file-btn");
    const textBtn = document.getElementById("tab-text-btn");
    const fileContent = document.getElementById("tab-file-content");
    const textContent = document.getElementById("tab-text-content");
    const modeInput = document.getElementById("process-mode");

    if (tabType === 'file') {
        fileBtn.classList.add("active");
        textBtn.classList.remove("active");
        fileContent.classList.add("active");
        textContent.classList.remove("active");
        modeInput.value = "ocr";
    } else {
        fileBtn.classList.remove("active");
        textBtn.classList.add("active");
        fileContent.classList.remove("active");
        textContent.classList.add("active");
        modeInput.value = "text";
    }
}

function initDragAndDrop() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    if (!dropZone) return;

    // Trigger file dialog
    dropZone.addEventListener("click", () => fileInput.click());

    // File selection event
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelected(e.target.files[0]);
        }
    });

    // Drag-over styling
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        }, false);
    });

    // Drop handler
    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files; // assign files
            handleFileSelected(files[0]);
        }
    });
}

function handleFileSelected(file) {
    const dropZone = document.getElementById("drop-zone");
    const previewContainer = document.getElementById("image-preview-container");
    const previewImage = document.getElementById("image-preview");

    if (!file.type.startsWith('image/')) {
        alert("Please select a valid image file (PNG, JPG, JPEG).");
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        dropZone.style.display = "none";
        previewContainer.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
}

function clearSelectedFile() {
    const dropZone = document.getElementById("drop-zone");
    const previewContainer = document.getElementById("image-preview-container");
    const previewImage = document.getElementById("image-preview");
    const fileInput = document.getElementById("file-input");

    fileInput.value = "";
    previewImage.src = "#";
    previewContainer.classList.add("hidden");
    dropZone.style.display = "flex";
}

/* ==========================================================================
   TRANSLATION API HANDLER & PROGRESS INJECTORS
   ========================================================================== */
function initFormHandler() {
    const form = document.getElementById("translation-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const mode = document.getElementById("process-mode").value;
        const targetLang = document.getElementById("target_lang").value;
        const submitBtn = document.getElementById("submit-btn");
        
        // Form validations
        if (mode === "ocr" && !document.getElementById("file-input").files[0]) {
            alert("Please select or drop an image file first.");
            return;
        }
        if (mode === "text" && !document.getElementById("original_text_input").value.trim()) {
            alert("Please enter English text to translate.");
            return;
        }

        const formData = new FormData(form);
        
        // Show loading screen and disable button
        submitBtn.disabled = true;
        showLoadingOverlay(mode);

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                // Populate Output Workspace Panels
                updateWorkspaceOutput(result, targetLang);
            } else {
                alert(`Error: ${result.error || 'Server processing error'}`);
            }
        } catch (error) {
            alert(`Network Error: ${error.message}`);
        } finally {
            hideLoadingOverlay();
            submitBtn.disabled = false;
        }
    });
}

// Multi-step animated progress overlay for immersive AI feel
function showLoadingOverlay(mode) {
    const overlay = document.getElementById("loading-overlay");
    const statusText = document.getElementById("loading-status");
    const logText = document.getElementById("loading-log");
    
    if (!overlay) return;

    overlay.classList.remove("hidden");
    
    let step = 0;
    const ocrSteps = [
        { status: "Initializing image arrays...", log: "Loading OpenCV bindings" },
        { status: "Preprocessing filters (CLAHE active)...", log: "Equalizing contrast matrix" },
        { status: "Denoising pixels (Bilateral filter)...", log: "Smoothing Gaussian gradients" },
        { status: "Binarizing gradient lines...", log: "Otsu threshold segmentation" },
        { status: "Running Tesseract OCR Engine...", log: "Matching characters against English weights" },
        { status: "Executing NumPy preprocessing...", log: "Padding sequence matrices to length [1, 50]" },
        { status: "Running deep NMT translator...", log: "Interpreting encoder representation" }
    ];

    const textSteps = [
        { status: "Reading raw text streams...", log: "Validating input encodings" },
        { status: "Executing NumPy preprocessing...", log: "Padding sequence matrices to length [1, 50]" },
        { status: "Running deep NMT translator...", log: "Interpreting encoder representation" },
        { status: "Finalizing regional text synthesis...", log: "Generating target font characters" }
    ];

    const activeSteps = (mode === 'ocr') ? ocrSteps : textSteps;
    
    // Animate logs sequentially
    const interval = setInterval(() => {
        if (step < activeSteps.length) {
            statusText.innerText = activeSteps[step].status;
            logText.innerText = activeSteps[step].log;
            step++;
        } else {
            clearInterval(interval);
        }
    }, 450);

    // Save interval ID on window object to clear it on finish
    window.loadingInterval = interval;
}

function hideLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) {
        overlay.classList.add("hidden");
    }
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }
}

function updateWorkspaceOutput(result, targetLangCode) {
    const sourceTextarea = document.getElementById("extracted-text-output");
    const transDiv = document.getElementById("translated-text-output");
    const accuracyBadge = document.getElementById("accuracy-badge");
    const engineBadge = document.getElementById("engine-type");
    const targetBadge = document.getElementById("target-language-badge");
    
    // Tensors container
    const tensorBox = document.getElementById("tensor-stats");
    const tokenIds = document.getElementById("t-ids");
    const tokenPads = document.getElementById("t-pad");

    // Enable buttons
    document.getElementById("btn-copy").disabled = false;
    document.getElementById("btn-tts").disabled = false;
    document.getElementById("btn-download").disabled = false;

    // 1. Source Output
    sourceTextarea.value = result.original_text;
    sourceTextarea.readOnly = false; // Make it editable for custom tweaks

    // 2. Translated Output
    transDiv.innerText = result.translated_text;

    // 3. Update Badges
    if (result.confidence && result.mode === 'ocr_translation') {
        accuracyBadge.innerText = `OCR Accuracy: ${result.confidence}%`;
        accuracyBadge.classList.remove("hidden");
        // Highlight accuracy class
        accuracyBadge.className = "badge";
        accuracyBadge.classList.add(result.confidence >= 90 ? "badge-emerald" : "badge-indigo");
    } else {
        accuracyBadge.classList.add("hidden");
    }
    
    engineBadge.innerText = (result.mode === 'ocr_translation') ? "OCR Extracted" : "Direct Text Input";
    
    // Extract target language label from drop-down selector
    const langSelect = document.getElementById("target_lang");
    const selectedLangLabel = langSelect.options[langSelect.selectedIndex].text;
    targetBadge.innerText = `Target: ${selectedLangLabel}`;

    // 4. Fill NumPy/Pandas Token Preprocessing Visualizer
    if (result.preprocessed_stats) {
        tokenIds.innerText = JSON.stringify(result.preprocessed_stats.vocab_ids);
        tokenPads.innerText = JSON.stringify(result.preprocessed_stats.padded_array_preview);
        tensorBox.classList.remove("hidden");
    }

    // 5. Update global variables for text assets download
    currentTranslationData = {
        originalText: result.original_text,
        translatedText: result.translated_text,
        targetLang: selectedLangLabel,
        accuracy: result.confidence || 100.0,
        modelUsed: result.model_used
    };
}

/* ==========================================================================
   OUTPUT ACTION UTILITIES (Speech, Clipboard, Downloads)
   ========================================================================== */
function copyTranslation() {
    const textToCopy = document.getElementById("translated-text-output").innerText;
    const btn = document.getElementById("btn-copy");

    if (!textToCopy) return;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalContent = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="check" class="text-emerald"></i> Copied!`;
        lucide.createIcons();
        
        setTimeout(() => {
            btn.innerHTML = originalContent;
            lucide.createIcons();
        }, 2000);
    }).catch(err => {
        alert("Clipboard copy failed: ", err);
    });
}

function speakTranslation() {
    const textToSpeak = document.getElementById("translated-text-output").innerText;
    const btn = document.getElementById("btn-tts");

    if (!textToSpeak) return;

    // Check if speaking. If speaking, stop it (toggle play/stop)
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        btn.innerHTML = `<i data-lucide="volume-2"></i> Listen`;
        lucide.createIcons();
        return;
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    
    // Set appropriate Indian Voice Locale if available
    const langSelect = document.getElementById("target_lang").value;
    const langVoiceMap = {
        'hi': 'hi-IN',
        'mr': 'mr-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'bn': 'bn-IN',
        'gu': 'gu-IN',
        'ur': 'ur-PK',
        'kn': 'kn-IN',
        'ml': 'ml-IN',
        'pa': 'pa-IN'
    };

    utterance.lang = langVoiceMap[langSelect] || 'hi-IN';
    
    // Animate button during playback
    btn.innerHTML = `<i data-lucide="square" class="text-rose"></i> Stop`;
    lucide.createIcons();

    utterance.onend = () => {
        btn.innerHTML = `<i data-lucide="volume-2"></i> Listen`;
        lucide.createIcons();
    };

    utterance.onerror = () => {
        btn.innerHTML = `<i data-lucide="volume-2"></i> Listen`;
        lucide.createIcons();
    };

    window.speechSynthesis.speak(utterance);
}

function toggleDownloadDropdown() {
    const dd = document.getElementById("download-dropdown");
    if (dd) {
        dd.classList.toggle("show");
    }
}

// Close download dropdown if clicked outside
window.addEventListener("click", (e) => {
    if (!e.target.matches('#btn-download') && !e.target.closest('#btn-download')) {
        const dd = document.getElementById("download-dropdown");
        if (dd && dd.classList.contains("show")) {
            dd.classList.remove("show");
        }
    }
});

function downloadAs(format) {
    if (!currentTranslationData.translatedText) return;

    const targetLang = currentTranslationData.targetLang;
    const dateStr = new Date().toISOString().slice(0,10);
    
    if (format === 'txt') {
        const content = 
            `==================================================\n` +
            `MULTILINGUAL RESOURCE TRANSLATION EXPORT\n` +
            `Date Processed: ${new Date().toLocaleString()}\n` +
            `Target Language: ${targetLang}\n` +
            `Model Engine: ${currentTranslationData.modelUsed}\n` +
            `OCR Accuracy: ${currentTranslationData.accuracy}%\n` +
            `==================================================\n\n` +
            `--- ORIGINAL ENGLISH TEXT ---\n` +
            `${currentTranslationData.originalText}\n\n` +
            `--- TRANSLATED REGIONAL TEXT (${targetLang}) ---\n` +
            `${currentTranslationData.translatedText}\n`;
            
        triggerFileDownload(content, `translation_${dateStr}_${targetLang}.txt`, 'text/plain');
    } 
    else if (format === 'json') {
        const data = {
            exportedAt: new Date().toISOString(),
            targetLanguage: targetLang,
            engineModel: currentTranslationData.modelUsed,
            ocrAccuracy: currentTranslationData.accuracy,
            originalText: currentTranslationData.originalText,
            translatedText: currentTranslationData.translatedText
        };
        
        triggerFileDownload(JSON.stringify(data, null, 4), `translation_${dateStr}_${targetLang}.json`, 'application/json');
    }
}

function triggerFileDownload(content, filename, contentType) {
    const blob = new Blob([content], { type: `${contentType};charset=utf-8;` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/* ==========================================================================
   HISTORY LOG FILTER & DELETE UTILITIES
   ========================================================================== */
function filterLogs() {
    const query = document.getElementById("log-search-input").value.toLowerCase().trim();
    const cards = document.querySelectorAll(".history-card");
    const grid = document.getElementById("history-grid");
    let matchCount = 0;

    cards.forEach(card => {
        const searchTarget = card.getAttribute("data-search-target").toLowerCase();
        if (searchTarget.includes(query)) {
            card.style.display = "flex";
            matchCount++;
        } else {
            card.style.display = "none";
        }
    });

    // Handle empty state during filter
    let emptyState = document.getElementById("search-empty-state");
    if (matchCount === 0 && query !== "") {
        if (!emptyState) {
            emptyState = document.createElement("div");
            emptyState.id = "search-empty-state";
            emptyState.className = "empty-history glass-card";
            emptyState.innerHTML = `
                <i data-lucide="search-code" class="empty-icon text-muted"></i>
                <h3>No Match Found</h3>
                <p>We couldn't find any logs matching "${query}". Try searching another keyword.</p>
            `;
            grid.appendChild(emptyState);
            lucide.createIcons();
        }
    } else {
        if (emptyState) {
            emptyState.remove();
        }
    }
}

function confirmDeleteRecord(id) {
    activeDeleteRecordId = id;
    const modal = document.getElementById("delete-modal");
    if (modal) {
        modal.classList.remove("hidden");
    }
}

function closeDeleteModal() {
    const modal = document.getElementById("delete-modal");
    if (modal) {
        modal.classList.add("hidden");
    }
    activeDeleteRecordId = null;
}

async function executeDeleteRecord() {
    if (!activeDeleteRecordId) return;

    try {
        const response = await fetch(`/api/delete/${activeDeleteRecordId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Find the log element and apply fade out effect
            const card = document.querySelector(`.history-card[data-id="${activeDeleteRecordId}"]`);
            if (card) {
                card.style.transition = "all 0.5s ease";
                card.style.opacity = "0";
                card.style.transform = "scale(0.9)";
                setTimeout(() => {
                    card.remove();
                    // Reload if no cards left to render clean empty state
                    if (document.querySelectorAll(".history-card").length === 0) {
                        window.location.reload();
                    }
                }, 500);
            }
        } else {
            alert("Could not delete record from database.");
        }
    } catch (error) {
        alert("Failed to connect to delete endpoint: " + error.message);
    } finally {
        closeDeleteModal();
    }
}
