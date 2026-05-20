

document.addEventListener("DOMContentLoaded", () => {

    const API_BASE = "http://localhost:8000";

    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");
    const sectionTitle = document.getElementById("current-section-title");
    const sectionDesc = document.getElementById("current-section-desc");


    const reconcileForm = document.getElementById("reconcile-form");
    const reconResults = document.getElementById("reconcile-results");
    const reconLoading = document.getElementById("reconcile-loading");
    const reconError = document.getElementById("reconcile-error");
    const reconErrorMessage = document.getElementById("reconcile-error-message");
    const reconCardsContainer = document.getElementById("reconciliation-cards");
    const aiSummaryText = document.getElementById("ai-summary-text");
    const complianceAlertBox = document.getElementById("compliance-alert-box");
    const complianceAlertIcon = document.getElementById("compliance-alert-icon");
    const complianceAlertText = document.getElementById("compliance-alert-text");


    const declarationForm = document.getElementById("declaration-form");
    const submissionSuccess = document.getElementById("submission-success");
    const submissionError = document.getElementById("submission-error");
    const submissionErrorMsg = document.getElementById("submission-error-msg");
    const resetDeclarationBtn = document.getElementById("reset-declaration-btn");
    const receiptId = document.getElementById("receipt-id");
    const receiptTimestamp = document.getElementById("receipt-timestamp");
    const receiptProducer = document.getElementById("receipt-producer");
    const receiptMonth = document.getElementById("receipt-month");


    const chatForm = document.getElementById("chat-form");
    const chatInputField = document.getElementById("chat-input-field");
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const chatTypingIndicator = document.getElementById("chat-typing-indicator");


    navItems.forEach(item => {
        item.addEventListener("click", () => {

            navItems.forEach(n => n.classList.remove("active"));

            item.classList.add("active");


            sections.forEach(s => s.classList.remove("active"));

            const targetId = item.getAttribute("data-target");
            document.getElementById(targetId).classList.add("active");


            updateTopBar(targetId);
        });
    });

    function updateTopBar(sectionId) {
        if (sectionId === "dashboard-section") {
            sectionTitle.textContent = "EPR Compliance Dashboard";
            sectionDesc.textContent = "Reconcile plastic declarations with ERP procurement data.";
        } else if (sectionId === "declare-section") {
            sectionTitle.textContent = "Submit Declaration";
            sectionDesc.textContent = "Deterministic input verification for monthly plastic weights.";
        } else if (sectionId === "assistant-section") {
            sectionTitle.textContent = "EPR Compliance AI Assistant";
            sectionDesc.textContent = "Conversational chat grounded in central compliance circulars.";
        }
    }


    let activeTypewriterTimeout = null;
    function typeWriter(element, text, speed = 15) {

        if (activeTypewriterTimeout) {
            clearTimeout(activeTypewriterTimeout);
        }

        element.textContent = "";
        let i = 0;

        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                activeTypewriterTimeout = setTimeout(type, speed);
            }
        }
        type();
    }


    reconcileForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const producerId = document.getElementById("recon-producer-id").value.trim();
        const month = document.getElementById("recon-month").value.trim();


        reconResults.classList.add("hidden");
        reconError.classList.add("hidden");
        reconLoading.classList.remove("hidden");

        try {
            const response = await fetch(`${API_BASE}/summary/${producerId}/${month}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to fetch reconciliation summary.");
            }

            const data = await response.json();


            renderReconciliationResults(data);


            reconLoading.classList.add("hidden");
            reconResults.classList.remove("hidden");

        } catch (error) {
            console.error("Reconciliation error:", error);
            reconErrorMessage.textContent = error.message;
            reconLoading.classList.add("hidden");
            reconError.classList.remove("hidden");
        }
    });

    function renderReconciliationResults(data) {
        const reconciliation = data.reconciliation;
        const summary = data.summary;


        reconCardsContainer.innerHTML = "";

        let hasFlaggedCategory = false;

        reconciliation.forEach(item => {
            const card = document.createElement("div");
            card.className = "category-recon-item";


            const statusClass = item.flagged ? "flagged" : "compliant";
            const statusText = item.flagged ? "Flagged Discrepancy" : "Compliant";
            const percentageColor = item.flagged ? "red" : "green";
            const icon = item.flagged ? "⚠️" : "✓";

            if (item.flagged) {
                hasFlaggedCategory = true;
            }

            card.innerHTML = `
                <div class="category-meta">
                    <h4>${item.category.replace("_", " ")}</h4>
                    <span>Tolerance threshold: 5%</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Declared</span>
                    <span class="metric-value">${item.declared_kg.toLocaleString()} kg</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Procured (ERP)</span>
                    <span class="metric-value">${item.procured_kg.toLocaleString()} kg</span>
                </div>
                <div class="discrepancy-status">
                    <span class="status-badge ${statusClass}">${icon} ${statusText}</span>
                    <span class="percentage-label ${percentageColor}">Diff: ${item.difference_percent}%</span>
                </div>
            `;
            reconCardsContainer.appendChild(card);
        });


        typeWriter(aiSummaryText, summary, 12);


        if (hasFlaggedCategory) {
            complianceAlertBox.className = "action-alert flagged";
            complianceAlertIcon.textContent = "⚠️";
            complianceAlertText.textContent = "Compliance Alert: One or more categories exceed the 5% mismatch limit. Corrective audit required.";
        } else {
            complianceAlertBox.className = "action-alert compliant";
            complianceAlertIcon.textContent = "✓";
            complianceAlertText.textContent = "Compliance Confirmed: All category declarations match procurement records within the 5% margin.";
        }
    }


    declarationForm.addEventListener("submit", async (e) => {
        e.preventDefault();


        const producerId = document.getElementById("decl-producer-id").value.trim();
        const month = document.getElementById("decl-month").value.trim();
        const rigid = parseFloat(document.getElementById("decl-rigid").value);
        const flexible = parseFloat(document.getElementById("decl-flexible").value);
        const multilayer = parseFloat(document.getElementById("decl-multilayer").value);


        submissionError.classList.add("hidden");


        const payload = {
            producer_id: producerId,
            month: month,
            declared_quantities_kg: {
                rigid_plastic: rigid,
                flexible_plastic: flexible,
                multilayer_plastic: multilayer
            }
        };

        try {
            const response = await fetch(`${API_BASE}/submit`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {

                let errorMsg = "Declaration input validation rejected.";
                if (data.detail && Array.isArray(data.detail)) {
                    errorMsg = data.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(", ");
                } else if (data.detail) {
                    errorMsg = data.detail;
                }
                throw new Error(errorMsg);
            }


            receiptId.textContent = data.record_id;

            receiptTimestamp.textContent = new Date(data.created_at).toLocaleString();
            receiptProducer.textContent = data.producer_id;
            receiptMonth.textContent = data.month;


            declarationForm.classList.add("hidden");
            submissionSuccess.classList.remove("hidden");

        } catch (error) {
            console.error("Submission error:", error);
            submissionErrorMsg.textContent = error.message;
            submissionError.classList.remove("hidden");
        }
    });


    resetDeclarationBtn.addEventListener("click", () => {
        declarationForm.reset();
        submissionSuccess.classList.add("hidden");
        declarationForm.classList.remove("hidden");
    });


    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = chatInputField.value.trim();
        if (!question) return;


        chatInputField.value = "";


        appendMessage("user", question);


        chatTypingIndicator.classList.remove("hidden");
        scrollToBottom();

        try {
            const response = await fetch(`${API_BASE}/ask`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) {
                throw new Error("Compliance assistant failed to respond.");
            }

            const data = await response.json();


            appendMessage("assistant", data.answer, data.sources);

        } catch (error) {
            console.error("Chat error:", error);
            appendMessage("assistant", `Error: ${error.message}. Please check if the backend service is running.`);
        } finally {

            chatTypingIndicator.classList.add("hidden");
            scrollToBottom();
        }
    });

    function appendMessage(sender, text, sources = []) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;

        const avatarIcon = sender === "assistant" ? "🤖" : "👤";
        let citationsHTML = "";


        if (sender === "assistant" && sources && sources.length > 0) {
            const uniqueSources = Array.from(new Set(sources.map(s => `${s.source} (Page ${s.page})`)));
            const tagsHTML = uniqueSources.map(s => `<span class="citation-tag">${s}</span>`).join("");

            citationsHTML = `
                <div class="citations-box">
                    <span class="citation-header" onclick="this.nextElementSibling.classList.toggle('hidden')">Sources cited</span>
                    <div class="citations-list">${tagsHTML}</div>
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarIcon}</div>
            <div class="message-bubble glass">
                <p>${text}</p>
                ${citationsHTML}
            </div>
        `;

        chatMessagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }
});
