const form = document.getElementById("question-form");
const input = document.getElementById("question");
const askButton = document.getElementById("ask-button");
const reasoningSelect = document.getElementById("retrievalReasoningEffort");
const outputModeSelect = document.getElementById("knowledgeRetrievalOutputMode");
const themeToggle = document.getElementById("theme-toggle");
const conversation = document.getElementById("conversation");
const emptyState = document.getElementById("empty-state");
const modal = document.getElementById("citation-modal");
const modalClose = document.getElementById("close-modal");
const modalBody = document.getElementById("citation-body");

const kbConfigElement = document.getElementById("kb-config");
let kbConfig = {};
try {
    kbConfig = JSON.parse(kbConfigElement?.textContent || "{}");
} catch (error) {
    console.error("Unable to parse KB configuration", error);
}

const state = {
    interactions: [],
    config: kbConfig,
};

const THEME_STORAGE_KEY = "kbThemePreference";

let markdownConfigured = false;
const configureMarkdown = () => {
    if (typeof window === "undefined" || typeof window.marked === "undefined" || markdownConfigured) {
        return;
    }

    window.marked.setOptions({
        gfm: true,
        breaks: false,
        mangle: false,
        headerIds: false,
        pedantic: false,
    });
    markdownConfigured = true;
};

const escapeHtml = (unsafe = "") =>
    unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

const renderMarkdown = (text) => {
    if (!text) {
        return "";
    }

    if (typeof window !== "undefined" && window.marked && window.DOMPurify) {
        configureMarkdown();
        
        // Normalize text: ensure proper paragraph breaks
        // Convert sentences that end with period + space + capital letter to have double newlines
        let processedText = text
            // First, normalize existing line breaks
            .replace(/\r\n/g, "\n")
            // Convert ". [Capital]" patterns to paragraph breaks if they don't already have them
            .replace(/\.\s+(?=[A-Z])/g, ".\n\n")
            // Clean up excessive newlines (more than 2 consecutive)
            .replace(/\n{3,}/g, "\n\n")
            // Ensure citation markers like [ref_id:X] stay on same line
            .replace(/\n+(\[ref_[^\]]+\])/g, " $1");
        
        const rawHtml = window.marked.parse(processedText);
        return window.DOMPurify.sanitize(rawHtml);
    }

    return escapeHtml(text).replace(/\n/g, "<br />");
};

const formatSeconds = (value) => `${value.toFixed(3)}s`;

const REASONING_LABELS = {
    minimal: "Minimal — skips planning",
    low: "Low — lightweight planning",
    medium: "Medium — thorough planning",
};

const OUTPUT_MODE_LABELS = {
    extractiveData: "Extractive data (verbatim)",
    answerSynthesis: "Answer synthesis (LLM-written)",
};

const formatOverrideValue = (value, labels) => {
    if (!value) {
        return "Knowledge base default";
    }
    return labels[value] || value;
};

const toggleLoading = (isLoading) => {
    askButton.disabled = isLoading;
    if (isLoading) {
        askButton.dataset.originalText = askButton.textContent;
        askButton.textContent = "Thinking";
    } else if (askButton.dataset.originalText) {
        askButton.textContent = askButton.dataset.originalText;
    }
};

const applyTheme = (theme) => {
    const normalized = theme === "light" ? "light" : "dark";
    document.body.dataset.theme = normalized;
    if (themeToggle) {
        const nextLabel = normalized === "light" ? "Switch to dark mode" : "Switch to light mode";
        themeToggle.textContent = nextLabel;
        themeToggle.setAttribute("aria-pressed", normalized === "light" ? "true" : "false");
        themeToggle.setAttribute("aria-label", `${nextLabel} (current theme ${normalized})`);
    }
};

const initializeTheme = () => {
    let storedTheme = null;
    if (typeof window !== "undefined") {
        storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    }

    const prefersLight =
        typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;

    applyTheme(storedTheme || (prefersLight ? "light" : "dark"));
};

const renderConversation = () => {
    conversation.innerHTML = "";

    if (!state.interactions.length) {
        emptyState.style.display = "block";
        conversation.appendChild(emptyState);
        return;
    }

    emptyState.style.display = "none";
    state.interactions.forEach((interaction) => {
        const card = document.createElement("article");
        card.className = "message-card";

        const header = document.createElement("div");
        header.innerHTML = `<h3>Question</h3><p>${interaction.question}</p>`;

        const answerBlock = document.createElement("div");
        const renderedAnswers = interaction.answers
            .map((text) => `<div>${renderMarkdown(text)}</div>`)
            .join('<hr class="answer-divider" />');
        answerBlock.innerHTML = `<h3>Answer</h3><div class="answer-body">${renderedAnswers}</div>`;

        const citationHeading = document.createElement("h3");
        citationHeading.textContent = "Citations";
        card.appendChild(citationHeading);

        if (interaction.citations.length) {
            const citations = document.createElement("div");
            citations.className = "citation-list";
            interaction.citations.forEach((citation) => {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.className = "citation-chip";
                chip.textContent = `ref:${citation.id}`;
                chip.addEventListener("click", () => openCitation(citation));
                citations.appendChild(chip);
            });
            card.appendChild(citations);
        } else {
            const citationNote = document.createElement("p");
            citationNote.className = "citation-note";
            citationNote.textContent = "No citations were returned for this answer.";
            card.appendChild(citationNote);
        }

        const metrics = document.createElement("div");
        metrics.className = "metrics-grid";
        [
            { label: "Total", value: interaction.timing.total },
            { label: "Request Prep", value: interaction.timing.requestPreparation },
            { label: "KB Retrieval", value: interaction.timing.kbRetrieval },
            { label: "Response Processing", value: interaction.timing.responseProcessing },
        ].forEach((metric) => {
            const metricCard = document.createElement("div");
            metricCard.className = "metric-card";
            metricCard.innerHTML = `<span class="label">${metric.label}</span><span class="value">${formatSeconds(
                metric.value || 0
            )}</span>`;
            metrics.appendChild(metricCard);
        });

        card.appendChild(header);
        card.appendChild(answerBlock);
        card.appendChild(metrics);

        const overrides = interaction.metadata?.requestOverrides || {};
        const settings = document.createElement("div");
        settings.className = "request-settings";
        settings.innerHTML = `
            <span class="label">Request overrides</span>
            <div class="settings-grid">
                <div>
                    <span class="setting-name">Reasoning</span>
                    <span class="setting-value">${formatOverrideValue(
                        overrides.retrievalReasoningEffort,
                        REASONING_LABELS
                    )}</span>
                </div>
                <div>
                    <span class="setting-name">Output mode</span>
                    <span class="setting-value">${formatOverrideValue(
                        overrides.knowledgeRetrievalOutputMode,
                        OUTPUT_MODE_LABELS
                    )}</span>
                </div>
            </div>
        `;
        card.appendChild(settings);
        conversation.appendChild(card);
    });
};

initializeTheme();

themeToggle?.addEventListener("click", () => {
    const nextTheme = document.body.dataset.theme === "light" ? "dark" : "light";
    applyTheme(nextTheme);
    if (typeof window !== "undefined") {
        window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    }
});

const openCitation = (citation) => {
    const citationTextHtml = citation.citationText 
        ? `<div class="citation-content">
             <h4>Content</h4>
             <pre>${escapeHtml(citation.citationText)}</pre>
           </div>` 
        : "";
    
    const noteHtml = citation.note 
        ? `<div class="citation-note-section">
             <h4>Note</h4>
             <p>${escapeHtml(citation.note)}</p>
           </div>` 
        : "";
    
    const documentHtml = citation.document 
        ? `<p><strong>Document:</strong> ${escapeHtml(citation.document)}</p>` 
        : "";
    
    const relevanceHtml = citation.relevanceScore 
        ? `<p><strong>Relevance Score:</strong> ${citation.relevanceScore.toFixed(3)}</p>` 
        : "";

    modalBody.innerHTML = `
        <h3 id="citation-title">Reference ${citation.id}</h3>
        <p><strong>Source Type:</strong> ${escapeHtml(citation.type || "unknown")}</p>
        ${citation.title ? `<p><strong>Title:</strong> ${escapeHtml(citation.title)}</p>` : ""}
        ${documentHtml}
        ${citation.url ? `<p><a href="${escapeHtml(citation.url)}" target="_blank" rel="noreferrer noopener">Open Source ↗</a></p>` : ""}
        ${relevanceHtml}
        ${citationTextHtml}
        ${noteHtml}
    `;
    modal.setAttribute("aria-hidden", "false");
};

const closeCitation = () => {
    modal.setAttribute("aria-hidden", "true");
    modalBody.innerHTML = "";
};

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        closeCitation();
    }
});
modalClose.addEventListener("click", closeCitation);

const showError = (message) => {
    const card = document.createElement("article");
    card.className = "message-card";
    card.innerHTML = `<h3>Error</h3><p>${message}</p>`;
    conversation.prepend(card);
};

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) {
        return;
    }

    toggleLoading(true);
    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question,
                ...(reasoningSelect?.value ? { retrievalReasoningEffort: reasoningSelect.value } : {}),
                ...(outputModeSelect?.value ? { knowledgeRetrievalOutputMode: outputModeSelect.value } : {}),
            }),
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody.detail || "Unable to process your question.");
        }

        const payload = await response.json();
        state.interactions.unshift(payload);
        renderConversation();
        form.reset();
        input.focus();
    } catch (error) {
        showError(error.message);
    } finally {
        toggleLoading(false);
    }
});

renderConversation();
